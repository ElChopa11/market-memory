# mm-delivery

Phase 5d **no-send** payload strings. Telegram Bot API send, schedules, and secrets are **Phase 5e** (IMP-013).

**Must not (this phase):** send messages; hold bot tokens; depend on the `mm_execution` module; schedule live jobs.

`SEND_ENABLED` stays false until a Principal-scoped 5e PR. `prepare_payload` builds dry-run strings only.

See [../../ADR/0002-desk-delivery-architecture.md](../../ADR/0002-desk-delivery-architecture.md).
