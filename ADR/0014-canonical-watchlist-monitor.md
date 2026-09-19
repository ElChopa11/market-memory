# ADR 0014 — Canonical watchlist monitor.yaml (Principal 2026-09-19)

- **Status:** Accepted
- **Date:** 2026-09-19
- **Phase:** IMP-033 review-list lock. No live trading. No signing. No Redis. No universe promotion.

## Context

IMP-020 (#52) shipped a Research daily scan over `config/universe.yaml` `in_universe` ∪ `watch_only`. Principal then locked a complete review list (Operation Lunch Money) that is larger than membership, includes archive and blocked names, and requires Intel-owned ticker resolution plus EDGAR lockup formulas.

## Decision

| Piece | Rule |
|---|---|
| Review list | `config/watchlist/monitor.yaml` is THE complete list. Owner: Intel. Additions/removals = Principal PR only |
| Membership | Still `config/universe.yaml`. Monitor names are **not** promoted into `in_universe` |
| Tiers | `universe` (must match `in_universe`) / `monitor` (UNSIZED ideas) / `blocked` (state only) |
| Resolution | Exchange-qualified table. Unresolved (SAMSUN, KOSDA) render unresolved and are excluded from ideas |
| NEW_LISTING | `<200` daily bars → listings sleeve; SMA200 is an n/a string; post-IPO framework |
| Lockup | EDGAR-confirmed formulas. Do not assume flat 180d. Inside horizon → Skeptic (gate 5) blackout |
| Scan | `lab watchlist scan` walks monitor.yaml. Publishing desk remains Research |

## Consequences

- Same fixture twice → identical `content_hash`.
- Unresolved tickers never become ideas.
- CBRS / SPCX lockup blackouts stay fail-closed until the documented bound.

## Not this ADR

Universe ticker expansion. Live/signing/Redis. Paid data. Resolving SAMSUN/KOSDA.
