# market-memory

Private AI-native trading intelligence lab (Hyperliquid-first). Optimised for **auditability, small blast radius, and compounding institutional memory** — not maximum automation.

**Status: Phase 0 foundations.** Repository structure, local Postgres + MinIO, security model, artifact templates, empty packages, lifecycle checker, CI skeleton. **No live trading, no order signing, no wallet code, no market ingest.**

## Start here

| Doc | What it is |
|---|---|
| [docs/founding-brief.md](docs/founding-brief.md) | Operating philosophy, hive roles, lifecycle |
| [docs/security-model.md](docs/security-model.md) | Treasury vs API wallet, env separation, kill switch |
| [docs/research-lifecycle.md](docs/research-lifecycle.md) | Artifact chain and definition-of-done gates |
| [AGENTS.md](AGENTS.md) | Role permissions (Research **cannot** access trading credentials) |
| [ADR/0001-v1-monorepo.md](ADR/0001-v1-monorepo.md) | v1 architecture decision |

Live trading is **hard-gated** (`config/risk/environments/live.yaml` → `live_trading_enabled: false`). Default instruments: **BTC and ETH perps** (config only).

## Boot local dev

Requires Docker Compose and [uv](https://docs.astral.sh/uv/) (Python 3.12).

```bash
# 1. Object store + database of record
docker compose up -d

# Postgres 16 on localhost:5432 (user/password/db: lab / lab / market_memory)
# MinIO on localhost:9000 (API) and :9001 (console); images from quay.io/minio
# Local compose credentials are dev-only conveniences, not production secrets.

# 2. Python workspace
uv sync --all-packages

# 3. Lifecycle DoD gates (templates present; thesis without intent fails)
./scripts/check-lifecycle.sh

# 4. Tests
uv run pytest

# Optional one-shot
./scripts/bootstrap-dev.sh
```

Copy `.env.example` to `.env` only if you need local overrides. **Never put Hyperliquid keys in `.env` or git.**

`lab` CLI is a Phase 0 stub:

```bash
uv run lab
```

## Layout

```text
ADR/              architecture decisions
docs/             founding brief, security, lifecycle, runbooks
templates/        immutable artifact templates
research/         versioned thesis chain (git)
config/           risk / instruments / schedules
packages/         capability stubs (common, memory, ingest, …)
apps/             process stubs (lab-cli, workers, services)
tests/            unit, integration, adversarial (later)
scripts/          bootstrap + lifecycle checker
```

## Phases (not in this PR)

1. Read-only ingest + Market Memory  
2. Research workspace CLI  
3. Market Pulse  
4. Backtest + paper ledger  
5. Deterministic risk + simulated execution  
6. Tiny manually approved live (optional)  
7. Learning loop  

Out of scope for Phase 0: Market Pulse implementation, backtests, Hyperliquid clients, dashboards, Unicorn Hunter logic, live keys.
