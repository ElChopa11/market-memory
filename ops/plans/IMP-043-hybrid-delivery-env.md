# PLAN — IMP-043 Hybrid Step 2: delivery env-file + env preflight

**Report status:** IN_PROGRESS (this PR).  
**Owner:** Ops  
**Scope:** Delivery-only Telegram env file + full-state preflight. `--no-send` only. No live send. Paper only.

## Why

Hive is a clock. `lab` is the sole Telegram publisher. The bot token must not live on the Grok Secrets card. Preflight must name every declared var/service (found / missing / NOT CONFIGURED / DOWN SERVICE) and fail on required misses. Per-desk routes are expected-absent (plain group). `getChat` must catch a silent `-100...` id change if Hive is converted to a supergroup.

## Outcome

- Load `/home/box/agent-data/delivery/telegram.env` or `MM_DELIVERY_ENV_FILE` into the CLI process (file wins when present; process env for CI).
- `lab env preflight` / `lab brief` / `lab deliver --no-send` print full state. No secret values.
- `TELEGRAM_CHAT_ID` (group) required. Never fall back to `TELEGRAM_CHAT_ID_PRINCIPAL_DM`.
- `TELEGRAM_CHAT_ID_<DESK>` → `NOT CONFIGURED` (does not fail).
- `getChat` verifies the group id when token + group are present (not a sendMessage).
- Object store probe names `DOWN SERVICE (:port refused)` when the endpoint is up in env but TCP refuses.

## Non-goals

Real send (step 5). Forum topics / extra groups (IMP-045). Delivery binary isolation (IMP-044). Hive prompt rewrites. Equity work. Committing token or chat ids.

## Rollback

Revert this PR. Delivery still uses process env only. No live path to unwind.
