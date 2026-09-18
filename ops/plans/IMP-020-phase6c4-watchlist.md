# PLAN — IMP-020 Phase 6c-4 watchlist monitor + daily scan

**Report status:** DONE (#52).  
**Owner:** Research (Investment Research)  
**Scope:** Phase 6c-4 — daily watchlist monitor over the Principal-locked universe (`in_universe` ∪ `watch_only`). No live trading. No execution. No `live.yaml`. No Redis. No 6c-5 delivery expansion. No 6d listings. No universe promotion.

## Why

6c-1 locked the five-desk roster. 6c-2 locked naming. 6c-3 PLAYBOOK + Quant math is already on main (#47). Operators still lacked a standing Research product that scans the locked membership every day with provenance (`as_of_knowledge`, `content_hash`) without turning membership into a call.

## Outcome

- Queue: IMP-019 DONE (#51). IMP-020 this thread. IMP-017/021 PARKED. OPEN incidents untouched.
- `lab watchlist scan --fixture PATH --no-send` emits a deterministic Research artifact covering every locked name.
- Membership from `config/universe.yaml` only. `deferred_must_cut` stays archived. No promotion.
- Monitor states: `COVERED` | `PARTIAL` | `UNAVAILABLE`. Missing tape stays unavailable (never invented).
- Naming via `mm_common.naming` / `config/desks/naming.yaml` (`watchlist` is a Research sleeve, not a sixth desk).
- Mesh envelope on `desk.research.output` (existing 6a channel). PLAYBOOK idea flags only — trade math stays on `lab playbook run`.
- Zero LLM on the fixture path. `--no-send`. Paper only.

## Tests

- `tests/unit/test_phase6c4_watchlist.py`
- `tests/unit/test_phase6c4_queue.py`
- `tests/unit/test_phase6c4_cli.py`

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. PG NOTIFY ids only. `--no-send` in tests. Ask before network/keys/order deps.

## Non-goals

6c-5 delivery expansion. 6d listings/IPO. Universe promotion. Live/signing. Redis. New paid data. New Telegram routes. Live LLM HTTP.

## Rollback

Revert this PR. Watchlist CLI and Research sleeve label go away. Roster, naming, and PLAYBOOK stay on main. No live path exists to unwind.
