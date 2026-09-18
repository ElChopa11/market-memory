# PLAN — IMP-019 Phase 6c-2 naming / display layer

**Report status:** IN_REVIEW (this PR).  
**Owner:** Don / Ops (orchestration)  
**Scope:** Phase 6c-2 — single naming/namespace layer on the five-desk roster. No live trading. No execution. No `live.yaml`. No Redis. No 6c-4 watchlist, 6c-5 delivery expansion, or 6d listings.

## Why

6c-1 (#49) locked publishing slugs. Principal-facing titles, Telegram headers, PLAYBOOK artifact labels, and leftover Phase-5 desk names (`Crypto Desk`, skeptic-as-desk) were still ad-hoc.

## Outcome

- Queue: IMP-018 DONE (#49). IMP-019 this thread. IMP-017/020/021 PARKED.
- Module: `mm_common.naming` + `config/desks/naming.yaml` (must match).
- Publishing desks: `intel` | `research` | `quant` | `ic_risk` | `ops` with canonical display names.
- Coord orchestration label only. Alerts is an Ops-owned Telegram sink.
- PLAYBOOK types: stable machine ids vs human labels; owning desk slug on ladder artifacts/envelopes.
- Unknown slug / artifact type fails closed (`UnknownNameError`).
- Runbooks and remaining old names updated to the five-desk vocabulary.

## Tests

- `tests/unit/test_phase6c2_naming.py`
- `tests/unit/test_phase6c2_queue.py`

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. PG NOTIFY ids only. `--no-send` in tests. Ask before network/keys/order deps. Statement-anchored `mm_execution` import guard unchanged.

## Non-goals

6c-4 watchlist. 6c-5 delivery expansion. 6d listings. Live/signing. Redis. New paid deps. Reopening the 6c-1 roster.

## Rollback

Revert this PR. Display strings fall back to 6c-1 `DESK_META` tuples and Phase-5 titles. No live path exists to unwind.
