# Flow / liquidity desk (Phase 6b / IMP-015)

Research-only liquidity metrics for existing Hyperliquid structure and equities tape. **Not an order. Not Execution. Clip sizes are configured research notionals.**

Package: `packages/flow` (`mm_flow`). Desk runner: `mm_desks.flow` (`lab desk run --desk flow`).

## What operators can do

```bash
uv run lab desk run --desk flow --fixture tests/fixtures/phase6b/frozen_day.json --no-send --no-db
uv run pytest tests/unit/test_phase6b_flow.py tests/adversarial/test_phase6b_point_in_time.py
```

Mesh publish uses the existing Postgres `LISTEN/NOTIFY` bus (`desk.flow.output`). Coord still assembles if flow is missing or killed.

## Metrics

| Name | Input | Notes |
|---|---|---|
| `funding_z` | HL `funding` history | Sample z-score over YAML window. Too few prints → `unavailable` |
| `oi_delta` | `open_interest` | Last minus lookback. Missing OI → `unavailable` |
| `basis` | `basis_mark_oracle` else `basis_perp_spot` | Latest visible |
| `spread_bps` | `l2_spread` / `l2_mid` | Spread / mid × 1e4 |
| `depth_usd` | `l2_bid_notional` + `l2_ask_notional` | Top-of-book notional |
| `adv_notional` / turnover | OHLCV `volume * close` | YAML window |
| slippage @ clips | book impact, else ADV `k √(clip/ADV)` | Configured `clip_sizes_usd` |

## Liquidity verdict

`OK | THIN | UNTRADEABLE_AT_SIZE` plus **max clip under the slippage budget**. Missing book and ADV → `unavailable` (never invented sizes). Risk YAML auto-blocks `UNTRADEABLE_AT_SIZE` (`rule_id: untradeable_at_size`).

Config: [`config/flow/liquidity.yaml`](../../config/flow/liquidity.yaml).

## Point-in-time law

Only points with `as_of_knowledge <= watermark` (lockstep with `ingested_at`). Adversarial fixture: `tests/fixtures/phase6b/lookahead_trap.json`.

Derived observations set `as_of_knowledge = ingested_at`.

## Import walls

`packages/flow` must not import `mm_execution` or Redis. Intel (`packages/ingest`) must not import `mm_flow`. CI: `scripts/check_import_boundaries.py`.

## Not this phase

Per-desk Telegram fan-out (6c). Listings/IPO (6d). Scorecards (6e). Decay/prompt versioning (6f). Live trading, signing, Redis, paid data vendors.
