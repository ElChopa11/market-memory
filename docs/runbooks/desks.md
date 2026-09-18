# Desk runners (Phase 5d) + Telegram delivery (Phase 5e)

Private research lab control plane. **Desk orchestration on frozen-day fixtures.** Telegram Bot API send is **Phase 5e** (`lab deliver`; default `--no-send`). No live trading.

Canonical names and charters: [ops/desk-charters.md](../../ops/desk-charters.md). Permissions: [AGENTS.md](../../AGENTS.md). Architecture: [ADR/0002-desk-delivery-architecture.md](../../ADR/0002-desk-delivery-architecture.md), [ADR/0003-telegram-delivery.md](../../ADR/0003-telegram-delivery.md). Decision rights: [ops/decision-rights.md](../../ops/decision-rights.md). Telegram runbook: [telegram.md](telegram.md).

## What operators can do

```bash
# Full pipeline, fixture-only, no send (deterministic content hash)
uv run lab desk run --all --fixture tests/fixtures/phase5d/frozen_day.json --no-send --no-db

# One desk
uv run lab desk run --desk intel --fixture tests/fixtures/phase5d/frozen_day.json --no-send --no-db

# Writes dry-run pack + sha256 + no-send payload under briefs/YYYY-MM-DD/
uv run lab desk run --all --fixture tests/fixtures/phase5d/frozen_day.json --no-send --out /tmp/desk-run --no-db
```

`--send` on `lab desk run` is a gated Coord-pack POST (token required; pytest fail-closed). Default remains `--no-send`. `mm_delivery.SEND_ENABLED` stays false so send is never implicit. See [telegram.md](telegram.md).

Same fixture twice → identical `content_hash`.

## Protocol

Each desk implements `run(as_of, ctx) -> DeskOutput`:

| Field | Meaning |
|---|---|
| `status` | `OK` \| `DEGRADED` \| `FAILED` |
| `completeness_pct` | Coverage of expected slots (not conviction) |
| `provenance_ids` | Observation / fixture ids on numbers |
| `artifacts` | Markdown (and no-send payload hash for Coord) |

`as_of` is the knowledge watermark (`as_of_knowledge`, lockstep with `ingested_at`). Never `published_at` / `market_time`.

Pipeline (no skipped gates):

```text
Intel → 3a Crypto | 3b Equities → Quant → Skeptic → Risk → Coord pack
```

Paper / Principal remain human gates. Runners do **not** open paper. Telegram send is a separate Coordinator step (`lab deliver`), default dry-run.

## Desks

| Slug | Tier | Behaviour |
|---|---|---|
| `intel` | 2 | Read-only assemble of ingest/health feeds. Facts only. Missing required feed → `DEGRADED`, never invent. |
| `crypto` | 3a | Crypto tape note from fixture/Memory facts. No HL client. |
| `equities` | 3b | Equity tape note. Polygon client stays in `mm_ingest`. |
| `quant` | 4 | Calls `mm_quant` FactorRegistry + QuantCard. Closed verdict set. Not a call. |
| `skeptic` | 5 | Adversarial checklist. FAIL **return** (`revise` → `in_research`) or FAIL **archive** (`reject` → `rejected`). No self-approve. |
| `risk` | 6 | Deterministic allow/block from `config/risk/*`. Explains `rule_id` + `config_version`. **BLOCK is terminal** without Principal override. No LLM. |
| `coord` | 1 | Calendar stub + pack assembly into [templates/output-contract.md](../../templates/output-contract.md). Prepares payload strings; Telegram send is `lab deliver`. |

## Lifecycle

Transitions use the Phase 5a hook (`actor`, `ts`, `reason`) in `mm_research_kit.state_machine`. Illegal edges fail (`GateError`). Risk BLOCK cannot promote to paper. Author ≠ Skeptic ≠ Risk.

Fixture runs stamp `ts` from `as_of_knowledge` so hashes stay stable.

## Fixtures

| Path | Case |
|---|---|
| `tests/fixtures/phase5d/frozen_day.json` | Happy path, all `OK` |
| `tests/fixtures/phase5d/missing_feed.json` | Intel `DEGRADED` (polygon unavailable) |
| `tests/fixtures/phase5d/skeptic_fail.json` | Skeptic FAIL return |
| `tests/fixtures/phase5d/risk_block.json` | Risk BLOCK (SOL not allowlisted) |

## Import walls (CI)

`scripts/check_import_boundaries.py` (also a job in `.github/workflows/test.yml`):

- `packages/research_kit`, `packages/desks`, `packages/quant`, `packages/delivery` must not import `mm_execution` / `mm_execution_service` or signing / live-trade surfaces.
- Intel `packages/ingest` must not import opine packages: `mm_research_kit`, `mm_desks`, `mm_quant`, `mm_delivery`.

The Intel *desk runner* lives in `mm_desks.intel` and only assembles fixture/health facts. Ingest does not import it.

## Output contract

Principal-facing desk product copy uses [templates/output-contract.md](../../templates/output-contract.md). Trade ideas are **intent-only**. Writer hard rules are on that template.

## Gates kept

`live_trading_enabled: false`. `risk-config-guard`. `promote-gate`. Point-in-time law. Degrade-never-invent. No secrets in git.

## Not this phase

Phase 6a PG NOTIFY bus (IMP-014, parked). New market-data adapters. Live trading, signing, Redis, paid deps. Risk *service* (`apps/risk-service`) stays a stub — `mm_risk.evaluate` is the library used by the Risk desk.

Telegram: [telegram.md](telegram.md). Factor math: [quant-desk.md](quant-desk.md). Polygon + HL structure ingest: [polygon-hl-structure.md](polygon-hl-structure.md).
