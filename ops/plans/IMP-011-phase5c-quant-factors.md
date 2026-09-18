# PLAN — IMP-011 Phase 5c quant factor library

**Report status:** READY (parked until IMP-010 merges). **Do not implement in the 5b PR.**  
**Owner:** Don/Quant (Quant & Market Structure Desk)  
**Scope (when started):** Factor registry implementations in `packages/quant` for research-only features. No execution. No `live.yaml`. No Telegram.

## Why

Phase 5b lands Polygon + HL structure into Memory. Quant still has an empty `FactorRegistry` (IMP-009 skeleton). Principal lock: one phase per PR.

## Proposed outcome (later PR)

- Typed factor outputs with PIT watermarks (`available_at` / `as_of_knowledge`).
- Fixture-backed tests; degrade-never-invent on missing Memory rows.
- Still not a trading decision.

## Non-goals

Desk runners (5d). Telegram / 5e. Signing. `live.yaml`. Paid data. Reopening IMP-010 adapters.

## Dependencies

IMP-010 Phase 5b Polygon + HL structure — this item stays READY/PARKED until that PR is `DONE`.

## Status

READY (parked; single-threaded — do not move to `IN_PROGRESS` while IMP-010 is open).
