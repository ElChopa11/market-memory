# PLAN — IMP-042 Scheduler miss detector

**Report status:** IN_PROGRESS (this PR).  
**Owner:** Ops  
**Scope:** MERGE-BLOCKING miss sweep. Closed window + no completion row → escalate. Heartbeat-on-fire is a secondary log. Paper only. No live trading.

## Why

SCHED-001: Sydney 08:00 digest had weekday windows and never fired while NY siblings completed. There was no standing check. A write-on-fire heartbeat without a miss sweep is a log, not a control. This must land before Mon 21 Sep 06:30 AEST.

## Outcome

- Queue: IMP-040 DONE (#66). This item is the only `IN_PROGRESS`. SCHED-001 stays OPEN (P0). Do not close on “no window yet”.
- Principal L2 sprint intake: P0 this thread → P1 Phase-1 Memory rates (expand if #66 fixture-only) → P2 instance ledger → P3 truth-in-repo. P1/P2/P3 are **not** this PR.
- `lab schedule miss-check` (alias `heartbeat-check`) is the control.
- CI runs miss-check on `tests/fixtures/scheduler/ci_clock.yaml` with `--now 2026-09-19T09:49:00Z`.
- Table `schedule_heartbeat` is the completion log (secondary).
- Root-cause report separates (a) 08:00 unexplained OPEN from (b) 06:30 / Fri 17:00 unverified Hive timestamps.
- Canaries ignored.

## Tests

- `tests/unit/test_imp042_heartbeat.py` — delta math, miss, CI clock, CLI
- `tests/unit/test_imp042_queue.py`
- `tests/unit/test_imp042_import_boundary.py`
- `tests/integration/test_imp042_schedule_heartbeat.py`

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. No Redis. No canary code. No auto-close of SCHED-001.

## Non-goals

Closing SCHED-001. Phase-1 rate expansion. Instance ledger. Source-health regen. Desk naming. Telegram inventory. SRC-object_store. Candidate study compute. Paid adapters. Auto-merge. Gate waiver.

## Rollback

Revert this PR. `schedule_heartbeat` and miss-check go away. Five-desk roster and IMP-040 stay. SCHED-001 remains OPEN. No live path exists to unwind.
