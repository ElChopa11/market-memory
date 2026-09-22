# ADR 0018 — Scheduler miss detector

- **Status:** Accepted
- **Phase:** IMP-042. No live trading. No signing. No Redis. SCHED-001 **CLOSED** 2026-09-22 (run_id `actions-b1-35727756341`; Actions clock #90; Grok app-routine clock `box-us-pre-20260922T133710Z`).

## Context

Sydney 08:00 digest never fired while NY sibling briefs completed (SCHED-001). A completion log written only when a job fires cannot detect a job that never runs.

## Decision

The scheduler **control** is a miss sweep: for each configured routine, if the window is closed and no completion row exists, escalate (non-zero `lab schedule miss-check`, OPEN ops artifact). Heartbeat-on-fire is a secondary log (`schedule_heartbeat`). CI uses a fixture clock so the check is non-flaky. Canaries are not in the catalog.

Hive `created_at` / `updated_at` / `ROUTINE_CHANGE` are not in this repo; they are not invented to suppress a closed window.

## Consequences

- SCHED-001 **CLOSED** citing run_id `actions-b1-35727756341` (hybrid-sydney-morning #1; stamp `857f55c` on `main`). Panel SCHEDULE cron is dead (7 routines, 0 fires). Panel WEBHOOK is dead (C1 silent). Actions cron + durable completion commit-back is the durable clock for `grok.sydney_morning`. Grok Bot app routines are a second working clock (run_id `box-us-pre-20260922T133710Z`). “No window yet” was never a close. See [ops/reports/incident-closures/20260922-sched-001-actions-invoker-close.md](../ops/reports/incident-closures/20260922-sched-001-actions-invoker-close.md).
- 06:30 / Fri 17:00 calendar hypotheses for *other* routines stay unverified until Don pastes Hive timestamps; they are not SCHED-001.
- Operators run `lab schedule miss-check`. `heartbeat-check` is an alias of that control, not a dump of heartbeat rows.
- Hybrid Step 4: Hive → lab CLI writes the completion JSON the miss sweep loads (`ops/reports/scheduler/completions/`, plus optional `schedule_heartbeat`). A failed CLI run is a fire (`exit_status != 0`). Silence (no row) is the miss. CI fixture clocks stay isolated unless `--completions-dir` is set.
- IMP-056: `lab migrate` is idempotent for `schedule_heartbeat`. Slot/anchor is catalog `local_time` on the fire's local calendar date; unscheduled weekday writes **no** completion row (stamp refused, not `late`). `lab schedule miss-check --baseline-before today` labels pre-today (Australia/Sydney) misses without deleting history.
- B1 Stage 1 (#90): Actions is the durable commit-back clock for `grok.sydney_morning` (`completions/` only). Grok Bot app routines are the agent-shaped clock (box CLI + local stamp). Panel SCHEDULE cron and panel WEBHOOK stay dead. Auto-review can force the Grok path dry (`--no-db`, DQ unavailable); whether that block is configurable is an open Principal question.
