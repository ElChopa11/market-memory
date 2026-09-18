# mm-delivery

Phase 5e **Telegram Bot API** delivery for desk packs, plus Phase 6c per-desk fan-out and Coord mirror. Dry-run (`--no-send`) is default. `SEND_ENABLED` stays false so send is never implicit.

**Must not:** import `mm_execution`; hold tokens in git; alert without a numeric threshold; hit live Telegram from pytest; re-render a Coord mirror (same `content_hash` + footer only).

See [../../docs/runbooks/telegram.md](../../docs/runbooks/telegram.md), [../../ADR/0003-telegram-delivery.md](../../ADR/0003-telegram-delivery.md), and [../../ADR/0006-phase6c-playbook-telegram.md](../../ADR/0006-phase6c-playbook-telegram.md).
