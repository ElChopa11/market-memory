# market-memory

Private AI-native trading intelligence lab (Hyperliquid-first). Optimised for **auditability, small blast radius, and compounding institutional memory** — not maximum automation.

**Status: Phase 4 — backtest + paper ledger.** Reproducible fixture replay (`params_hash`), adversarial look-ahead tests, and a shadow paper ledger bound to theses. Phase 1 ingest, Phase 2 thesis workspaces, and Phase 3 Market Pulse remain. **No live trading, no order signing, no wallet code.**

## Start here

| Doc | What it is |
|---|---|
| [docs/founding-brief.md](docs/founding-brief.md) | Operating philosophy, hive roles, lifecycle |
| [docs/security-model.md](docs/security-model.md) | Treasury vs API wallet, env separation, kill switch |
| [docs/research-lifecycle.md](docs/research-lifecycle.md) | Artifact chain and definition-of-done gates |
| [docs/runbooks/ingest.md](docs/runbooks/ingest.md) | Phase 1 how-to: compose, migrate, ingest, query |
| [docs/runbooks/research-workspace.md](docs/runbooks/research-workspace.md) | Phase 2 how-to: create thesis, link evidence, skeptic checklist |
| [docs/runbooks/market-pulse.md](docs/runbooks/market-pulse.md) | Phase 3 how-to: generate pre-open/close briefs, alert-check, DST schedule |
| [docs/runbooks/backtest.md](docs/runbooks/backtest.md) | **Phase 4 how-to:** reproducible fixture backtest |
| [docs/runbooks/paper-trade.md](docs/runbooks/paper-trade.md) | **Phase 4 how-to:** open/close shadow paper trades |
| [AGENTS.md](AGENTS.md) | Role permissions (Research **cannot** access trading credentials) |
| [ADR/0001-v1-monorepo.md](ADR/0001-v1-monorepo.md) | v1 architecture decision |

Live trading is **hard-gated** (`config/risk/environments/live.yaml` → `live_trading_enabled: false`). **Controlled universe is locked** (`config/universe.yaml`, Principal 2026-09-17). Ingest membership stays full: Hyperliquid **BTC, ETH, UNI, AAVE** perps; equities **NVDA, AVGO, SMH, MSFT, META, JPM, XLF, XOM** are a Phase 3 briefing / future equity-feed watchlist, not HL. Survivors are **not equal priority** — **active calls** (thesis priority): BTC, ETH, NVDA, AVGO, MSFT, META, JPM, XLF, XOM; **watch-only** (no active call): UNI, AAVE, SMH (Skeptic PR #14 / call cards PR #13). Must-cuts (HYPE, SOL, XRP, ARB, NEAR, LINK, GLD, LLY) stay archived. Intent-level only — not orders. Ops timezone: **Australia/Sydney**; US session: **America/New_York** (DST via `zoneinfo`); all database timestamps are **UTC `timestamptz`**.

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
# uv run lab ingest --window 7d

# 5. Point-in-time query (as_of_knowledge <= T — never published_at / market_time)
uv run lab what-did-we-know --at 2026-09-10T00:00:00Z

# 6. Thesis workspace from intent
uv run lab thesis new --goal "BTC funding fade after crowding" --owner Research --instrument BTC --no-db

# 7. Frozen-day Market Pulse brief (deterministic content hash)
uv run lab brief preopen --fixture tests/fixtures/briefing/frozen_day.json --no-db
uv run lab brief close --fixture tests/fixtures/briefing/frozen_day.json --no-db
uv run lab brief alert-check --fixture tests/fixtures/briefing/frozen_day.json --no-db

# 8. Reproducible backtest (paper open needs skeptic pass — see docs/runbooks/paper-trade.md)
uv run lab backtest run --fixture tests/fixtures/backtest/clean_bars.json --strategy buy_hold --no-db

# 9. Lifecycle DoD gates + tests
./scripts/check-lifecycle.sh
uv run pytest

# Optional one-shot
./scripts/bootstrap-dev.sh
```

Copy `.env.example` to `.env` only if you need local overrides. **Never put Hyperliquid keys or FRED keys in git.** Phase 3 live macro fetchers read `FRED_API_KEY` from the environment and degrade to `data_quality=partial` when it is missing.

```bash
uv run lab status
uv run briefing-worker next --from 2026-03-06T00:00:00Z --days 5
```

## Layout

```text
ADR/              architecture decisions
docs/             founding brief, security, lifecycle, runbooks
templates/        immutable artifact templates
research/         versioned thesis chain (git)
briefs/           generated Market Pulse markdown (gitignored dated files)
config/           risk / universe / instruments / ingest / schedules / briefing
packages/         common, memory, ingest, provenance, briefing, …
apps/             lab CLI, ingest-worker, briefing-worker, later services
tests/            unit + integration (fixture window + frozen brief day)
scripts/          bootstrap + lifecycle checker
```

## Phases

0. Foundations (merged)
1. Read-only ingest + Market Memory (merged)
2. Research workspace (merged)
3. Market Pulse (merged)
4. Backtest + paper ledger **(this tree)**
5. Deterministic risk + simulated execution
6. Tiny manually approved live (optional)
7. Learning loop

Out of scope for Phase 4: risk/execution services, dashboards, Unicorn Hunter logic, live keys, alert spam without thresholds.
