# Scheduler completion rows (IMP-046 / Hybrid Step 4)

Hive is a clock. `lab` CLI is the executed path. Every Hive-driven `lab brief` / `lab deliver` / `lab schedule heartbeat` writes one JSON file here so the miss detector can observe a **fire**.

Miss sweep (`lab schedule miss-check`) is still the control: **closed window + no file (and no `schedule_heartbeat` row) → miss**. A failed CLI run (`exit_status != 0`) is a fire, not a miss. Heartbeat-on-fire remains a log.

## Location

Canonical: `ops/reports/scheduler/completions/{routine_id}__{YYYYMMDDTHHMMSSZ}.json`

Override: `--completions-dir` or `MM_SCHEDULE_COMPLETIONS_DIR`.

**Policy (B1 Stage 1 / Principal 2026-09-22):** Actions-produced stamps **ARE committed** under this directory so the box can `git pull` and `lab schedule miss-check --no-db` can read them. Artifact upload alone is not durable. Prefer the Actions commit path (auditable message with routine id, run_id, scheduled_for, actual, delta_seconds, status). Do not commit secrets — only `*.json` completion rows. Postgres table `schedule_heartbeat` remains the optional DB copy (skipped with `--no-db`).

**SCHED-001 CLOSED** citing run_id `actions-b1-35727756341` (observable row: `grok.sydney_morning__20260921T203000Z.json`; stamp commit `857f55c` on `main`). Principal 2026-09-22: Actions is execution (this directory is the durable commit). Grok Bot app routines are a pure clock plus agent wake (local stamp only; run_id `box-us-pre-20260922T133710Z`, `grok.us_pre_market__20260922T130000Z.json`; degrade-to-dry is permanent). Panel SCHEDULE cron and panel WEBHOOK are dead. The box is not a production host. Close pack: [../../incident-closures/20260922-sched-001-actions-invoker-close.md](../../incident-closures/20260922-sched-001-actions-invoker-close.md).

## Row fields

| Field | Meaning |
|---|---|
| `run_id` | This fire |
| `routine_id` | Configured trigger (`grok.sydney_morning`, `grok.us_pre_market`, `grok.weekly_investment_review`, or lab pulse/delivery id) |
| `fired_at_ts` | Actual fire time (UTC) |
| `scheduled_anchor_ts` | Catalog anchor |
| `delta_seconds` | Offset vs anchor (negative = early) |
| `status` | Timing class: `ok` / `late` (a fire). Not process exit. Unscheduled weekday writes **no row** (stamp refused), never `late`. |
| `exit_status` | CLI process exit (0 or nonzero). Failed is still a fire. |
| `payload_path` | briefs/ payload if any |
| `cli` | Invoked command |

## How miss-sweep reads it

1. CI / fixture clock: `--fixture tests/fixtures/scheduler/ci_clock.yaml` does **not** load this directory (isolated). Pass `--completions-dir` to merge disk rows into a fixture catalog (tests).
2. Operator / Hive box: `lab schedule miss-check --no-db` loads this directory (and DB unless `--no-db`).
3. Same `(routine_id, scheduled_anchor_ts)` key as the table. Higher-rank timing status wins (`ok` > `late` > `skipped` > `missed`). A refused wrong-anchor stamp is not a row.
4. `lab schedule miss-check --baseline-before today` writes `ops/reports/scheduler/known-missed-baseline.yaml` (pre-today Australia/Sydney windows labeled, not deleted).

Hive clocks (catalog in `config/schedules/routines.yaml`):

```bash
uv run lab brief preopen --no-db --no-send --routine-id grok.us_pre_market
uv run lab deliver pack --no-send --no-db --routine-id grok.weekly_investment_review --from-markdown PATH --as-of ...
uv run lab schedule heartbeat --routine-id grok.sydney_morning --exit-status 0 --no-db
```

Hive group / desk pack `--send` stays SEND_FROZEN. DM-only: `lab deliver test --to-principal-dm --i-mean-it`.
