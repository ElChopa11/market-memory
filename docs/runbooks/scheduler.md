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

- Neon/R2 credentials go to Actions secrets, not the box. Prepare-only names, offline `lab migrate --sql`, and the blocked-on-Principal list: [persistence-neon-r2.md](persistence-neon-r2.md). The Sydney morning job is still `--no-db`.
- A separate Telegram bot for Actions stands (two credential stores, two blast radii).
- Stage 2 is the right next build: Actions delivering a real pack to the Principal DM.
- Minutes of Actions cron drift on the 06:30 digest are accepted as drift. They are not a skip.

This section does not change `.github/workflows/hybrid-sydney-morning.yml`. That file stays one AEST cron. Every fire stamps. No ±900s skip. No second cron.

## B1 Stage 1 — GitHub Actions execution path (stamp today)

Actions is the execution path. This workflow is still the Stage 1 stamp for `grok.sydney_morning`, via `.github/workflows/hybrid-sydney-morning.yml`. Fetch, brief, and Principal-DM delivery are Stage 2 (next build; not this file).

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

Manual fire: Actions → **hybrid-sydney-morning** → **Run workflow** → use the **PR branch** while draft. The job stamps; there is no force flag and no ±900s skip.
