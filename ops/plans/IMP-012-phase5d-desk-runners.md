# PLAN — IMP-012 Phase 5d desk runners

**Report status:** READY (parked until IMP-011 merges). **Do not implement in the 5c PR.**  
**Owner:** Don / Chief of Staff (Coordinator) with Crypto / Equities / Quant desks as consumers  
**Scope (when started):** Desk orchestration that calls `mm_quant` + Market Memory and writes desk artifacts. No Telegram. No execution. No `live.yaml`.

## Why

Phase 5c lands the factor library. Desks still have skeleton packages (`mm_desks`) without runners. Principal lock: one phase per PR.

## Proposed outcome (later PR)

- Coordinator-run desk jobs that read Memory at an `as_of_knowledge` watermark and call `mm_quant`.
- Artifacts remain research-only (output contract / thesis cards / factor cards).
- Still not a trading decision.

## Non-goals

Telegram / 5e. Signing. `live.yaml`. Paid data. Reopening IMP-011 factor math except queue hygiene. Phase 6 bus. Order endpoints.

## Dependencies

IMP-011 Phase 5c quant factor library — this item stays READY/PARKED until that PR is `DONE`.

## Status

READY (parked; single-threaded — do not move to `IN_PROGRESS` while IMP-011 is open).
