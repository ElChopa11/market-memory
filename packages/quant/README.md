# mm-quant

Phase 5c **quant factor library** (IMP-011). Quant & Market Structure Desk (Tier 4).

**May:** compute PIT-safe research factors from Memory/fixture observations; emit a factor QuantCard; classify a regime tag from **explicit YAML thresholds**.

**Must not:** depend on the `mm_execution` module or signing; call a trade; submit an order; skip Skeptic; invent missing feeds.

The working Quant Review Board remains `mm_research_kit.quant_review` (IMP-001 / IMP-008). This package does **not** replace Board verdicts. Desk runners that wire factors into desks are Phase 5d (`lab desk run`, IMP-012).

## Layout

| Path | Role |
|---|---|
| `mm_quant.factors.FactorRegistry` | momentum, realised vol, ADX-style, z-score, funding/basis carry, RS, breadth, corr, beta |
| `mm_quant.regime` | tag + confidence + driving inputs from `config/quant/regime.yaml` |
| `mm_quant.stats` | sample size, t-stat/bootstrap CI, deflated Sharpe / haircut, walk-forward, MAE/MFE, expectancy |
| `mm_quant.sizing` | vol-targeted + fixed-fractional → `% of research budget` only |
| `mm_quant.card` | `QuantCard` dataclass + markdown (`templates/quant-factor-card.md`) |

Config: [`config/quant/factors.yaml`](../../config/quant/factors.yaml), [`config/quant/regime.yaml`](../../config/quant/regime.yaml).

Runbook: [../../docs/runbooks/quant-desk.md](../../docs/runbooks/quant-desk.md).

Knowledge watermark is `as_of_knowledge` (lockstep with `ingested_at`). Never `published_at` / `market_time`.
