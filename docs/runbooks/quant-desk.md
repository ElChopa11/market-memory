# Quant desk — factor library (Phase 5c / IMP-011)

Research-only factor math for the Quant & Market Structure Desk (Tier 4). **Not a trading decision. Not Execution. Not a desk runner.**

The Quant Review Board (IMP-001 / IMP-008) still lives in `mm_research_kit.quant_review` and still emits closed verdicts. This runbook is the **factor layer** in `packages/quant` (`mm_quant`). Wiring factors into desk orchestration is Phase **5d** (`lab desk run --all --fixture --no-send`).

## What operators can do

Compute PIT-safe factors from a fixture panel (or later, from Memory observations already filtered by `as_of_knowledge`):

```bash
uv run pytest tests/unit/test_phase5c_quant.py tests/adversarial/test_phase5c_point_in_time.py
```

There is **no** `lab quant-factors` desk runner in 5c. Same `params_hash` / `result_hash` twice on a fixture is the reproducibility gate (see unit tests).

## Config (auditable YAML)

Thresholds and windows are versioned files, not model-internal weights:

| File | Holds |
|---|---|
| [`config/quant/factors.yaml`](../../config/quant/factors.yaml) | Lookbacks, annualisation, RS/beta benches, sizing caps, stats seeds |
| [`config/quant/regime.yaml`](../../config/quant/regime.yaml) | Explicit vol / ADX / z-score / funding thresholds |

Changing a regime threshold **must** change the emitted tag (covered by tests). Do not hide cut-offs inside a fitted model.

## Factor catalog

| Name | Input | Notes |
|---|---|---|
| `momentum_short` / `momentum_long` | OHLCV close | Trailing bar return; crypto vs equity windows in YAML |
| `realised_vol_short` / `realised_vol_long` | Close returns | Sample stdev (ddof=1) × √ann_factor (365 crypto / 252 equity) |
| `adx` | High/low/close | Wilder ADX-style. Close-only → `unavailable` (range not invented) |
| `zscore` | Close | `(close − mean) / sample stdev` |
| `funding_carry` | Phase 5b `funding`, else `predicted_funding` | Missing both → `unavailable` |
| `basis_carry` | Phase 5b `basis_mark_oracle`, else `basis_perp_spot` | Missing both → `unavailable` |
| `relative_strength_btc` | Name vs BTC | Not reported for BTC itself |
| `relative_strength_sector` | Name vs sector ETF (SMH/XLF) or SPY when mapped | Missing bench → `unavailable` |
| `breadth` | Panel | Fraction of names with close > SMA |
| `correlation_matrix` | Panel returns | Pairwise Pearson; diagonal 1; mean pairwise as scalar |
| `beta` | Name vs BTC (crypto) or sector/SPY (equity) | OLS; missing bench → `unavailable` |

Every value carries provenance hooks: observation id and/or fixture id plus `as_of_knowledge`.

## Regime tag

`mm_quant.regime.classify_regime` emits:

- **tag** — `{low\|mid\|high}_vol_{trending\|chop}` with optional `_stretched` / `_crowded_funding`
- **confidence** — 0–1 coverage/sharpness score (**not** the phrase “high confidence”, not a trade conviction)
- **driving inputs** — vol, ADX, z-score, funding, and the YAML threshold block

If vol or ADX is missing, tag is `unavailable`. Never invent a regime.

## Stat helpers

`mm_quant.stats`: sample size, mean t-stat + normal CI, seeded bootstrap CI, Bailey–López de Prado deflated Sharpe, Bonferroni-style multiple-testing haircut (`SR / √n_tests`), expanding walk-forward splits with embargo, MAE/MFE, expectancy. Stdlib only.

## Sizing helpers (intent-level)

`vol_targeted_budget_pct` and `fixed_fractional_budget_pct` return **`budget_fraction_pct`** — a percentage of a research notional **budget**. They do not place orders, pick venues, or emit fills. Missing vol → `unavailable`, not `0`.

## Output card

Dataclass `mm_quant.QuantCard` (distinct from the IMP-001 review-board `QuantCard`). Markdown: [`templates/quant-factor-card.md`](../../templates/quant-factor-card.md). Review-board cards remain [`templates/quant-card.md`](../../templates/quant-card.md).

## Point-in-time law

Factors may use a bar only when `as_of_knowledge <= watermark` (lockstep with `ingested_at`). `market_time` / `published_at` are **not** knowledge. Adversarial fixture: `tests/fixtures/phase5c/lookahead_trap.json`.

Backtests still key off `available_at` (Phase 4). Map `as_of_knowledge` → `available_at` when a 5d runner feeds the harness; do not mix clocks.

## Degrade, never invent

Missing Polygon tape, missing HL structure, missing sector ETF → status `unavailable` / `partial`. Tests: `tests/fixtures/phase5c/missing_feeds.json`.

## Import walls

`packages/quant` must not import `mm_execution`, signing, or live-trade surfaces. Intel (`packages/ingest`) must not import `mm_quant`. CI: `scripts/check_import_boundaries.py` + `test.yml` greps.

## Gates kept

`live_trading_enabled: false`. `risk-config-guard`. `promote-gate`. PIT law. Degrade-never-invent. No secrets in git. No LLM at decision time.

## Not in 5c

Desk runners / orchestration (5d / IMP-012). Telegram (5e). Phase 6 bus. New paid deps. Polygon/HL adapter expansion. `live.yaml`. Order endpoints.
