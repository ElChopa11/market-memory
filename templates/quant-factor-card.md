# Quant factor card (research-only). Fill via `mm_quant` (IMP-011). Not a call.

IMP-001 review-board cards stay at `templates/quant-card.md`. This template is the **factor-layer** card: every number needs an observation id / fixture id / `as_of_knowledge` provenance hook.

- **Instrument:**
- **Knowledge watermark (as_of_knowledge):**
- **Config version:**
- **Engine:**
- **params_hash:**
- **result_hash:**
- **Data-quality status:** `ok` | `partial` | `unavailable`
- **Regime tag:**
- **Regime confidence (0–1 coverage/sharpness; not a conviction label):**
- **Regime thresholds version:**
- **Driving inputs:**
- **Independent Skeptic review required:** yes (for any promotion; this card is not a verdict)

## Factors

| name | status | value | unit | window | provenance (observation/fixture@as_of_knowledge) | reason |
| --- | --- | --- | --- | --- | --- | --- |

Missing feeds stay `unavailable`. Do not invent.

## Intent-level budget fraction

Research helper only. `% of research budget`. Not an order, not a fill, not Execution.

| method | status | budget_fraction_pct | reason |
| --- | --- | --- | --- |

## Data gaps

Always list. Polygon/HL structure fields that were not in the panel stay `unavailable`.

Research only. Not a trade instruction, allocation decision, or execution approval. Intent-level budget fraction is not an order.
