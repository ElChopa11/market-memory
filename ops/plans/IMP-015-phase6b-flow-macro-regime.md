# PLAN — IMP-015 Phase 6b flow + macro + regime

**Report status:** READY (parked until IMP-014 merges). **Do not implement in the 6a PR.**  
**Owner:** Don / Macro & Cross-Asset Desk + Data & Market Memory Desk  
**Scope (when started):** Flow and macro market-data packages plus a real regime tag (replacing the 6a `unset` placeholder). No live trading. No execution. No `live.yaml`. No Redis.

## Why

Phase 6a ships the mesh with `regime: unset` on every envelope. Cross-asset regime notes and flow/macro ingest were deferred from IMP-002 / IMP-014. Principal lock: one phase per PR.

## Proposed outcome (later PR)

- Read-only flow + macro adapters into Market Memory (degrade-never-invent).
- Envelope `regime` filled from versioned thresholds / 5c `mm_quant.regime`, not invented copy.
- Import walls unchanged. No Redis. Telegram fan-out stays 6c.

## Non-goals

Live trading. Signing. `live.yaml`. Redis. Per-desk Telegram channels (6c). Listings/IPO desk (6d). Scorecards (6e). Decay/prompt versioning (6f). Reopening IMP-014 except queue hygiene. Paid deps without Principal ask.

## Dependencies

IMP-014 Phase 6a PG NOTIFY mesh — this item stays READY/PARKED until that PR is `DONE`.

## Status

READY (parked; single-threaded — do not move to `IN_PROGRESS` while IMP-014 is open).
