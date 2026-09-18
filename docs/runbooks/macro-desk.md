# Macro sleeve (Phase 6b / IMP-015; Intel-owned as of 6c-1)

Cross-asset regime tag and calendar `EVENT_RISK`. **Not a call. Not an allocation. Not a publishing desk.**

Package: `packages/macro` (`mm_macro`). Intel sleeve: `mm_desks.macro` via `lab desk run --desk intel`.

## What operators can do

```bash
uv run lab desk run --desk intel --fixture tests/fixtures/phase6b/frozen_day.json --no-send --no-db
uv run pytest tests/unit/test_phase6b_macro.py tests/adversarial/test_phase6b_point_in_time.py
```

A successful Intel macro sleeve **replaces the 6a envelope `regime: unset` placeholder** with the YAML tag. Missing VIX or DXY → tag `unavailable` / Intel `DEGRADED`; other envelopes keep `unset`. Ops still assembles if Intel is killed.

## Regime classifier

Thresholds live in [`config/macro/regimes.yaml`](../../config/macro/regimes.yaml). Two driving inputs are required:

| Input | Buckets |
|---|---|
| VIX | `risk_on` / `risk_neutral` / `risk_off` |
| DXY | `usd_weak` / `usd_mid` / `usd_strong` |

Tag example: `risk_on_usd_mid`. Confidence is coverage/sharpness in `[0, 1]` — **not** the phrase “high confidence”, not a trade conviction.

Optional context when present (never invents a tag): US10Y, US2Y, T10Y2Y, HY OAS, WTI. FRED series ids are listed in the same YAML. Missing `FRED_API_KEY` on a live ingest stays `unavailable`.

This is **distinct** from the instrument-level `mm_quant.regime` vol/ADX tag (Phase 5c).

## EVENT_RISK

Within `window_minutes` of a **high-importance** calendar event, ideas are tagged `EVENT_RISK` with `rule_id: event_risk` for a Risk size haircut (YAML `haircut_pct`). Calendar knowledge is PIT-filtered (`as_of_knowledge` / `ingested_at` ≤ watermark).

## Envelope header

`stamp_output` / `apply_regime_to_context` copy a successful tag onto every desk envelope. Mesh channels: `desk.intel.output`, `desk.intel.alert`, `dq.event` on degrade.

## Import walls

`packages/macro` must not import `mm_execution` or Redis. Intel must not import `mm_macro`.

## Not this phase

Per-desk Telegram fan-out (6c). Live FRED as a silent default. Inventing missing prints. Live trading / signing.
