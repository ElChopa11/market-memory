# PLAN — IMP-011 Phase 5c quant factor library

**Report status:** IN_REVIEW (this PR).  
**Owner:** Don/Quant (Quant & Market Structure Desk)  
**Scope:** Factor registry implementations in `packages/quant` (`mm_quant`). Research-only. No execution. No `live.yaml`. No Telegram. No desk runners.

## Why

Phase 5b (#41) landed Polygon + HL structure into Memory. Quant still had an empty `FactorRegistry` (IMP-009 skeleton). Principal lock: one phase per PR.

## Outcome

- Typed factor outputs with PIT watermarks (`as_of_knowledge`; map to backtest `available_at` later).
- Regime classifier from **explicit** `config/quant/regime.yaml` thresholds (tag + confidence + driving inputs).
- Stat rigor helpers (sample size, t-stat/bootstrap CI, deflated Sharpe / haircut, walk-forward, MAE/MFE, expectancy).
- Sizing helpers returning **% of research budget** only (intent-level).
- `mm_quant.QuantCard` → `templates/quant-factor-card.md` with provenance on every number.
- Fixture-backed unit + adversarial PIT tests; degrade-never-invent on missing feeds.
- Still not a trading decision.

## Tests

- `tests/unit/test_phase5c_quant.py`
- `tests/unit/test_phase5c_queue.py`
- `tests/adversarial/test_phase5c_point_in_time.py`
- Import-boundary CI unchanged (quant must not import `mm_execution`).

## Gates kept

`live_trading_enabled: false`. risk-config-guard. promote-gate. PIT law (`as_of_knowledge` = knowledge clock). Degrade-never-invent. No secrets in git. No new network/keys/order dependency.

## Non-goals

Desk runners (5d / IMP-012). Telegram / 5e. Signing. `live.yaml`. Paid data. Reopening IMP-010 adapters. LLM at decision time.

## Status

IN_REVIEW (IMP-011 merged as #42). IMP-012 Phase 5d is the following implementation thread.
