# ADR 0005 — Flow / liquidity + macro regime (Phase 6b)

- **Status:** Accepted (Phase 6b). Follow-ons 6c–6f are **not** implemented here.
- **Date:** 2026-09-18
- **Deciders:** Principal (Phase 6a–6f locked; **bus = Postgres LISTEN/NOTIFY, no Redis**)
- **Phase:** 6b flow + macro packages + real envelope regime tag. No live trading. No signing. No Redis. No 6c Telegram fan-out.

## Context

Phase 6a shipped the desk mesh with `regime: unset` on every envelope. Cross-asset regime notes were deferred from IMP-002. Flow/liquidity metrics from existing HL structure and equities tape were not a standing desk product.

Without an explicit 6b ADR, later slices can sneak Redis, per-desk Telegram channels, paid vendors, or live paths into the first market-data phase after the mesh.

## Decision

1. **`packages/flow` (`mm_flow`)** computes PIT-safe funding z, OI delta, basis, depth/spread proxies, ADV/turnover, and slippage at configured clip sizes. Verdict `OK | THIN | UNTRADEABLE_AT_SIZE` plus max clip under the slippage budget. Derived observations use `as_of_knowledge = ingested_at`.
2. **`packages/macro` (`mm_macro`)** classifies a cross-asset regime from **explicit YAML** (`config/macro/regimes.yaml`) with two driving inputs (VIX + DXY) plus confidence. Missing feeds → `unavailable` / `DEGRADED`, never invented. Econ/CB calendar proximity emits `EVENT_RISK` + `rule_id`.
3. Desk runners `flow` and `macro` publish on the existing PG NOTIFY mesh. Coord still assembles if either fails (`FAILED` + `error_class`).
4. A successful macro run **replaces the envelope `regime` placeholder**. Instrument-level `mm_quant.regime` (vol/ADX) stays on Quant cards.
5. Risk YAML stubs (no LLM): auto-block `UNTRADEABLE_AT_SIZE`; `EVENT_RISK` size haircut. `live.yaml` is unchanged.

### What 6b includes vs defers

| Include in 6b | Defer |
|---|---|
| `mm_flow` + `mm_macro` + desk runners | 6c per-desk Telegram channel matrix |
| Envelope `regime` from macro YAML | 6d listings / IPO desk |
| EVENT_RISK + liquidity Risk YAML stubs | 6e scorecards |
| Fixtures + adversarial PIT | 6f decay / prompt versioning |
| Runbooks + this ADR | Redis, live trading, signing, paid vendors |

## Consequences

- **Positive:** Envelopes carry an auditable regime tag; liquidity and calendar risk are deterministic inputs to Risk; Coord remains available when a desk is down.
- **Negative:** Regime is cross-asset, not per-instrument. Live FRED/DXY still degrade without keys.
- **Follow-ups:** IMP-016 / Phase 6c Telegram fan-out — READY/PARKED.

## Notes

Live trading remains disabled. Flow/macro/desks/quant/research/delivery must not import `mm_execution`. Do not add Redis.
