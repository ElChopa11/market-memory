# market-memory

Private AI-native trading intelligence lab (Hyperliquid-first). Optimised for **auditability, small blast radius, and compounding institutional memory** — not maximum automation.

**Status: Phase 5 in progress (5d desk runners).** Phase 4 backtest + paper ledger remain. 5a desk boundaries merged (#40). 5b Polygon equities + HL structure merged (#41). 5c quant factor library merged (#42). **No live trading, no order signing, no wallet code, no Telegram send.** 5e (Telegram) is queued as IMP-013, not this tree.

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
| [docs/runbooks/desks.md](docs/runbooks/desks.md) | **Phase 5d:** desk runners (`lab desk run --all --fixture --no-send`) |
| [docs/runbooks/polygon-hl-structure.md](docs/runbooks/polygon-hl-structure.md) | **Phase 5b:** Polygon equities + HL structure ingest (fixture dry-run without keys) |
| [docs/runbooks/quant-desk.md](docs/runbooks/quant-desk.md) | **Phase 5c:** Quant factor library (`mm_quant`; fixture-backed, not a call) |
| [ADR/0001-v1-monorepo.md](ADR/0001-v1-monorepo.md) | v1 architecture decision |
| [ADR/0002-desk-delivery-architecture.md](ADR/0002-desk-delivery-architecture.md) | Phase 5 desk/delivery architecture (5a committed; 5b–5e follow-ons) |

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

# 13. Desk runners (frozen day; no Telegram send)
uv run lab desk run --all --fixture tests/fixtures/phase5d/frozen_day.json --no-send --no-db

# Optional one-shot
./scripts/bootstrap-dev.sh
```

Copy `.env.example` to `.env` only if you need local overrides. **Never put Hyperliquid keys, Polygon keys, or FRED keys in git.** Phase 5b Polygon and Phase 3 live macro fetchers read `POLYGON_API_KEY` / `FRED_API_KEY` from the environment (or CI repository secrets) and mark the feed `unavailable` / `error_class=missing_env` when missing. See [docs/runbooks/polygon-hl-structure.md](docs/runbooks/polygon-hl-structure.md) and [docs/runbooks/market-pulse.md](docs/runbooks/market-pulse.md).

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
config/           risk / universe / instruments / ingest / schedules / briefing / quant-review universe / equities screen / quant factors
packages/         common, memory, ingest, provenance, briefing, desks, quant, delivery, …
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
5. **in progress** — 5a desk boundaries merged (#40). 5b Polygon equities + HL funding/OI/basis/depth + spot cross-check **merged (IMP-010, #41)**. 5c quant factors **merged (IMP-011, #42)**. **5d desk runners (IMP-012, this tree).** 5e delivery (Telegram/schedules) deferred as IMP-013. Risk *service* / simulated execution are **not** 5d.
6. Tiny manually approved live (optional)
7. Learning loop

Out of scope for Phase 5d: Telegram client/send, schedules, `live.yaml` changes, order/signing code, paid deps, new market-data adapters, Redis, risk/execution *services*, dashboards, Unicorn Hunter logic, alert spam without thresholds, LLM at decision time, Phase 6 bus.
