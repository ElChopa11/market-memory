# ADR 0018 — Scheduler miss detector

- **Status:** Accepted
- **Phase:** IMP-042. No live trading. No signing. No Redis. SCHED-001 **CLOSED** 2026-09-22 (run_id `actions-b1-35727756341`). Principal 2026-09-22: Grok is a pure clock (`box-us-pre-20260922T133710Z`); Actions is execution (#90).

## Context

Sydney 08:00 digest never fired while NY sibling briefs completed (SCHED-001). A completion log written only when a job fires cannot detect a job that never runs.

## Decision

The scheduler **control** is a miss sweep: for each configured routine, if the window is closed and no completion row exists, escalate (non-zero `lab schedule miss-check`, OPEN ops artifact). Heartbeat-on-fire is a secondary log (`schedule_heartbeat`). CI uses a fixture clock so the check is non-flaky. Canaries are not in the catalog.

Hive `created_at` / `updated_at` / `ROUTINE_CHANGE` are not in this repo; they are not invented to suppress a closed window.

## Consequences

- SCHED-001 **CLOSED** citing run_id `actions-b1-35727756341` (hybrid-sydney-morning #1; stamp `857f55c` on `main`). Panel SCHEDULE cron is dead (7 routines, 0 fires). Panel WEBHOOK is dead (C1 silent). Principal 2026-09-22: Grok routines are a pure clock plus agent wake (stamp only; no live fetch; no delivery; degrade-to-dry is permanent; run_id `box-us-pre-20260922T133710Z`). Actions is execution (fetch, brief, deliver; the runner runs the CLI and commits output). The box is interactive desk work, not a production host. “No window yet” was never a close. See [ops/reports/incident-closures/20260922-sched-001-actions-invoker-close.md](../ops/reports/incident-closures/20260922-sched-001-actions-invoker-close.md).
- 06:30 / Fri 17:00 calendar hypotheses for *other* routines stay unverified until Don pastes Hive timestamps; they are not SCHED-001.
- Operators run `lab schedule miss-check`. `heartbeat-check` is an alias of that control, not a dump of heartbeat rows.
- Hybrid Step 4: Hive → lab CLI writes the completion JSON the miss sweep loads (`ops/reports/scheduler/completions/`, plus optional `schedule_heartbeat`). A failed CLI run is a fire (`exit_status != 0`). Silence (no row) is the miss. CI fixture clocks stay isolated unless `--completions-dir` is set.
- IMP-056: `lab migrate` is idempotent for `schedule_heartbeat`. Slot/anchor is catalog `local_time` on the fire's local calendar date; unscheduled weekday writes **no** completion row (stamp refused, not `late`). `lab schedule miss-check --baseline-before today` labels pre-today (Australia/Sydney) misses without deleting history.
- B1 Stage 1 (#90): Actions is the execution path. This stage stamps `grok.sydney_morning` and commits `completions/` only. Stage 2 (Actions delivers a real pack to the Principal DM) is the next build and is not in this ADR’s code. Grok app routines stamp and wake only. Degrade-to-dry is permanent; no standing Auto-review allow. Minutes of Actions cron drift on the 06:30 digest are accepted (±900s). Neon/R2 credentials belong in Actions secrets, not on the box. A separate Telegram bot for Actions stands (two blast radii). None of those follow-ons are implemented here.
