# PLAN — IMP-015 Phase 6b flow + macro + regime

**Report status:** IN_REVIEW (this PR).  
**Owner:** Don / Macro & Cross-Asset Desk + Data & Market Memory Desk  
**Scope:** Flow and macro market-data packages plus a real regime tag (replacing the 6a `unset` placeholder). No live trading. No execution. No `live.yaml`. No Redis. No Phase 6c Telegram fan-out.

## Why

Phase 6a ships the mesh with `regime: unset` on every envelope. Cross-asset regime notes and flow/macro ingest were deferred from IMP-002 / IMP-014. Principal lock: one phase per PR. Bus remains Postgres NOTIFY.

## Outcome

- Queue: IMP-014 DONE (#45). This item the implementation thread. IMP-016 Phase 6c parked.
- `packages/flow` (`mm_flow`): funding z, OI delta, basis, depth/spread, ADV/turnover, slippage @ clips; verdict `OK|THIN|UNTRADEABLE_AT_SIZE` + max clip; PIT observations.
- `packages/macro` (`mm_macro`): FRED/curve/DXY/credit/commodities/VIX as available; econ+CB calendar; regime classifier from `config/macro/regimes.yaml` (tag + confidence + two driving inputs). Missing feeds → unavailable/DEGRADED.
- Envelope `regime` filled when the macro run succeeds.
- `EVENT_RISK` within N minutes of high-impact events; `rule_id` for Risk haircut.
- Risk YAML stubs: auto-block `UNTRADEABLE_AT_SIZE`; `EVENT_RISK` size haircut. No LLM.
- Desk runners publish via the 6a mesh. Coord assembles if one fails.
- Fixtures + adversarial PIT. Runbooks + ADR 0005. README Phase 6 in progress (6b).

## Tests

- `tests/unit/test_phase6b_flow.py`
- `tests/unit/test_phase6b_macro.py`
- `tests/unit/test_phase6b_envelope.py`
- `tests/unit/test_phase6b_risk.py`
- `tests/unit/test_phase6b_queue.py`
- `tests/adversarial/test_phase6b_point_in_time.py`

## Gates kept

`live_trading_enabled: false`. risk-config-guard. promote-gate. PIT. degrade-never-invent. No secrets in git. Import walls (flow/macro vs execution; Intel vs opine). Ask before any new network/keys/order dependency.

## Non-goals

Redis. Per-desk Telegram fan-out (6c). Listings/IPO desk (6d). Scorecards (6e). Decay/prompt versioning (6f). Live trading. Signing. Order endpoints. New paid data vendors. Reopening IMP-014 except queue hygiene.

## Status

IN_REVIEW (this PR). IMP-014 is DONE (#45). IMP-016 Phase 6c is READY/PARKED — do not implement Telegram fan-out here.
