# Scheduler miss sweep (IMP-042)

The clock is true only if a **closed window without a completion row is a miss**. Heartbeat-on-fire is a log. Canaries are out of scope.

```bash
# Control (MERGE-BLOCKING). Fixture clock in CI.
uv run lab schedule miss-check \
  --fixture tests/fixtures/scheduler/ci_clock.yaml \
  --now 2026-09-19T09:49:00Z \
  --no-db

# Same control (alias). Not a heartbeat dump.
uv run lab schedule heartbeat-check --fixture tests/fixtures/scheduler/ci_clock.yaml --now 2026-09-19T09:49:00Z --no-db

# Prove the 08:00 class escalates:
uv run lab schedule miss-check --fixture tests/fixtures/scheduler/miss_clock.yaml --now 2026-09-19T09:49:00Z --no-db --out /tmp/sched-miss

# Label all pre-today (Australia/Sydney) closed windows as known-missed so
# Monday's miss is visible. History is labeled, not deleted.
uv run lab schedule miss-check --baseline-before today --no-db

# Secondary log (does not pass the check by itself). Hive → lab CLI also
# writes ops/reports/scheduler/completions/ so the miss sweep can see a fire.
# After `lab migrate`, heartbeat also persists to schedule_heartbeat (disk
# still writes if the table is missing).
uv run lab migrate
uv run lab schedule heartbeat --routine-id grok.sydney_morning --fired-at 2026-09-17T20:32:00Z --exit-status 0 --no-db
uv run lab schedule record-fire --routine-id lab.pulse.preopen --fired-at 2026-09-18T12:02:00Z --no-db

# Backfill markdown:
uv run lab schedule backfill --fixture tests/fixtures/scheduler/miss_clock.yaml --now 2026-09-19T09:49:00Z --no-db --out /tmp/sched
```

Catalog composition:

- Grok Bot / Hive: `config/schedules/routines.yaml` (no `created_at` in repo)
- Lab Pulse: `config/schedules/market-pulse.yaml`
- Lab Telegram wall-clock: `config/delivery/telegram.yaml` `schedule`

## Completion rows (Hybrid Step 4)

Hive clock → `lab brief` / `lab deliver` / `lab schedule heartbeat` writes a JSON row:

`ops/reports/scheduler/completions/{routine_id}__{anchor}.json`

Fields: `run_id`, `routine_id` (configured trigger), `fired_at_ts` (actual time), `delta_seconds` (offset vs catalog anchor), `status` (timing `ok`/`late`), `exit_status` (CLI process; failed is still a fire), `payload_path` if a briefs/ artifact exists.

Anchor is catalog `local_time` on the fire's **local calendar date** in the routine timezone (Hive clocks: Australia/Sydney). If that weekday is not in the catalog, **write no completion row** (`lab schedule heartbeat` exits 2, `wrote: false`). Do not classify as `late`. Silence (no CLI) and a failed CLI that still stamped a scheduled-day fire stay distinct from a successful fire with a bad stamp.

How miss-sweep reads it:

- Operator: `lab schedule miss-check --no-db` loads that directory (and `schedule_heartbeat` unless `--no-db`).
- CI fixture clock does **not** load the directory unless `--completions-dir` is passed (keeps the clock non-flaky).
- Hive passes `--routine-id grok.sydney_morning` / `grok.us_pre_market` / `grok.weekly_investment_review`.

## known-missed baseline

Sunday dry-run lookback produced ~99 historical misses. Label them once so Monday is visible:

```bash
uv run lab schedule miss-check --baseline-before today --no-db
```

`--baseline-before today` is the Australia/Sydney calendar date of `--now` (or now). Writes `ops/reports/scheduler/known-missed-baseline.yaml` (gitignored). Subsequent miss-check loads that file. Windows are **labeled**, not deleted.

Hive group / desk pack `--send` stays SEND_FROZEN. DM-only live path is `lab deliver test --to-principal-dm --i-mean-it` (does not change miss-check). Root cause (historical): [ops/reports/scheduler/2026-09-19-sched-001-root-cause.md](../../ops/reports/scheduler/2026-09-19-sched-001-root-cause.md). **SCHED-001 CLOSED** citing run_id `actions-b1-35727756341` — [ops/reports/incident-closures/20260922-sched-001-actions-invoker-close.md](../../ops/reports/incident-closures/20260922-sched-001-actions-invoker-close.md).

## Locked architecture (Principal 2026-09-22)

| Path | Role | Evidence |
|---|---|---|
| Panel SCHEDULE cron | Dead | 7 routines, 0 fires |
| Panel WEBHOOK | Dead | C1 silent |
| Grok Bot app routine | Pure clock + agent wake | Stamps a completion and wakes a desk for interactive work. No live fetch. No delivery. Proven 2026-09-22 by run_id `box-us-pre-20260922T133710Z` (`ops/reports/scheduler/completions/grok.us_pre_market__20260922T130000Z.json`). Auto-review blocked `--live`; degrade-to-dry (`--no-db`, DQ unavailable) is permanent correct behaviour. No standing Auto-review allow. |
| GitHub Actions | Execution | Fetch, brief, deliver. The runner is ephemeral: it runs the CLI itself and commits the output. Auditable by construction. Durable path. Stage 1 stamp observed as `actions-b1-35727756341` (commit `857f55c` on `main`, `completions/` only). |
| Bot box | Interactive desk work | Not a production host. |

House lesson: [config/knowledge/house-lessons.md](../../config/knowledge/house-lessons.md) (2026-09-22 Principal decision, run_id `box-us-pre-20260922T133710Z`). ADR: [ADR/0019-grok-clock-actions-execution.md](../../ADR/0019-grok-clock-actions-execution.md).

Why:

1. The Actions runner is destroyed after every job (no persistent state, cookie seeds, screenshots, or autorecovery). Credential exposures this week came from shared-box state.
2. Actions has different egress. That may fix keyless API 429s that backoff only mitigates.
3. Actions is auditable by construction (log, `run_id`, commit, diff).
4. A standing Auto-review allow would permanently widen the path for an occasional need. Principal rejected that trade.

Follow-on decisions (record only; not built here):

- Neon/R2 credentials go to Actions secrets, not the box.
- A separate Telegram bot for Actions stands (two credential stores, two blast radii).
- Stage 2 is the right next build: Actions delivering a real pack to the Principal DM.
- Minutes of Actions cron drift on the 06:30 digest are accepted as drift. They are not a skip.

This section does not change `.github/workflows/hybrid-sydney-morning.yml`. That file stays one AEST cron. Every fire stamps. No ±900s skip. No second cron.

## B1 Stage 1 — GitHub Actions execution path (stamp today)

Actions is the execution path. `stage1-stamp` in `.github/workflows/hybrid-sydney-morning.yml` is the clock proof for `grok.sydney_morning` (fire → stamp → exit). It does not brief and it does not deliver. `brief-and-deliver` runs after that stamp on the same scheduled run. See the next section.

- `on.schedule` one cron while AEST is in force: weekday 06:30 Australia/Sydney is `30 20 * * 0-4` UTC (Sun–Thu 20:30 UTC). No ±900s skip. The AEDT companion cron is not scheduled. Every fire stamps.
- `on.workflow_dispatch` for a Principal canary. Manual dispatch stamps the same way as the cron (no skip).
- Job runs `uv run lab schedule heartbeat --routine-id grok.sydney_morning --no-db --source github.actions` (no Telegram; never `--send`).
- **Durable path:** the job commits the completion JSON to the branch the workflow ran on (`github.ref_name`) with an auditable message (`routine_id`, `run_id`, `scheduled_for`, `actual`, `delta_seconds`, `status`), using `permissions: contents: write` and rebase-retry on non-fast-forward. Completions are **not** gitignored.
- **Secondary:** `actions/upload-artifact` (expires; box cannot read).
- After `git pull` on the box, `lab schedule miss-check --no-db` can load the row.

**SCHED-001 CLOSED** on observed fire with readable completion row: run_id `actions-b1-35727756341` (job hybrid-sydney-morning #1 Success ~21s; stamp commit `857f55c` on `main`, path scoped to `ops/reports/scheduler/completions/` only). Forced-dispatch status `late` (delta 57741s vs yesterday's anchor) is correct; next on-anchor test is 06:30 Australia/Sydney without Principal action.

### Push target

| When | Select / runs on | Commit lands on |
|---|---|---|
| Draft PR canary (before merge) | Actions → Run workflow → branch **`cursor/b1-sydney-morning-actions-ae81`** (or current PR head) | That PR branch |
| After merge | `schedule` on default branch | `main` |

Manual fire: Actions → **hybrid-sydney-morning** → **Run workflow** → select this branch (or `main` after merge). The stamp job runs; there is no force flag and no ±900s skip. Leave `i_mean_it_deliver` false (it defaults to false) and `brief-and-deliver` does not run — that cannot send. Set `i_mean_it_deliver` true to stamp, then brief and deliver to the Principal DM.

## B1 brief-and-deliver (same workflow, after the stamp)

Job `brief-and-deliver` has `needs: stage1-stamp`. It runs when `github.event_name == 'schedule'`, or when `github.event_name == 'workflow_dispatch'` and `i_mean_it_deliver` is true. The input is a boolean and defaults to false. The cron on `stage1-stamp` is unchanged (`30 20 * * 0-4`). No ±900s guard. No second cron. No `i_mean_it_stage2` input. `stage1-stamp` has no `if`, so a manual prove still stamps first.

| Scheduled run | What happens |
|---|---|
| Always | `stage1-stamp` writes and pushes the completion row, with or without Telegram secrets. |
| `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID_PRINCIPAL_DM` absent | `brief-and-deliver` soft-skips (exit 0; later steps skipped). No fetch. No POST. Stamp stands. |
| Both present, and `TELEGRAM_CHAT_ID` unset | `lab brief close --live --no-db`, then `lab deliver pack --from-markdown <brief> --as-of <UTC> --desk ops --to-principal-dm --i-mean-it --ignore-quiet-hours --no-db`. |
| `TELEGRAM_CHAT_ID` set | `brief-and-deliver` exits 1. Group stays SEND_FROZEN. |

`--ignore-quiet-hours` is required on this path because 06:30 Australia/Sydney falls inside `quiet_hours` 22:00–07:00. This job is the morning digest, not an overnight alert.

Stage 1 alone still does not brief or deliver. The schedule path ignores `i_mean_it_deliver` and is the same as the merged brief-and-deliver job: secrets absent → soft skip exit 0; both secrets and `TELEGRAM_CHAT_ID` unset → brief then Principal DM; `TELEGRAM_CHAT_ID` set → exit 1.

| Dispatch | What happens |
|---|---|
| `i_mean_it_deliver` false (default) | `stage1-stamp` runs. `brief-and-deliver` does not run. No send. |
| `i_mean_it_deliver` true | `stage1-stamp` runs first, then the same brief+DM gate as a scheduled fire. |

Principal prove (once): Actions → **hybrid-sydney-morning** → **Run workflow** → branch of this change → set `i_mean_it_deliver` true. Default false cannot send.

**Secret names (Actions; Principal adds values):**

| Name | Role |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Actions-only **second** bot. Not the box `/home/box/agent-data/delivery/telegram.env` token. |
| `TELEGRAM_CHAT_ID_PRINCIPAL_DM` | Principal private DM. |
| `TELEGRAM_CHAT_ID` | **Must stay unset.** The job exits 1 if it is set. Never the Hive group. |

No other secrets on this path (no `FRED_API_KEY`, no `POLYGON_API_KEY`). Those slots stay `unavailable` in the brief. CoinGecko and Hyperliquid `/info` are keyless.

Group preflight treats unset `TELEGRAM_CHAT_ID` as an error for desk publish. DM-only `--to-principal-dm --i-mean-it` proceeds when that is the only preflight error. Any other preflight error strips `--i-mean-it` (no degraded publish).

### P0.4 — Actions egress vs box rate limits

Fetch code classifies HTTP 429 as `error_class=rate_limited` and honours `Retry-After` internally. It does not print rate-limit headers unless `MM_LOG_RATE_LIMIT_HEADERS=1`. The brief step sets that flag. Stderr then prints `rate-limit headers source=<hostname> status=<code> headers=...` for CoinGecko (`api.coingecko.com` via `http_get`) and Hyperliquid (`hyperliquid.info <info type>`). Allowlisted header names only (`Retry-After`, `*ratelimit*`). The request URL is not printed (query keys and bot tokens live in URLs).

This agent did not measure GitHub-hosted runner egress. A run that enters `brief-and-deliver` with both DM secrets prints those lines in the brief step log **before** the DM POST. A clean pass is `status=200` with `headers=(none)` or a remaining quota. A limited pass is `status=429` plus `Retry-After`. Compare that log to box 429s. A Run workflow with `i_mean_it_deliver` left at its default false does not run the brief and cannot send. Set it true to prove the DM; that run also prints the P0.4 lines. The schedule does not read the input.
