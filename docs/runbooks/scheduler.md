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

`--baseline-before today` is the Australia/Sydney calendar date of `--now` (or now). Writes `ops/reports/scheduler/known-missed-baseline.yaml` (gitignored). Subsequent miss-check loads that file. Windows are **labeled**, not deleted. SCHED-001 stays OPEN.

Hive group / desk pack `--send` stays SEND_FROZEN. DM-only live path is `lab deliver test --to-principal-dm --i-mean-it` (does not change miss-check). SCHED-001 stays OPEN. Root cause: [ops/reports/scheduler/2026-09-19-sched-001-root-cause.md](../../ops/reports/scheduler/2026-09-19-sched-001-root-cause.md).

## B1 Stage 1 — GitHub Actions invoker (permanent clock)

Grok Bot panel schedule is dead. The permanent invoker is `.github/workflows/hybrid-sydney-morning.yml`:

- `on.schedule` dual cron for weekday 06:30 Australia/Sydney (AEST `30 20 * * 0-4` UTC; AEDT `30 19 * * 0-4` UTC). Off-season companion is skipped unless within ±900s of the local anchor.
- `on.workflow_dispatch` for Principal canary (default force stamp).
- Job runs `uv run lab schedule heartbeat --routine-id grok.sydney_morning --no-db --source github.actions` (no Telegram; never `--send`).
- **Durable path:** the job commits the completion JSON to the branch the workflow ran on (`github.ref_name`) with an auditable message (`routine_id`, `run_id`, `scheduled_for`, `actual`, `delta_seconds`, `status`), using `permissions: contents: write` and rebase-retry on non-fast-forward. Completions are **not** gitignored.
- **Secondary:** `actions/upload-artifact` (expires; box cannot read).
- After `git pull` on the box, `lab schedule miss-check --no-db` can load the row. **SCHED-001 closes only on an observed fire with a readable completion row** — not artifact-only.

### Push target

| When | Select / runs on | Commit lands on |
|---|---|---|
| Draft PR canary (before merge) | Actions → Run workflow → branch **`cursor/b1-sydney-morning-actions-ae81`** (or current PR head) | That PR branch |
| After merge | `schedule` on default branch | `main` |

Manual fire: Actions → **hybrid-sydney-morning** → **Run workflow** → use the **PR branch** while draft → leave `force` true.

## B1 Stage 2 PREP — Actions Principal DM pack (DRAFT — do not run)

**Do not run until Principal approves** this diff and the Actions secret names below. Do not `workflow_dispatch` with `i_mean_it_stage2=true` until then. Paper only. GROUP SEND_FROZEN stays.

Stage 2 is a **separate job** (`stage2-principal-dm-pack`) on the same workflow file. Stage 1 heartbeat path is unchanged. Stage 2 never runs on `schedule` — only `workflow_dispatch` when input `i_mean_it_stage2` is explicitly `true` (default **false** so accidental Run workflow cannot send).

### Secret names (NAMES ONLY — never invent values)

| Actions secret name | Purpose | Notes |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Actions-only **second** bot token | Separate blast radius from box `/home/box/agent-data/delivery/telegram.env`. Not the Grok Secrets card. |
| `TELEGRAM_CHAT_ID_PRINCIPAL_DM` | Principal private DM chat id | Required for `--to-principal-dm`. |
| `TELEGRAM_CHAT_ID` | **Must remain UNSET** in Actions | Hive group. Never wire this secret into Stage 2. GROUP SEND_FROZEN — never `--send` to group. |

### Operator prerequisites (before any first send)

1. Principal creates / owns a **second** BotFather bot used only by GitHub Actions.
2. Principal opens a DM with that second bot and sends `/start` (required before first send).
3. Principal adds the two secret **names** above under repo Actions secrets (values never in git / PR body).
4. Principal reviews this workflow diff, then (only if approved) may set `i_mean_it_stage2=true` on a manual Run workflow.

### CLI the Stage 2 job would run

```bash
uv run lab deliver pack \
  --from-markdown tests/fixtures/phase5e/desk-pack.md \
  --as-of <UTC-now> \
  --desk ops \
  --to-principal-dm \
  --i-mean-it \
  --ignore-quiet-hours \
  --no-db \
  --repo-root . \
  --out /tmp/stage2-principal-dm-<run_id>
```

`--no-db` until Neon. Fixture markdown is the PREP canary; later may brief then `--from-markdown` a live artifact. Never group `--send`.
