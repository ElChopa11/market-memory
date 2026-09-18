# mm-delivery

Phase 5e **Telegram Bot API** delivery for desk packs, plus Phase 6c per-desk fan-out and Phase 6c-5 Ops-owned expansion (watchlist / listings / scorecard products + naming-bound channel matrix). Dry-run (`--no-send`) is default. `SEND_ENABLED` stays false so send is never implicit. **Publisher is Ops.** Coord orchestrates and does not publish.

**Must not:** import `mm_execution`; hold tokens in git; alert without a numeric threshold; hit live Telegram from pytest; re-render an Ops mirror (same `content_hash` + footer only); invent watchlist ideas or like-for-like scores.

See [../../docs/runbooks/telegram.md](../../docs/runbooks/telegram.md), [../../ADR/0003-telegram-delivery.md](../../ADR/0003-telegram-delivery.md), [../../ADR/0006-phase6c-playbook-telegram.md](../../ADR/0006-phase6c-playbook-telegram.md), and [../../ADR/0010-phase6c5-delivery.md](../../ADR/0010-phase6c5-delivery.md).
