# PLAN — IMP-041 Principal-locked desk knowledge base

**Report status:** DONE (#67). IMP-042 holds the single `IN_PROGRESS` slot.  
**Owner:** Ops (queue + pointer) / Principal (file lock)  
**Scope:** Seed `config/knowledge/` priors, failure modes, house lessons, and usage rules. Paper only. No candidate compute.

## Why

Desks had no Principal-locked prefix for literature priors, measurement failure modes, or dated house lessons. Without it, a strong prior can be misread as a trigger and a no-evidence pattern can be under-tested.

## Outcome

- Queue: IMP-041 **DONE** (#67). IMP-042 holds `IN_PROGRESS`. OPEN incidents untouched. No second `IN_PROGRESS`.
- `config/knowledge/{README,priors,failure-modes,house-lessons}.md` Principal-locked.
- Strong / moderate / no-comparable-evidence priors as specified. Standing rule: strong prior still needs our base rates; no-evidence prior needs MORE evidence.
- Failure modes each have: what it looks like, which test catches it, placeholder worked example.
- House lessons seeded with the five Principal-listed rows. File compounds from post-mortems.
- Usage: cached prompt prefix; prior never triggers/sizes; citing desk must label the prior; house lesson wins over prior with date + `run_id`.
- One-line “read before a round” pointer from AGENTS.md + desk-charters.
- Light smoke: the three content files exist and parse as markdown.

## Tests

- `tests/unit/test_imp041_knowledge.py`

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. No sizing. No candidate study results. No paid data.

## Non-goals

Strategy instructions. Sizing. Live path. Candidate compute. Displacing the SCHED/miss-detector thread. Closing OPEN incidents. Auto-merge. Gate waiver. Prompt auto-disable.

## Rollback

Knowledge tree is on `main` via #67. IMP-042 / IMP-039 / OPEN incidents unchanged. No live path exists to unwind.
