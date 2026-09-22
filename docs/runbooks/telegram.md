# Telegram delivery (Phase 5e + 6c fan-out + 6c-5 Ops expansion + 6d listings)

**Ops-owned** delivery of desk packs over the **Telegram Bot API**, plus Phase 6c per-desk fan-out and Ops mirror. Coord/Don is orchestration only — **Coord is not the publisher**. Default is **dry-run** (`--no-send`). Live send is operator-gated. **No live trading. No signing. No execution.**

## Hybrid clock (Principal 2026-09-19)

Hive is a **clock** (routines / schedules). The `lab` CLI is the **sole Telegram publisher**. Hive group / desk pack `--send` without `--to-principal-dm` is **SEND_FROZEN**. `--i-mean-it` **does not lift that freeze**. Without `--to-principal-dm`, any `--send` / `--i-mean-it` still prints `SEND_FROZEN` and does not POST. The freeze is a **code constant/path** (`GROUP_SEND_FROZEN` / `group_live and not to_dm`), not YAML yet — per-channel `send_enabled` is IMP-050 BACKLOG.

Live POST is DM-only (test ping or pack / `--from-markdown`):

```bash
uv run lab deliver test --to-principal-dm --i-mean-it --ignore-quiet-hours
uv run lab deliver pack --from-markdown PATH --as-of UTC --to-principal-dm --i-mean-it --ignore-quiet-hours
```

Those commands POST only to env `TELEGRAM_CHAT_ID_PRINCIPAL_DM`. Missing that env → refuse. Never silently fall back to `TELEGRAM_CHAT_ID` (group). Preflight still runs. `--routine-id` still stamps a completion row. **Live acceptance is on-box only** (cloud VM has no delivery token). Pytest mocks Telegram HTTP and is not acceptance.

Every Hive fire must stamp a completion row (`lab brief` / `lab deliver` / `lab schedule heartbeat`) under `ops/reports/scheduler/completions/` so `lab schedule miss-check` can see the executed path. See [scheduler.md](scheduler.md). Do not change the miss detector.

| Rule | Detail |
|---|---|
| Token location | Delivery-only file `/home/box/agent-data/delivery/telegram.env` (mode 0600) or `MM_DELIVERY_ENV_FILE`. Loaded into the CLI process only. |
| Not on Secrets card | `TELEGRAM_BOT_TOKEN` must **not** live on the Grok Secrets card. `secret-request` / secure-input wrote it onto the shared multi-agent card (known leak). Rotate if that path was used. Agents must not get the token via default env. |
| Group route | `TELEGRAM_CHAT_ID` = Hive **plain group** (not a supergroup). Required for desk publish. Preflight `getChat`s this id and fails loudly if it does not resolve or if the id drifted to a `-100...` form. |
| Principal DM | `TELEGRAM_CHAT_ID_PRINCIPAL_DM` required for `lab deliver pack|test --to-principal-dm --i-mean-it`. **Never** a silent fallback when the group id is missing. |
| Per-desk routes | `TELEGRAM_CHAT_ID_<DESK>` / `message_thread_id` are **NOT CONFIGURED** (expected-absent). Hive has no forum topics. Preflight prints `NOT CONFIGURED` and does **not** fail. Principal will later choose forum topics (id change) or separate groups — not needed before step 5. |
| Preflight | `lab env preflight` prints **full** FOUND / MISSING / NOT CONFIGURED / DOWN SERVICE / absent state for Telegram, FRED, Polygon, Postgres, and object store. `MISSING` (required absent) → exit non-zero. `NOT CONFIGURED` (per-desk routes today) does **not** fail. Group `TELEGRAM_CHAT_ID` is required. |
| Shared box | File-path readability is a **soft** boundary. Hard fix (delivery binary under a separate user or own container) is queued — do not build it here. |

```bash
uv run lab env preflight
uv run lab deliver test --desk ops --no-send --out /tmp/desk-run
```

`--no-send` writes the exact payload under `briefs/` for inspection. Pytest unsets `TELEGRAM_BOT_TOKEN` and refuses connections to `api.telegram.org`.

Architecture: [ADR/0003-telegram-delivery.md](../../ADR/0003-telegram-delivery.md), [ADR/0006-phase6c-playbook-telegram.md](../../ADR/0006-phase6c-playbook-telegram.md), [ADR/0010-phase6c5-delivery.md](../../ADR/0010-phase6c5-delivery.md), [ADR/0011-phase6d-listings.md](../../ADR/0011-phase6d-listings.md). Desk packs: [desks.md](desks.md). Watchlist: [watchlist.md](watchlist.md). Listings: [listings.md](listings.md). PLAYBOOK: [../playbook.md](../playbook.md). Secrets: [security-model.md](../security-model.md). Naming: [`config/desks/naming.yaml`](../../config/desks/naming.yaml).

## What operators can do

```bash
# Dry-run from the Ops pack (writes exact payload under briefs/YYYY-MM-DD/)
uv run lab desk run --all --fixture tests/fixtures/phase5d/frozen_day.json --no-send --out /tmp/desk-run --no-db

uv run lab deliver pack --fixture tests/fixtures/phase5d/frozen_day.json --no-send --out /tmp/desk-run

uv run lab deliver pack --from-markdown tests/fixtures/phase5e/desk-pack.md \
  --as-of 2026-09-18T00:00:00Z --desk ops --no-send --out /tmp/desk-run

# Per-desk fan-out + Ops mirror (same content_hash + footer; never re-rendered)
uv run lab deliver fanout --desk research --from-markdown tests/fixtures/phase5e/desk-pack.md \
  --as-of 2026-09-18T00:00:00Z --no-send

# Watchlist monitor → Ops Telegram cut (IMP-020 artifact; inherit content_hash)
uv run lab deliver watchlist --fixture tests/fixtures/phase6c4/locked_scan.json --no-send --out /tmp/watchlist

# Listings / IPO screen → Ops Telegram cut (IMP-017 artifact; inherit content_hash)
uv run lab deliver listings --fixture tests/fixtures/phase6d/listing_day.json --no-send --out /tmp/listings

# Manual real send of a one-line ping — DM-only (group stays SEND_FROZEN).
# On-box only. Requires TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID_PRINCIPAL_DM.
# Never posts to TELEGRAM_CHAT_ID (Hive group).
uv run lab deliver test --to-principal-dm --i-mean-it --ignore-quiet-hours --out /tmp/desk-run

# Pack / brief to Principal DM (same DM route + gates; group stays SEND_FROZEN).
uv run lab deliver pack --from-markdown tests/fixtures/phase5e/desk-pack.md \
  --as-of 2026-09-18T00:00:00Z --desk ops --to-principal-dm --no-send --out /tmp/desk-run
# Live (on-box only): add --i-mean-it (and omit --no-send, or pass --send --i-mean-it).
```

`--no-send` is the default. Pytest unsets `TELEGRAM_BOT_TOKEN` and refuses connections to `api.telegram.org`.

## Secrets (delivery-only file, not the Secrets card)

| Env | Required | Purpose |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | live send / getChat | Bot token. Never git. Never Grok Secrets card. Never dry-run files. |
| `TELEGRAM_CHAT_ID` | desk publish | Hive **group** route. Missing → fail. Never default to Principal DM. |
| `TELEGRAM_CHAT_ID_PRINCIPAL_DM` | DM-only live pack/test | Private Principal DM. Required for `--to-principal-dm`. |
| `TELEGRAM_CHAT_ID_<DESK>` | NOT CONFIGURED | Plain group; no forum topics. Report, do not fail. |

`config/delivery/telegram.yaml` maps desk → **env var name** + optional forum `thread_id`. It must not contain token or chat id values. Copy `.env.example` placeholders only. `owner` / `publisher` are `ops`. Coordinator is `orchestration_only`.

## Channel matrix (naming-bound)

Publishing routes (from `mm_common.naming`): `intel` `research` `quant` `ic_risk` `ops`. Sink: `alerts`. Unknown or retired slug (`coord`, `crypto`, …) **fails closed**. Telegram header is `{display} · {slug}` plus optional sleeve (`watchlist monitor`, `listings / IPO screen`) or PLAYBOOK artifact label.

## Gates (never alert without a threshold)

Every live POST is refused unless all of these pass:

1. **Numeric threshold** in `config/delivery/telegram.yaml` (`thresholds.require_threshold_config`, `desk_pack.min_completeness_pct`, `watchlist.min_completeness_pct`, `listings.min_completeness_pct`, `alert.min_events`).
2. **Quiet hours** (default 22:00–07:00 Australia/Sydney). `lab deliver test --ignore-quiet-hours` is operator-only.
3. **Idempotency** key `sha256(desk, as_of, content_hash)` — reruns inside `dedupe.ttl_seconds` do not double-post.
4. **Rate limit** `rate_limit.max_requests_per_minute`.
5. Token + chat id present in env (`missing_env` fail-closed; values never printed).
6. **Retry** 429 / 5xx honouring `Retry-After`. Exhausted retries write a `FAILED` delivery row and escalate to **Ops** — **never silent drop**. Coord does not publish the failure.

Dry-run still writes the **exact** `sendMessage` chunks that would have been posted.

## Payload files

Under `--out` (or repo root) `briefs/YYYY-MM-DD/`:

| File | Contents |
|---|---|
| `telegram-payload.json` | Canonical envelope (MarkdownV2 chunks, env **names**, idempotency key). No token. |
| `telegram-payload.sha256` | Byte-stable hash of that file. |
| `desk-pack.md` | Ops output contract (from `lab desk run --out`). |

Parse mode is MarkdownV2. Messages longer than 4096 characters are split with ordered `[i/n]` prefixes.

## Inbound (read-only)

`lab deliver inbound "/status"` — allowlist `/status`, `/brief`, `/desk`, `/idea`, `/gaps`, `/halt`. Trading verbs (`/buy`, `/sell`, `/order`, …) are refused. Unknown uid → **silent drop + audit** (no reply). No network, no orders.

## Fan-out (Phase 6c + 6c-5)

`lab deliver fanout --desk <slug>` delivers the desk channel then an Ops mirror of the **same** `content_hash` plus a footer. The body is not re-rendered. Chart PNG caption uses filename `{content_hash}.png`.

`lab deliver watchlist` presents the IMP-020 Research scan (membership, monitor_state, freshness, PLAYBOOK flags only — **no invented ideas**) and fans it to `research` with an Ops mirror, inheriting the scan `content_hash`. Watchlist schedule in yaml is 07:45 Sydney; it does **not** close SCHED-001 (Sydney 08:00 digest).

`lab deliver listings` presents the IMP-017 Research listings screen (deals, closed Quant verdicts, inherited trade math, index events — **no invented prints**) and fans it to `research` with an Ops mirror, inheriting the scan `content_hash`. Listings schedule is 07:50 Sydney; it also does **not** close SCHED-001.

`lab deliver scorecard` presents the IMP-030 Quant pack scorecard (like-for-like only; BRIEF-TAG 90m vs 30m stays `NOT_COMPARABLE`) and fans it to `quant` with an Ops mirror, inheriting the scorecard `content_hash`. Scorecard schedule is 07:55 Sydney; it also does **not** close SCHED-001.

`lab deliver decay` presents the IMP-031 Quant prompt-hash decay watch (pinned SHA-256; mismatch is a NOTIFY/queue signal, not a gate waiver) and fans it to `quant` with an Ops mirror, inheriting the watch `content_hash`. Decay schedule is 08:05 Sydney; it also does **not** close SCHED-001.

## B1 Stage 2 PREP — Actions second bot → Principal DM (do not run yet)

**Do not run until Principal approves.** Draft workflow only: see [scheduler.md](scheduler.md) § B1 Stage 2 PREP and `.github/workflows/hybrid-sydney-morning.yml` job `stage2-principal-dm-pack`.

| Item | Detail |
|---|---|
| Gate | `workflow_dispatch` input `i_mean_it_stage2` default **false** |
| CLI | `lab deliver pack --to-principal-dm --i-mean-it --no-db` (fixture markdown canary; never group `--send`) |
| Actions secrets (names only) | `TELEGRAM_BOT_TOKEN` (second bot), `TELEGRAM_CHAT_ID_PRINCIPAL_DM` |
| Must stay UNSET | `TELEGRAM_CHAT_ID` (Hive group) — GROUP SEND_FROZEN |
| Blast radius | Actions second bot ≠ box `/home/box/agent-data/delivery/telegram.env` |
| Before first send | Principal must `/start` the second bot in DM |

## Import walls

`packages/delivery` must not import `mm_execution`. Research / desks / quant must not grow a signing surface. CI: `scripts/check_import_boundaries.py`.

## Not this phase

- `live_trading_enabled: true`, signing, wallet code, order endpoints.
- Paid Telegram SDKs (httpx is enough). Redis.
- Closing OPEN incidents (SCHED-001, BRIEF-TAG, SRC-STOOQ-404, SRC-FRED-MISSING-ENV).
- Auto-merge or gate waiver via the queue helper.
