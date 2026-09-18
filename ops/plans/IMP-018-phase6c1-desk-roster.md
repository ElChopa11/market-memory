# PLAN — IMP-018 Phase 6c-1 desk consolidation (11 → 5)

**Report status:** DONE (#49).  
**Owner:** Don / Ops (orchestration)  
**Scope:** Phase 6c-1 — roster cutover to exactly five publishing desks matching the Principal hive. No live trading. No execution. No `live.yaml`. No Redis. No 6c-2 naming layer, 6c-4 watchlist, 6c-5 delivery expansion, or 6d listings.

## Why

Phase 5/6a/6b grew eleven publishing slugs (intel, crypto, equities, flow, macro, quant, skeptic, risk, coord, chart, briefing). Principal resume-build order 2026-09-19 locks the hive at five desks. Don/Coord is orchestration only.

## Outcome

- Queue: OPEN incidents logged (SCHED-001, BRIEF-TAG-20260918, SRC-STOOQ-404, SRC-FRED-MISSING-ENV). IMP-016 DONE (#47). IMP-017 PARKED until 6c-1..6c-5 complete.
- Publishing desks: `intel` | `research` | `quant` | `ic_risk` | `ops`.
- Sleeves (not desks): crypto+equities+chart → Research; flow+macro+briefing → Intel; skeptic+risk → IC/Risk (two gates); Coord pack → Ops.
- Mesh still Postgres LISTEN/NOTIFY. `coord.assemble` remains the orchestration channel, not a desk slug.
- Delivery stays Ops-owned. Fan-out matrix cut over to the five slugs. No new 6c-5 features.
- Import-boundary CI stays statement-anchored (`^[ \t]*(import mm_execution|from mm_execution)\b` and AST equivalent).

## Tests

- `tests/unit/test_phase6c1_roster.py`
- `tests/unit/test_phase6c1_queue.py`
- `tests/unit/test_import_boundaries.py` (comment vs real import)

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. PG NOTIFY ids only. `--no-send` in tests. Ask before network/keys/order deps.

## Non-goals

6c-2 naming. 6c-3 ladder/math (already on main via #47). 6c-4 watchlist. 6c-5 delivery expansion. 6d listings. Live/signing. Redis. New paid deps.

## Rollback

Revert this PR. Cadence/telegram YAML and `mm_desks.PIPELINE` return to the Phase 6b/6c eleven-slug roster. No live path exists to unwind.
