# PLAN — IMP-013 Phase 5e Telegram delivery

**Report status:** READY (parked until IMP-012 merges). **Do not implement in the 5d PR.**  
**Owner:** Don / Chief of Staff (Coordinator)  
**Scope (when started):** Telegram Bot API send, schedules, secret handling. No live trading. No execution. No `live.yaml`.

## Why

Phase 5d prepares `--no-send` payload strings and dry-run files. Delivery still has `SEND_ENABLED = False`. Principal lock: one phase per PR.

## Proposed outcome (later PR)

- Telegram client behind explicit send enablement and Principal-scoped secrets (env only; never git).
- Schedules for desk packs / Pulse — no alert spam without thresholds.
- Import walls unchanged: delivery still must not import `mm_execution`.

## Non-goals

Live trading. Signing. `live.yaml`. Phase 6 PG NOTIFY bus / multi-channel mesh. Reopening IMP-012 runners except queue hygiene. Paid deps. Redis.

## Dependencies

IMP-012 Phase 5d desk runners — this item stays READY/PARKED until that PR is `DONE`.

## Status

READY (parked; single-threaded — do not move to `IN_PROGRESS` while IMP-012 is open).
