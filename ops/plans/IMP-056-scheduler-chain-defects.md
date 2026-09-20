# PLAN — IMP-056 Scheduler chain defects (heartbeat table, slot/anchor, miss baseline)

**Report status:** IN_PROGRESS (this PR).  
**Owner:** Ops  
**Scope:** Three Principal-ordered defects before Monday 06:30 AEST Sydney Morning. Paper only. No Telegram send. No group. No C-00x compute.

## Why

Sunday dry-run (2026-09-20) showed:

1. `lab schedule heartbeat` → `ProgrammingError: relation "schedule_heartbeat" does not exist`
2. Completion `grok.sydney_morning__20260917T203000Z.json` with Friday 17 Sep anchor and status `late` Δ≈2d, while the fire was Sun 20 Sep ~06:30 AEST
3. `lab schedule miss-check` returned `n_missed`≈99, burying Monday's result

## Outcome

- Idempotent Alembic `0012_heartbeat_if_not_exists` (plus 0011 `IF NOT EXISTS`) so `schedule_heartbeat` exists after `lab migrate`. Disk completions stay the primary log. Revision id fits Alembic `version_num` varchar(32).
- Slot/anchor = catalog `local_time` on the fire's local calendar date in the routine timezone. Unscheduled weekday → **no completion row** (stamp refused, never mere `late`).
- `lab schedule miss-check --baseline-before today` labels pre-today (Australia/Sydney date) closed windows as **known-missed**. History is labeled, not deleted. File: `ops/reports/scheduler/known-missed-baseline.yaml`.
- Pack path markdown-only envelope/provenance/gaps is queued as IMP-057 — does not block Monday.

## Tests

- `tests/unit/test_imp056_scheduler.py`
- `tests/unit/test_imp056_queue.py`
- existing IMP-042 / IMP-046 clocks still green
- integration: table present at Alembic head; persist still works for scheduled-day fires

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. No Redis. No Telegram send. SCHED-001 stays OPEN. No C-00x compute.

## Non-goals

Closing SCHED-001. Enforcing 6c-3 pack envelope on `--from-markdown` (IMP-057). Weekly authoring CLI. Lifting group freeze. Auto-merge.

## Rollback

Revert this PR. Disk completions remain. Baseline file is generated and gitignored. Table `schedule_heartbeat` may remain if migrate already ran — drop is 0011 downgrade.
