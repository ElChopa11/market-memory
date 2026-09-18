# Telegram delivery (Phase 5e) + per-desk fan-out (Phase 6c)

Coordinator delivery of desk packs over the **Telegram Bot API**, plus Phase 6c per-desk fan-out and Ops mirror. Default is **dry-run** (`--no-send`). Live send is operator-gated. **No live trading. No signing. No execution.** Delivery is **Ops-owned**. Coord/Don is orchestration only.

Architecture: [ADR/0003-telegram-delivery.md](../../ADR/0003-telegram-delivery.md), [ADR/0006-phase6c-playbook-telegram.md](../../ADR/0006-phase6c-playbook-telegram.md). Desk packs: [desks.md](desks.md). PLAYBOOK: [../playbook.md](../playbook.md). Secrets: [security-model.md](../security-model.md).

## What operators can do

```bash
# Dry-run from the Coord pack (writes exact payload under briefs/YYYY-MM-DD/)
uv run lab desk run --all --fixture tests/fixtures/phase5d/frozen_day.json --no-send --out /tmp/desk-run --no-db

uv run lab deliver pack --fixture tests/fixtures/phase5d/frozen_day.json --no-send --out /tmp/desk-run

uv run lab deliver pack --from-markdown tests/fixtures/phase5e/desk-pack.md \
  --as-of 2026-09-18T00:00:00Z --desk ops --no-send --out /tmp/desk-run

# Per-desk fan-out + Ops mirror (same content_hash + footer; never re-rendered)
uv run lab deliver fanout --desk research --from-markdown tests/fixtures/phase5e/desk-pack.md \
  --as-of 2026-09-18T00:00:00Z --no-send

# Manual real send of a one-line ping (bot box only; never in pytest)
# Requires TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in the environment.
uv run lab deliver test --desk ops --i-mean-it --ignore-quiet-hours
```

`--no-send` is the default. Pytest unsets `TELEGRAM_BOT_TOKEN` and refuses connections to `api.telegram.org`.

## Secrets (env only)

| Env | Required | Purpose |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | live send | Bot token. Never git. Never dry-run files. |
| `TELEGRAM_CHAT_ID` | live send | Default chat. |
| `TELEGRAM_CHAT_ID_<DESK>` | optional | Per-desk override (`INTEL`, `RESEARCH`, `QUANT`, `IC_RISK`, `ALERTS`). |

`config/delivery/telegram.yaml` maps desk → **env var name** + optional forum `thread_id`. It must not contain token or chat id values. Copy `.env.example` placeholders only.

## Gates (never alert without a threshold)

Every live POST is refused unless all of these pass:

1. **Numeric threshold** in `config/delivery/telegram.yaml` (`thresholds.require_threshold_config`, `desk_pack.min_completeness_pct`, `alert.min_events`).
2. **Quiet hours** (default 22:00–07:00 Australia/Sydney). `lab deliver test --ignore-quiet-hours` is operator-only.
3. **Idempotency** key `sha256(desk, as_of, content_hash)` — reruns inside `dedupe.ttl_seconds` do not double-post.
4. **Rate limit** `rate_limit.max_requests_per_minute`.
5. Token + chat id present in env (`missing_env` fail-closed; values never printed).
6. **Retry** 429 / 5xx honouring `Retry-After`. Exhausted retries write a `FAILED` delivery row and escalate to Coord — **never silent drop**.

Dry-run still writes the **exact** `sendMessage` chunks that would have been posted.

## Payload files

Under `--out` (or repo root) `briefs/YYYY-MM-DD/`:

| File | Contents |
|---|---|
| `telegram-payload.json` | Canonical envelope (MarkdownV2 chunks, env **names**, idempotency key). No token. |
| `telegram-payload.sha256` | Byte-stable hash of that file. |
| `desk-pack.md` | Coord output contract (from `lab desk run --out`). |

Parse mode is MarkdownV2. Messages longer than 4096 characters are split with ordered `[i/n]` prefixes.

## Inbound (read-only)

`lab deliver inbound "/status"` — allowlist `/status`, `/brief`, `/desk`, `/idea`, `/gaps`, `/halt`. Trading verbs (`/buy`, `/sell`, `/order`, …) are refused. Unknown uid → **silent drop + audit** (no reply). No network, no orders.

## Fan-out (Phase 6c)

`lab deliver fanout --desk <slug>` delivers the desk channel then an Ops mirror of the **same** `content_hash` plus a footer. The body is not re-rendered. Chart PNG caption uses filename `{content_hash}.png`. Publishing slugs (from `mm_common.naming`): `intel` `research` `quant` `ic_risk` `ops`. Telegram header is `{display} · {slug}`. Unknown slug fails closed.

## Import walls

`packages/delivery` must not import `mm_execution`. Research / desks / quant must not grow a signing surface. CI: `scripts/check_import_boundaries.py`.

## Not this phase

- Phase 6d listings / IPO desk (IMP-017, parked).
- `live_trading_enabled: true`, signing, wallet code, order endpoints.
- Paid Telegram SDKs (httpx is enough). Redis.
