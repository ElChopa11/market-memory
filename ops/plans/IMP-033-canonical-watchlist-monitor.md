# PLAN — IMP-033 Canonical watchlist monitor.yaml

**Report status:** DONE (#59). SAMSUN/KOSDA resolved in IMP-034.  
**Owner:** Intel (resolution + EDGAR lockup) / Ops (queue + scan wire)  
**Scope:** Principal-lock `config/watchlist/monitor.yaml` as THE complete review list (2026-09-19, Operation Lunch Money). Wire `lab watchlist scan`. No universe promotion. Paper only.

## Why

IMP-020 scans locked `in_universe` ∪ `watch_only`. Principal then locked a larger review list (crypto 06:30 Syd, base 23:00 Syd) with tiers, clusters, ticker resolution, NEW_LISTING handling, and EDGAR-confirmed lockups. The path `config/watchlist/monitor.yaml` was 404 on main.

## Outcome

- Queue: IMP-032 DONE (#57). IMP-033 this thread. OPEN incidents untouched.
- Intel-owned `config/watchlist/monitor.yaml`. Additions/removals = Principal PR only.
- Universe tier matches locked `in_universe` only (BTCUSD, NVDA). No promotion into `universe.yaml`.
- Blocked: CASHCAT, PONSUSD. Monitor-by-archive: HYPEUSD, SOLUSD, NEARUSD, ARBUSD.
- Unresolved only: SAMSUN, KOSDA. Do not invent.
- Resolved HL perps (USD): VVVUSD→HL:VVV (coin VVV on HL per Intel snapshot), PURR→HL:PURR, CHIPIUSD display→HL:CHIP (Principal coin-id confirm; CHIPI absent on HL meta — do not invent CHIPI). SPCX→NASDAQ:SPCX (idio, pending corr). CBRS→NASDAQ:CBRS (semis_ai).
- EDGAR lockups confirmed; **not** a flat 180d. Lockup inside horizon = gate 5 blackout.
- NEW_LISTING → listings sleeve; SMA200 `n/a (insufficient history: <n> bars)`.
- Research states watchlist tier on every idea. Monitor ideas UNSIZED.
- `lab watchlist scan --fixture --no-send` walks the review list. Zero LLM. Paper only.

## Tests

- `tests/unit/test_imp033_watchlist_monitor.py`
- `tests/unit/test_imp033_queue.py`
- Existing IMP-020 / delivery tests updated for the review list

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. `--no-send`. Ask before network/keys/order deps.

## Non-goals

Universe promotion. Guessing SAMSUN/KOSDA. Live/signing. Redis. Paid data. Closing OPEN incidents. Auto-merge. Gate waiver.

## Rollback

Revert this PR. IMP-020 scan-of-locked-membership stays on main. `universe.yaml` is unchanged. No live path exists to unwind.
