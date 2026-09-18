# PLAN — IMP-010 Phase 5b Polygon equities + HL structure

**Report status:** READY (parked until IMP-009 merges). **Do not implement in the 5a PR.**  
**Owner:** Don/Data (Data & Market Memory Desk) + Crypto / Equities desks as consumers  
**Scope (when started):** Polygon as default equities vendor; Hyperliquid funding / OI / basis / depth; spot cross-check. Read-only public / ToS-compliant ingest into Market Memory. No Telegram. No execution. No `live.yaml`.

## Why

Phase 5a commits desk boundaries only. Equities still have no durable tape in Memory. Crypto structure (funding, OI, basis, depth) is not a standing desk product. Principal lock: **equities default = Polygon**.

## Proposed outcome (later PR)

- Polygon equities adapter (ToS, secrets in env not git, degrade-never-invent).
- HL public `/info` (and documented public market-data) for funding, open interest, basis, depth.
- Spot cross-check (crypto) without treating divergence as executable-arb unless criteria are complete.
- Tests + source-health inventory updates. Universe ticker set unchanged unless Principal expands membership.

## Non-goals

Desk full runners. Quant factor library. Telegram / 5e delivery. Signing / `hl_trade`. Risk service. Live path. Paid deps without Principal ask. Reopening IMP-009 docs.

## Dependencies

IMP-009 Phase 5a desk boundaries — this item stays READY/PARKED until that PR is `DONE`.

## Status

READY (parked; single-threaded — do not move to `IN_PROGRESS` while IMP-009 is open).
