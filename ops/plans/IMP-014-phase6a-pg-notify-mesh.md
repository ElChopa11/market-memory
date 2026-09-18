# PLAN — IMP-014 Phase 6a PG LISTEN/NOTIFY mesh

**Report status:** READY (parked until IMP-013 merges). **Do not implement in the 5e PR.**  
**Owner:** Don / Chief of Staff (Coordinator)  
**Scope (when started):** Postgres `LISTEN/NOTIFY` (or equivalent) so desk products fan out to per-desk workers / extra channels. No live trading. No execution. No `live.yaml`.

## Why

Phase 5e delivers Telegram as a single channel from Coordinator `lab deliver`. A multi-channel mesh (per-desk workers, extra chat products, bus) must not sneak into the first send client. Principal lock: one phase per PR.

## Proposed outcome (later PR)

- Durable notify bus keyed off Market Memory / pack artifacts.
- Per-desk workers consume notifications; Telegram remains one sink, not the bus.
- Import walls unchanged: delivery still must not import `mm_execution`.

## Non-goals

Live trading. Signing. `live.yaml`. Redis-as-source-of-truth. Reopening IMP-013 Telegram client except queue hygiene. Paid deps. Order endpoints.

## Dependencies

IMP-013 Phase 5e Telegram delivery — this item stays READY/PARKED until that PR is `DONE`.

## Status

READY (parked; single-threaded — do not move to `IN_PROGRESS` while IMP-013 is open).
