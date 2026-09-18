# PLAN — IMP-033 Canonical watchlist monitor.yaml (Principal lock)

**Report status:** IN_PROGRESS (this intake PR — paper only).  
**Owner:** Ops (queue + Telegram hold) / Research (scan remains IMP-020 product)  
**Scope:** Queue intake + thin plan. Versioned `config/watchlist/monitor.yaml` encodes the Principal lock with tiers/clusters (crypto then base). Implementation lives on the sister agent *Canonical watchlist monitor.yaml Principal lock*. **Do not reopen IMP-020.** No live trading. No execution. No `live.yaml`. No credentials. No delivery send-path edits.

## Why

IMP-020 (#52) already ships `lab watchlist scan` over locked `in_universe` ∪ `watch_only` (ADR 0009, [docs/runbooks/watchlist.md](../../docs/runbooks/watchlist.md)). Membership is already locked in [`config/universe.yaml`](../../config/universe.yaml). What is missing is a versioned monitor config that the scan reads for Principal-locked **tiers/clusters** (crypto then base). Until that file is merged, Ops (sole publisher) holds Telegram.

This item is **intake**. The sister agent writes `config/watchlist/monitor.yaml`. This PR does not re-implement the monitor product.

## Principal lock (already in universe.yaml)

| Partition | Crypto | Equities |
|---|---|---|
| `in_universe` | BTC | NVDA, AVGO, MSFT, META, JPM, XOM |
| `watch_only` | ETH, UNI, AAVE | SMH, XLF |
| `deferred_must_cut` | archived (HYPE, SOL, XRP, ARB, NEAR, LINK) | archived (GLD, LLY) |

Membership is not a call. No universe expand.

## Outcome

- Queue: IMP-032 DONE (#57). IMP-033 this thread (only `IN_PROGRESS`). OPEN incidents untouched (SCHED-001, BRIEF-TAG-20260918, SRC-STOOQ-404, SRC-FRED-MISSING-ENV).
- Versioned `config/watchlist/monitor.yaml` encodes the lock + tiers/clusters (crypto then base).
- `lab watchlist scan` (or equivalent) becomes config-backed. Existing IMP-020 product, ADR 0009, and runbook stay the product SoT.
- Ops does not publish / send until the scan is config-backed.
- Implementation PR: sister agent *Canonical watchlist monitor.yaml Principal lock* (link when opened).

## Pointers (do not reopen IMP-020)

- Plan: [IMP-020-phase6c4-watchlist.md](IMP-020-phase6c4-watchlist.md) — DONE (#52)
- ADR: [0009-phase6c4-watchlist.md](../../ADR/0009-phase6c4-watchlist.md)
- Runbook: [docs/runbooks/watchlist.md](../../docs/runbooks/watchlist.md)
- Product spec still on main: `config/desks/watchlist.yaml` (IMP-020). Sister PR adds `config/watchlist/monitor.yaml`.

## Tests

- `tests/unit/test_imp033_queue.py` (this intake)
- Sister implementation PR owns monitor.yaml / scan-config tests

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. No delivery send-path edits. `--no-send` remains default. Ask before network/keys/order deps.

## Non-goals

Reopening IMP-020. Re-implementing the monitor. Universe ticker expansion. Treating membership as a call. Closing OPEN incidents. `live.yaml`. Signing. Redis. Delivery send. Auto-publish Telegram before config-backed. Paid data.

## Rollback

Revert this intake PR. Queue loses IMP-033. IMP-020 monitor on main is unchanged. No live path exists to unwind.
