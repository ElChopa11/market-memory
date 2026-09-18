# PLAN — IMP-017 Phase 6d listings / IPO

**Report status:** IN_REVIEW (this PR).  
**Owner:** Research (Investment Research) — listings sleeve; Ops publishes  
**Scope:** Phase 6d — listings / IPO product on the five-desk roster + 6c PLAYBOOK + Ops-owned Telegram. No live trading. No execution. No `live.yaml`. No Redis. No 6e/6f.

## Why

6c-1..6c-5 are DONE on main. Operators still lacked a standing Research product for upcoming IPOs / direct listings, index add/delete/rebalance (separate stream), post-listing tracking, and own-history base rates — without inventing prints or adding a sixth desk.

## Outcome

- Queue: IMP-021 DONE (#53). IMP-017 this thread. OPEN incidents untouched. 6e/6f stay later.
- `lab listings scan --fixture PATH --no-send` emits a deterministic Research artifact.
- Naming via `mm_common.naming` (`listings` is a Research sleeve, not a sixth desk).
- Mesh envelope on `desk.research.output`. Ops `lab deliver listings` inherits `content_hash`.
- Closed Quant verdicts. Inherited `trade_math_hash` only. IC/Risk gates still required. No self-approve.
- Honest unavailable when the listing feed is missing. Point-in-time via `as_of_knowledge`.
- Screen-only names. No universe promotion.
- Zero LLM on the fixture path. `--no-send`. Paper stays closed.

Salvage: parked draft #48 (`packages/listings` engine, PIT helpers, tracking, base rates, Alembic `listing_outcome`). Rewired off the 11-desk sketch onto the five-desk roster.

## Tests

- `tests/unit/test_phase6d_listings.py`
- `tests/unit/test_phase6d_cli.py`
- `tests/unit/test_phase6d_cli_deliver.py`
- `tests/unit/test_phase6d_delivery.py`
- `tests/unit/test_phase6d_queue.py`
- `tests/adversarial/test_phase6d_point_in_time.py`

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. PG NOTIFY ids only. `--no-send` in tests. Ask before network/keys/order deps.

## Non-goals

Live trading. Signing. `live.yaml`. Redis. Scorecards automation (6e). Strategy decay-watch (6f). Universe promotion. Paid listing feeds. Closing OPEN incidents. Reopening the roster.

## Rollback

Revert this PR. Listings CLI and Research sleeve label go away. Five-desk roster, naming, watchlist, and Ops delivery stay on main. No live path exists to unwind.
