# mm-delivery

Phase 5e **Telegram Bot API** delivery for desk packs. Dry-run (`--no-send`) is default. `SEND_ENABLED` stays false so send is never implicit.

**Must not:** import `mm_execution`; hold tokens in git; alert without a numeric threshold; hit live Telegram from pytest.

See [../../docs/runbooks/telegram.md](../../docs/runbooks/telegram.md) and [../../ADR/0003-telegram-delivery.md](../../ADR/0003-telegram-delivery.md).
