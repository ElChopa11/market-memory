# ADR 0010 — Phase 6c-5 Ops-owned delivery expansion

- **Status:** Accepted
- **Date:** 2026-09-18
- **Phase:** 6c-5 delivery expansion. No live trading. No signing. No Redis. No 6d listings.

## Context

Phase 6c (#47) shipped per-desk Telegram fan-out. Phase 6c-1 (#49) cut the roster to five publishing desks. Phase 6c-2 (#51) locked naming. Phase 6c-4 (#52) shipped a Research watchlist monitor with no Telegram route. Delivery copy and CLI still described Coordinator as the publisher. Watchlist artifacts had no Ops fan-out.

## Decision

Ops owns delivery. Coord/Don orchestrates and does not publish.

| Piece | Rule |
|---|---|
| Publisher | `ops`. `config/delivery/telegram.yaml` `owner` / `publisher` must be `ops`. |
| Channel matrix | Desk keys = `mm_common.naming.ROUTE_SLUGS` (five desks + `alerts`). Unknown / retired slug fails closed. |
| Presentation | Telegram banners from `telegram_header` (desk + optional sleeve / artifact). Unknowns are `?`. |
| Watchlist product | Fan-out of the IMP-020 scan on `research` + Ops mirror. Inherit Research `content_hash`. Do not invent ideas. |
| Gates | Quiet hours, numeric threshold per kind (including `watchlist`), idempotency, rate limit, `--no-send` default. |
| CI | Pytest unsets `TELEGRAM_BOT_TOKEN` and blocks `api.telegram.org`. |

`lab deliver watchlist --fixture --no-send` is the operator path. `lab watchlist scan` remains the Research artifact generator.

## Consequences

- Channel matrix drift from naming is a load-time failure.
- Watchlist Telegram body is an Ops cut of existing scan fields (membership, monitor_state, freshness, PLAYBOOK flags). It is not EDGE_SCAN and not a call.
- FAILED sends escalate to Ops (Coord remains the orchestration channel, not the publisher).
- SCHED-001 (Sydney 08:00 digest) stays OPEN; watchlist schedule is 07:45 Sydney and does not close that incident.

## Not this ADR

6d listings/IPO (IMP-017, parked until 6c-1..6c-5 complete). Live/signing/Redis. Universe promotion. Paid data. Closing OPEN ops incidents.
