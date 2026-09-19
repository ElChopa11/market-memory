# Crypto / Equities thesis cards (Research sleeves)

Dedicated Research sleeves for crypto and equities (not publishing desks). **Research only. Not a trading decision.** Canonical desk: Research (Investment Research) / `research`.

Plan: [ops/plans/IMP-007-thesis-card-templates.md](../../ops/plans/IMP-007-thesis-card-templates.md).

Generic `templates/thesis.md` remains the **lifecycle spine** (`lab thesis new` still requires `intent.md` → `thesis.md`). These cards are companions, not a second backlog.

## Templates

| Desk | Template | Copied into workspace as |
|---|---|---|
| Research (Investment Research) / crypto sleeve | `templates/crypto-thesis-card.md` | `crypto-thesis-card.md` |
| Research (Investment Research) / equities sleeve | `templates/equities-thesis-card.md` | `equities-thesis-card.md` |

```bash
uv run lab thesis new \
  --goal "…" \
  --owner Research \
  --instrument BTC \
  --repo-root . \
  --no-db
```

`lab thesis new` copies the matching desk card when `--instrument` is in locked `config/universe.yaml` membership (or archived `deferred_must_cut`). BTC/ETH/UNI/AAVE → crypto card. NVDA/AVGO/SMH/MSFT/META/JPM/XLF/XOM → equities card. Unknown names keep the generic spine only.

Filesystem-only (no Postgres index): `--no-db` (same as the rest of Phase 4 research).

## Card contract

- **Principal membership:** `in_universe` | `watch_only` | `deferred_must_cut` | `not_in_membership` (IMP-005). Membership is not a Quant verdict and not a recommendation.
- **Watchlist tier:** `universe` | `monitor` | `blocked` | `unset` from [`config/watchlist/monitor.yaml`](../../config/watchlist/monitor.yaml). Research must state tier on every idea. Monitor-tier ideas publish UNSIZED. Intel owns ticker resolution.
- **Working Quant verdict:** closed set only (IMP-001) `RESEARCH_PRIORITY` | `MONITOR` | `DEFER` | `REJECT` | `INSUFFICIENT_DATA` — or `unset` until a Quant Board review exists. Do not invent a verdict.
- **Provenance:** source, timestamp, capture, evidence_confidence, observation id. Missing prints stay `unavailable`.
- **Knowledge watermark:** `as_of_knowledge` (lockstep with `ingested_at`). Never `published_at` / `market_time`.
- **Independent Skeptic stub:** required; verdict starts `pending` (never claimed as pass). Record via `lab skeptic`.
- **Non-goals (printed on the card):** no sizing, no execution / order intent, no investment-call language, no `config/universe.yaml` edits, author cannot be the sole Skeptic.

Crypto card: Hyperliquid public `/info` structure placeholders (funding, open interest, basis). No wallet types.

Equities card: filings / peers / liquidity placeholders. Post-IPO reclaim screening is [post-ipo-reclaim.md](post-ipo-reclaim.md) (`lab equities reclaim-screen`) — this card is not that screen. A drawdown is not a thesis.

## Language

Forbidden on cards (same gate as Quant Board): “active call,” MAKE, buy, sell, high confidence, sizing / order-instruction phrasing. `tests/unit/test_membership_vocab.py` lints every `templates/*.md` file.

## Lifecycle

Still: intent → thesis.md → research-plan → evidence links → Independent Skeptic. The desk card does not skip Skeptic, paper invalidation, or Principal gates. Rejected theses stay queryable.

See also: [research-workspace.md](research-workspace.md), [desk charters](../../ops/desk-charters.md).
