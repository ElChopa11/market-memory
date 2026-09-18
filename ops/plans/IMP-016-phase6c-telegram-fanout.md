# PLAN — IMP-016 Phase 6c per-desk Telegram fan-out

**Report status:** READY (parked until IMP-015 merges). **Do not implement in the 6b PR.**  
**Owner:** Don / Chief of Staff (Coordinator)  
**Scope (when started):** Phase 6c — per-desk Telegram channels + presentation layer + chart desk + read-only inbound, on top of the PG NOTIFY mesh. No live trading. No execution. No `live.yaml`. No Redis.

## Why

Phase 5e delivers Telegram as a single Coordinator sink. Phase 6a/6b publish per-desk envelopes on Postgres NOTIFY. Operators still lack a desk→chat_id fan-out that is more than the Coord pack.

## Proposed outcome (later PR)

- Config-driven desk → `TELEGRAM_CHAT_ID_<DESK>` (env-only secrets) fan-out of already-built `--no-send` payloads.
- Presentation layer + chart desk + read-only inbound (Principal-locked 6c DoD; details filled when 6c starts).
- Hive PLAYBOOK (artifact ladder + Quant-owned trade math + sizing/DD/invalidation/concentration/post-mortem/DQ%) applies from Phase 6c onward and is absorbed here — **not** IMP-015.
- Quiet hours / completeness / dedupe from IMP-013 stay in force.
- Bus remains Postgres NOTIFY. Redis stays forbidden.

## Non-goals

Live trading. Signing. `live.yaml`. Redis. Listings/IPO desk (6d). Scorecards (6e). Decay/prompt versioning (6f). Reopening IMP-015 except queue hygiene. Paid Telegram SDKs. Implementing the Hive PLAYBOOK in 6b.

## Dependencies

IMP-015 Phase 6b flow+macro+regime — this item stays READY/PARKED until that PR is `DONE`.

## Status

READY (parked; single-threaded — do not move to `IN_PROGRESS` while IMP-015 is open).
