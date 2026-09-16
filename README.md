# market-memory

Private AI-native trading intelligence lab (Hyperliquid-first). Optimised for **auditability, small blast radius, and compounding institutional memory** — not maximum automation.

**Status: Phase 1 — read-only ingest + Market Memory.** Postgres schema, Alembic migrations, Hyperliquid public `/info` ingest for BTC and ETH perps, observation provenance, and `what_did_we_know(T)`. **No live trading, no order signing, no wallet code.**

## Start here

| Doc | What it is |
|---|---|
| [docs/founding-brief.md](docs/founding-brief.md) | Operating philosophy, hive roles, lifecycle |
| [docs/security-model.md](docs/security-model.md) | Treasury vs API wallet, env separation, kill switch |
| [docs/research-lifecycle.md](docs/research-lifecycle.md) | Artifact chain and definition-of-done gates |
| [docs/runbooks/ingest.md](docs/runbooks/ingest.md) | **Phase 1 how-to:** compose, migrate, ingest, query |
| [AGENTS.md](AGENTS.md) | Role permissions (Research **cannot** access trading credentials) |
| [ADR/0001-v1-monorepo.md](ADR/0001-v1-monorepo.md) | v1 architecture decision |

Live trading is **hard-gated** (`config/risk/environments/live.yaml` → `live_trading_enabled: false`). Default instruments: **BTC and ETH perps**. Ops timezone: **Australia/Sydney**; all database timestamps are **UTC `timestamptz`**.

## Boot local dev (Phase 1)

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

# 5. Point-in-time query (ingested_at <= T — never published_at alone)
uv run lab what-did-we-know --at 2026-09-10T00:00:00Z

# 6. Lifecycle DoD gates + tests
./scripts/check-lifecycle.sh
uv run pytest

# Optional one-shot
./scripts/bootstrap-dev.sh
```

Copy `.env.example` to `.env` only if you need local overrides. **Never put Hyperliquid keys in `.env` or git.** Phase 1 uses the public info endpoint only.

```bash
uv run lab status
uv run ingest-once --window 7d
```

## Layout

```text
ADR/              architecture decisions
docs/             founding brief, security, lifecycle, runbooks
templates/        immutable artifact templates
research/         versioned thesis chain (git)
config/           risk / instruments / ingest / schedules
packages/         common, memory, ingest, provenance, … (later phases remain stubs)
apps/             lab CLI, ingest-worker, later services
tests/            unit + integration (fixture window replay)
scripts/          bootstrap + lifecycle checker
```

## Phases

0. Foundations (merged)
1. Read-only ingest + Market Memory **(this tree)**
2. Research workspace CLI
3. Market Pulse
4. Backtest + paper ledger
5. Deterministic risk + simulated execution
6. Tiny manually approved live (optional)
7. Learning loop

Out of scope for Phase 1: research workspace UI, Market Pulse, backtests, risk service, execution, dashboards, Unicorn Hunter logic, live keys.
