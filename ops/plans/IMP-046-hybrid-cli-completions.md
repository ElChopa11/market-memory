# PLAN — IMP-046 Hybrid Step 4: Hive CLI completion rows

**Report status:** DONE (#72).  
**Owner:** Ops  
**Scope:** Every Hive fire writes a completion row the IMP-042 miss detector can observe. `--no-send` only. Freeze held until Step 5a (DM-only). Paper only.

## Why

Hive is the clock; `lab` CLI is the only path that executes. Heartbeat-on-fire that never ran on that path is a log, not a control. Step 3 (outside this PR) made the three Grok routines CLI-clock only. This step stamps `run_id`, configured trigger, actual fire time, offset vs anchor, and exit status so `lab schedule miss-check` can see a fire vs a miss.

## Outcome

- `lab brief` / `lab deliver` / `lab schedule heartbeat` (alias `record-fire`) write JSON under `ops/reports/scheduler/completions/`.
- Failed CLI runs still write a row (`exit_status != 0` is a fire).
- Miss sweep loads disk rows (and optional `schedule_heartbeat`) unless a fixture clock is used without `--completions-dir`.
- SCHED-001 stays OPEN. No real Telegram send. Freeze holds.

## Tests

- `tests/unit/test_imp046_hive_completions.py` — fixture clock; CLI writes a row; miss detector sees fire vs miss
- `tests/unit/test_imp046_queue.py` — single IN_PROGRESS; IMP-043 DONE; 044/045 BACKLOG

## Non-goals

Real Telegram send (step 5). Hive prompt rewrites (step 3, done). Lift freeze. Equity/Polygon feature work. Closing SCHED-001. Delivery isolation (IMP-044). Per-desk topics (IMP-045). Auto-merge. Gate waiver.

## Rollback

Revert this PR. Miss sweep still runs; Hive fires go silent again on the completion log. No live path to unwind.
