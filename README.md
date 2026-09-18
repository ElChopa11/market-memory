# market-memory

Private AI-native trading intelligence lab (Hyperliquid-first). Optimised for **auditability, small blast radius, and compounding institutional memory** — not maximum automation.

**Status: Phase 6 in progress (6e pack scorecards + queue hygiene on the five-desk roster).** Phase 5 is complete (5a–5e, #40–#44). Phase 6a mesh is **IMP-014 DONE** (#45). Phase 6b flow/macro/regime is **IMP-015 DONE** (#46). Phase 6c PLAYBOOK + fan-out is **IMP-016 DONE** (#47). Phase 6c-1 five-desk roster is **IMP-018 DONE** (#49). Phase 6c-2 naming layer is **IMP-019 DONE** (#51). Phase 6c-4 watchlist monitor is **IMP-020 DONE** (#52). Phase 6c-5 Ops-owned delivery is **IMP-021 DONE** (#53). Phase 6d listings / IPO Research screen is **IMP-017 DONE** (#54). **No live trading, no order signing, no wallet code.** IMP-030 is this tree.

## Start here

| Doc | What it is |
|---|---|
| [docs/founding-brief.md](docs/founding-brief.md) | Operating philosophy, hive roles, lifecycle |
| [docs/security-model.md](docs/security-model.md) | Treasury vs API wallet, env separation, kill switch |
| [docs/research-lifecycle.md](docs/research-lifecycle.md) | Artifact chain and definition-of-done gates |
| [docs/runbooks/ingest.md](docs/runbooks/ingest.md) | Phase 1 how-to: compose, migrate, ingest, query |
| [docs/runbooks/research-workspace.md](docs/runbooks/research-workspace.md) | Phase 2 how-to: create thesis, link evidence, skeptic checklist |
| [docs/runbooks/market-pulse.md](docs/runbooks/market-pulse.md) | Market Pulse: US pre-market (`briefs/YYYY-MM-DD/us-pre-market.md`), close, alert-check, DST |
| [docs/runbooks/source-health.md](docs/runbooks/source-health.md) | Standing DQ / source-health report (`ops/reports/source-health/YYYY-MM-DD.md`) |
| [docs/runbooks/post-ipo-reclaim.md](docs/runbooks/post-ipo-reclaim.md) | Equities Post-IPO / reclaim screen (`research/screens/post-ipo-reclaim/YYYY-MM-DD.md`) |
| [docs/runbooks/thesis-cards.md](docs/runbooks/thesis-cards.md) | Crypto / Equities thesis cards (`templates/crypto-thesis-card.md`, `templates/equities-thesis-card.md`) |
| [docs/runbooks/backtest.md](docs/runbooks/backtest.md) | **Phase 4 how-to:** reproducible fixture backtest |
| [docs/runbooks/paper-trade.md](docs/runbooks/paper-trade.md) | **Phase 4 how-to:** open/close shadow paper trades |
| [AGENTS.md](AGENTS.md) | Role permissions (Research **cannot** access trading credentials) |
| [ops/desk-charters.md](ops/desk-charters.md) | Desk operating model (private research lab, not a fund) |
| [ops/decision-rights.md](ops/decision-rights.md) | Propose / challenge / veto / approve — Principal-only gates |
| [ops/improvement-queue.md](ops/improvement-queue.md) | Single desk-owned improvement queue (Don / Chief of Staff) |
| [docs/runbooks/desks.md](docs/runbooks/desks.md) | **Phase 5d + 6a/6b/6c + 6c-5 + 6d + 6e:** desk runners + PG NOTIFY mesh + PLAYBOOK + watchlist + Ops delivery + listings screen + pack scorecards (`lab desk run`, `lab mesh dry`, `lab playbook run`, `lab watchlist scan`, `lab listings scan`, `lab scorecard compare`, `lab queue check`, `lab deliver watchlist\|listings\|scorecard`) |
| [docs/runbooks/flow-desk.md](docs/runbooks/flow-desk.md) | **Phase 6b:** flow / liquidity (`mm_flow`; verdict OK\|THIN\|UNTRADEABLE_AT_SIZE) |
| [docs/runbooks/macro-desk.md](docs/runbooks/macro-desk.md) | **Phase 6b:** macro regime + EVENT_RISK (`mm_macro`; envelope `regime` tag) |
| [docs/runbooks/telegram.md](docs/runbooks/telegram.md) | **Phase 5e + 6c + 6c-5 + 6d + 6e:** Ops-owned Telegram delivery + per-desk fan-out + watchlist/listings/scorecard cuts (`lab deliver pack\|fanout\|watchlist\|listings\|scorecard --no-send`) |
| [docs/runbooks/llm-budget.md](docs/runbooks/llm-budget.md) | **Phase 6c-0:** LLM WRITER/CRITIC only; hard token budgets; grounding locks |
| [docs/playbook.md](docs/playbook.md) | **Phase 6c:** Hive PLAYBOOK artifact ladder + Quant-owned trade math |
| [docs/runbooks/watchlist.md](docs/runbooks/watchlist.md) | **Phase 6c-4:** locked-universe watchlist monitor (`lab watchlist scan`) |
| [docs/runbooks/listings.md](docs/runbooks/listings.md) | **Phase 6d:** listings / IPO Research screen (`lab listings scan`) |
| [docs/runbooks/scorecards.md](docs/runbooks/scorecards.md) | **Phase 6e:** like-for-like pack scorecards + queue hygiene (`lab scorecard compare`, `lab queue check`) |
| [docs/runbooks/polygon-hl-structure.md](docs/runbooks/polygon-hl-structure.md) | **Phase 5b:** Polygon equities + HL structure ingest (fixture dry-run without keys) |
| [docs/runbooks/quant-desk.md](docs/runbooks/quant-desk.md) | **Phase 5c:** Quant factor library (`mm_quant`; fixture-backed, not a call) |
| [ADR/0001-v1-monorepo.md](ADR/0001-v1-monorepo.md) | v1 architecture decision |
| [ADR/0002-desk-delivery-architecture.md](ADR/0002-desk-delivery-architecture.md) | Phase 5 desk/delivery architecture (5a committed; 5b–5e follow-ons) |
| [ADR/0003-telegram-delivery.md](ADR/0003-telegram-delivery.md) | Phase 5e Telegram channel; multi-channel mesh is Phase 6 |
| [ADR/0004-desk-mesh-pg-notify.md](ADR/0004-desk-mesh-pg-notify.md) | Phase 6a desk mesh; bus = Postgres LISTEN/NOTIFY (no Redis) |
| [ADR/0005-flow-macro-regime.md](ADR/0005-flow-macro-regime.md) | Phase 6b flow/liquidity + macro regime tag (no Redis) |
| [ADR/0006-phase6c-playbook-telegram.md](ADR/0006-phase6c-playbook-telegram.md) | Phase 6c PLAYBOOK + per-desk Telegram + deterministic-first LLM |
| [ADR/0007-phase6c1-desk-roster.md](ADR/0007-phase6c1-desk-roster.md) | Phase 6c-1 five-desk roster (11→5) |
| [ADR/0008-phase6c2-naming.md](ADR/0008-phase6c2-naming.md) | Phase 6c-2 naming / display layer |
| [ADR/0009-phase6c4-watchlist.md](ADR/0009-phase6c4-watchlist.md) | Phase 6c-4 watchlist monitor + daily scan |
| [ADR/0010-phase6c5-delivery.md](ADR/0010-phase6c5-delivery.md) | Phase 6c-5 Ops-owned delivery expansion |
| [ADR/0011-phase6d-listings.md](ADR/0011-phase6d-listings.md) | Phase 6d listings / IPO Research screen |
| [ADR/0012-phase6e-scorecards.md](ADR/0012-phase6e-scorecards.md) | Phase 6e pack scorecards + queue hygiene |

Live trading is **hard-gated** (`config/risk/environments/live.yaml` → `live_trading_enabled: false`). **Controlled universe is locked** (`config/universe.yaml`, Principal 2026-09-17). Ingest membership stays full: Hyperliquid **BTC, ETH, UNI, AAVE** perps; equities **NVDA, AVGO, SMH, MSFT, META, JPM, XLF, XOM** are a Phase 3 briefing / future equity-feed watchlist, not HL. Survivors are **not equal priority** — **in-universe membership** (thesis priority; not a Quant verdict): BTC, NVDA, AVGO, MSFT, META, JPM, XOM; **watch-only** (still ingested / still in membership; no thesis-priority): ETH, UNI, AAVE, SMH, XLF (Skeptic PR #14 / call cards PR #13 / FAIL-patch PR #23). Must-cuts (HYPE, SOL, XRP, ARB, NEAR, LINK, GLD, LLY) stay archived. Intent-level only — not orders. Ops timezone: **Australia/Sydney**; US session: **America/New_York** (DST via `zoneinfo`); all database timestamps are **UTC `timestamptz`**.

## Boot local dev (Phase 4)

Requires Docker Compose and [uv](https://docs.astral.sh/uv/) (Python 3.12).

```bash
# 1. Object store + database of record
docker compose up -d

# Postgres 16 on localhost:5432 (user/password/db: lab / lab / market_memory)
# MinIO on localhost:9000 (API) and :9001 (console); images from quay.io/minio
# Local compose credentials are dev-only conveniences, not production secrets.

# 2. Python workspace
uv sync --all-packages

# 3. Market Memory schema
uv run lab migrate

# 4. Ingest a fixture window (offline) or live public HL info
uv run lab ingest --fixture tests/fixtures/hl_window.json --no-objects
# Phase 5b dry-run (no Polygon/FRED keys, no Postgres):
uv run lab ingest --fixture tests/fixtures/phase5b/polygon_ohlcv.json --no-db
# uv run lab ingest --window 7d

# 5. Point-in-time query (as_of_knowledge <= T — never published_at / market_time)
uv run lab what-did-we-know --at 2026-09-10T00:00:00Z

# 6. Thesis workspace from intent (desk card copied for locked crypto/equity names)
uv run lab thesis new --goal "BTC funding fade after crowding" --owner Research --instrument BTC --no-db

# 7. Frozen-day Market Pulse brief (deterministic content hash)
uv run lab brief preopen --fixture tests/fixtures/briefing/frozen_day.json --no-db
uv run lab brief close --fixture tests/fixtures/briefing/frozen_day.json --no-db
uv run lab brief alert-check --fixture tests/fixtures/briefing/frozen_day.json --no-db
# Live public slice (degrades without keys; never invents):
# uv run lab brief preopen --live --no-db

# 8. Reproducible backtest (paper open needs skeptic pass — see docs/runbooks/paper-trade.md)
uv run lab backtest run --fixture tests/fixtures/backtest/clean_bars.json --strategy buy_hold --no-db

# 9. Quant Review Board (read-only; not a call generator)
uv run lab quant-review --fixture tests/fixtures/quant_review/watchlist_snapshot_20260917.yaml --no-db

# 10. Source health / data-quality (read-only; not a market brief)
uv run lab data source-health --no-db
# alias: uv run lab dq report --no-db

# 11. Post-IPO / reclaim screen (read-only Equities triage; not a trading decision)
uv run lab equities reclaim-screen --fixture tests/fixtures/equities/post_ipo_reclaim_snapshot.yaml --no-db

# 12. Lifecycle DoD gates + tests
./scripts/check-lifecycle.sh
uv run pytest

# 13. Desk runners (frozen day; default --no-send)
uv run lab desk run --all --fixture tests/fixtures/phase5d/frozen_day.json --no-send --no-db

# 14. Telegram delivery dry-run (exact payload under briefs/; no live API)
uv run lab deliver pack --fixture tests/fixtures/phase5d/frozen_day.json --no-send --no-db
# Manual real send on the bot box only:
# uv run lab deliver test --desk ops --i-mean-it

# 15. Desk mesh dry-run (PG NOTIFY / in-memory bus; identical content_hash on double run)
uv run lab mesh dry --fixture tests/fixtures/phase5d/frozen_day.json --no-db
uv run lab mesh dry --fixture tests/fixtures/phase5d/frozen_day.json --kill-desk intel --no-db
uv run lab mesh channels
# Phase 6b flow/macro (regime tag on envelopes; same mesh bus)
uv run lab desk run --all --fixture tests/fixtures/phase6b/frozen_day.json --no-send --no-db
uv run lab mesh dry --fixture tests/fixtures/phase6b/frozen_day.json --no-db

# 16. PLAYBOOK ladder (no-setup = zero LLM; default --no-send)
uv run lab playbook run --fixture tests/fixtures/phase6c/no_setup.json --no-send --no-db
uv run lab deliver fanout --desk research --from-markdown tests/fixtures/phase5e/desk-pack.md \
  --as-of 2026-09-18T00:00:00Z --no-send

# 17. Watchlist monitor (locked in_universe ∪ watch_only; not a call)
uv run lab watchlist scan --fixture tests/fixtures/phase6c4/locked_scan.json --no-send --no-db
uv run lab deliver watchlist --fixture tests/fixtures/phase6c4/locked_scan.json --no-send --no-db

# 18. Listings / IPO screen (Research sleeve; not a sixth desk)
uv run lab listings scan --fixture tests/fixtures/phase6d/listing_day.json --no-send --no-db
uv run lab deliver listings --fixture tests/fixtures/phase6d/listing_day.json --no-send --no-db

# 19. Pack scorecards + queue hygiene (Quant sleeve; not a call)
uv run lab scorecard compare --fixture tests/fixtures/phase6e/packs.json --no-send --no-db
uv run lab deliver scorecard --fixture tests/fixtures/phase6e/packs.json --no-send --no-db
uv run lab queue check

# Optional one-shot
./scripts/bootstrap-dev.sh
```

Copy `.env.example` to `.env` only if you need local overrides. **Never put Hyperliquid keys, Polygon keys, FRED keys, or Telegram bot tokens in git.** Phase 5e reads `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` (optional `TELEGRAM_CHAT_ID_<DESK>`) from the environment. Dry-run (`--no-send`) does not need them. See [docs/runbooks/telegram.md](docs/runbooks/telegram.md). Phase 5b Polygon and Phase 3 live macro fetchers read `POLYGON_API_KEY` / `FRED_API_KEY` from the environment (or CI repository secrets) and mark the feed `unavailable` / `error_class=missing_env` when missing. See [docs/runbooks/polygon-hl-structure.md](docs/runbooks/polygon-hl-structure.md) and [docs/runbooks/market-pulse.md](docs/runbooks/market-pulse.md).

```bash
uv run lab status
uv run briefing-worker next --from 2026-03-06T00:00:00Z --days 5
```

## Layout

```text
ADR/              architecture decisions
docs/             founding brief, security, lifecycle, runbooks
ops/              desk charters, decision rights, improvement queue, source-health reports
templates/        immutable artifact templates
research/         versioned thesis chain (git)
briefs/           generated Market Pulse markdown (gitignored dated files)
config/           risk / universe / instruments / ingest / schedules / briefing / quant-review universe / equities screen / quant factors / flow / macro / delivery / playbook / llm / prompts
packages/         common, memory, ingest, provenance, briefing, desks, quant, flow, macro, delivery, listings, …
apps/             lab CLI, ingest-worker, briefing-worker, later services
tests/            unit + integration (fixture window + frozen brief day)
scripts/          bootstrap + lifecycle checker
```

## Phases

0. Foundations (merged)
1. Read-only ingest + Market Memory (merged)
2. Research workspace (merged)
3. Market Pulse (merged)
4. Backtest + paper ledger (merged)
5. **complete** — 5a desk boundaries merged (#40). 5b Polygon equities + HL funding/OI/basis/depth + spot cross-check **merged (IMP-010, #41)**. 5c quant factors **merged (IMP-011, #42)**. 5d desk runners **merged (IMP-012, #43)**. 5e Telegram delivery **merged (IMP-013, #44)**.
6. **in progress (6e)** — pack scorecards + queue hygiene (IMP-030, this tree). 6a mesh **DONE** (#45). 6b flow/macro **DONE** (#46). 6c PLAYBOOK + fan-out **DONE** (#47). 6c-1 roster **DONE** (#49). 6c-2 naming **DONE** (#51). 6c-4 watchlist **DONE** (#52). 6c-5 Ops delivery **DONE** (#53). 6d listings **DONE** (#54). Tiny manually approved live remains later and hard-gated.
7. Learning loop

Out of scope for Phase 6e: Redis, strategy decay-watch remainder (6f), `live.yaml` changes, order/signing code, paid deps, live LLM HTTP provider, risk/execution *services*, dashboards, Unicorn Hunter logic, alert spam without thresholds, LLM as calculator/router, universe promotion, closing OPEN incidents, auto-merge, gate waivers, reopening the five-desk roster.
