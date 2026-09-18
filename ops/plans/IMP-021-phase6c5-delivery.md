# PLAN — IMP-021 Phase 6c-5 delivery expansion (Ops-owned)

**Report status:** IN_REVIEW (this PR).  
**Owner:** Ops  
**Scope:** Phase 6c-5 — Ops-owned Telegram fan-out / channel matrix / presentation bound to the five-desk naming layer, plus delivery of IMP-020 watchlist monitor artifacts. No live trading. No execution. No `live.yaml`. No Redis. No 6d listings/IPO. No universe promotion.

## Why

6c-1 cut Telegram routes to five desks. 6c-2 locked naming. 6c-4 shipped the Research watchlist scan with **no new Telegram route**. Coordinator copy still read like the publisher. 6c-5 finishes Ops ownership: channel matrix fail-closed against `mm_common.naming`, presentation headers from the naming layer, and `--no-send` fan-out of the watchlist artifact.

## Outcome

- Queue: IMP-020 DONE (#52). This item the implementation thread. IMP-017 PARKED until 6c-1..6c-5 complete. OPEN incidents untouched (SCHED-001, SRC-STOOQ-404, SRC-FRED-MISSING-ENV, BRIEF-TAG).
- `config/delivery/telegram.yaml`: `owner: ops`, `publisher: ops`, `coordinator: orchestration_only`. Desks = naming `ROUTE_SLUGS` (`intel` `research` `quant` `ic_risk` `ops` + `alerts`). Retired slugs fail closed.
- Products: `watchlist` → Research desk, kind `watchlist`, sleeve `watchlist`, inherit `content_hash`.
- `lab deliver watchlist --fixture PATH --no-send` presents the IMP-020 scan (inventory, not ideas) and fans out research + Ops mirror. Coord does not publish.
- Quiet hours, idempotency `(desk, as_of, content_hash)`, rate limits, numeric thresholds, `--no-send` default. Pytest never hits live Telegram.
- Runbooks + ADR 0010. README Phase 6 in progress (6c-5).

## Tests

- `tests/unit/test_phase6c5_delivery.py`
- `tests/unit/test_phase6c5_queue.py`
- `tests/unit/test_phase6c5_cli.py`

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. PG NOTIFY ids only. `--no-send` in tests. Ask before network/keys/order deps.

## Non-goals

6d listings/IPO. Live trading / signing / `live.yaml`. Redis. Universe promotion. New paid data. Waiving Skeptic/Risk. Closing OPEN incidents. Inventing watchlist ideas or trade math.

## Rollback

Revert this PR. Watchlist stays a Research scan (`lab watchlist scan`). Fan-out matrix remains the five-desk 6c-1 routes. No live path exists to unwind.
