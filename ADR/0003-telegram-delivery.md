# ADR 0003 — Telegram delivery (Phase 5e)

- **Status:** Accepted (Phase 5e). Multi-channel mesh is **not** implemented here.
- **Date:** 2026-09-18
- **Deciders:** Principal (Phase 5a–5e approved; this PR is 5e only)
- **Phase:** 5e Telegram Bot API delivery for desk packs. No live trading. No signing.

## Context

Phase 5d (`IMP-012`, #43) produces Coord output-contract packs and `--no-send` payload strings. `mm_delivery.SEND_ENABLED` stayed false. The Principal already has `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` on the bot box for standing briefs.

Without an explicit 5e ADR, later work can fold a Postgres `LISTEN/NOTIFY` bus, Redis, or extra channels into the first send client.

## Decision

**Telegram is the only 5e channel.** Delivery uses the existing httpx stack (`mm_common.http`), not a paid SDK.

- Config: `config/delivery/telegram.yaml` maps desk → `chat_id_env` + optional forum `thread_id`.
- Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, optional `TELEGRAM_CHAT_ID_<DESK>` — env only.
- Default path: `--no-send` writes the exact `sendMessage` envelope under `briefs/YYYY-MM-DD/`.
- Live POST requires explicit `--send` / `lab deliver test --i-mean-it`, numeric thresholds, quiet hours, idempotency TTL, and rate limit.
- `SEND_ENABLED` remains **false** as a module default (send is never implicit).
- Inbound `/status` `/brief` `/desk` are read-only stubs. No trading actions.

**Multi-channel mesh is Phase 6.** Per-desk workers, Postgres `LISTEN/NOTIFY`, Redis, and extra chat products are **IMP-014 / Phase 6a**, parked. Do not implement them in 5e.

## Consequences

- **Positive:** Coord packs from 5d can reach Telegram under the same env names the Principal already uses; pytest cannot hit `api.telegram.org`.
- **Negative:** Operators cron `lab deliver`; there is no bus yet.
- **Follow-ups:** IMP-014 Phase 6a PG NOTIFY mesh — READY/PARKED. Do not fold it into 5e.

## Notes

Live trading remains disabled in `config/risk/environments/live.yaml`. Delivery must not import `mm_execution`. Research / desks must not grow a signing surface.
