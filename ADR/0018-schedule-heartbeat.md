# ADR 0018 — Scheduler miss detector

- **Status:** Accepted
- **Phase:** IMP-042. No live trading. No signing. No Redis. SCHED-001 stays OPEN.

## Context

Sydney 08:00 digest never fired while NY sibling briefs completed (SCHED-001). A completion log written only when a job fires cannot detect a job that never runs.

## Decision

The scheduler **control** is a miss sweep: for each configured routine, if the window is closed and no completion row exists, escalate (non-zero `lab schedule miss-check`, OPEN ops artifact). Heartbeat-on-fire is a secondary log (`schedule_heartbeat`). CI uses a fixture clock so the check is non-flaky. Canaries are not in the catalog.

Hive `created_at` / `updated_at` / `ROUTINE_CHANGE` are not in this repo; they are not invented to suppress a closed window.

## Consequences

- SCHED-001 remains OPEN until a verified on-anchor fire. “No window yet” is not a close.
- 06:30 / Fri 17:00 calendar hypotheses stay unverified until Don pastes Hive timestamps.
- Operators run `lab schedule miss-check`. `heartbeat-check` is an alias of that control, not a dump of heartbeat rows.
- Hybrid Step 4: Hive → lab CLI writes the completion JSON the miss sweep loads (`ops/reports/scheduler/completions/`, plus optional `schedule_heartbeat`). A failed CLI run is a fire (`exit_status != 0`). Silence (no row) is the miss. CI fixture clocks stay isolated unless `--completions-dir` is set.
- IMP-056: `lab migrate` is idempotent for `schedule_heartbeat`. Slot/anchor is catalog `local_time` on the fire's local calendar date; unscheduled weekday writes **no** completion row (stamp refused, not `late`). `lab schedule miss-check --baseline-before today` labels pre-today (Australia/Sydney) misses without deleting history.

