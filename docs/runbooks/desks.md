# Desk runners (Phase 5d) + mesh (Phase 6a) + flow/macro (Phase 6b) + PLAYBOOK/Telegram (Phase 6c)

Private research lab control plane. **Desk orchestration on frozen-day fixtures.** Postgres `LISTEN/NOTIFY` mesh is **Phase 6a** (`lab mesh dry`). Flow/liquidity + macro regime are **Phase 6b**. Hive PLAYBOOK + per-desk Telegram fan-out are **Phase 6c** (`lab playbook run`, `lab deliver fanout`; default `--no-send`). No live trading. **No Redis.**

Canonical names and charters: [ops/desk-charters.md](../../ops/desk-charters.md). Permissions: [AGENTS.md](../../AGENTS.md). Architecture: [ADR/0002-desk-delivery-architecture.md](../../ADR/0002-desk-delivery-architecture.md), [ADR/0003-telegram-delivery.md](../../ADR/0003-telegram-delivery.md), [ADR/0004-desk-mesh-pg-notify.md](../../ADR/0004-desk-mesh-pg-notify.md), [ADR/0005-flow-macro-regime.md](../../ADR/0005-flow-macro-regime.md), [ADR/0006-phase6c-playbook-telegram.md](../../ADR/0006-phase6c-playbook-telegram.md). Decision rights: [ops/decision-rights.md](../../ops/decision-rights.md). Telegram runbook: [telegram.md](telegram.md). LLM budget: [llm-budget.md](llm-budget.md). PLAYBOOK: [../playbook.md](../playbook.md). Flow: [flow-desk.md](flow-desk.md). Macro: [macro-desk.md](macro-desk.md).

## What operators can do

```bash
# Full pipeline, fixture-only, no send (deterministic content hash)
uv run lab desk run --all --fixture tests/fixtures/phase5d/frozen_day.json --no-send --no-db

# One desk
uv run lab desk run --desk intel --fixture tests/fixtures/phase5d/frozen_day.json --no-send --no-db

# Writes dry-run pack + sha256 + no-send payload under briefs/YYYY-MM-DD/
uv run lab desk run --all --fixture tests/fixtures/phase5d/frozen_day.json --no-send --out /tmp/desk-run --no-db

# Mesh: publish envelopes + Coord assemble (in-memory bus; --dsn for Postgres LISTEN/NOTIFY)
uv run lab mesh dry --fixture tests/fixtures/phase5d/frozen_day.json --no-db
uv run lab mesh dry --fixture tests/fixtures/phase5d/frozen_day.json --kill-desk intel --no-db
uv run lab mesh channels

# PLAYBOOK ladder (Phase 6c; no-setup = zero LLM)
uv run lab playbook run --fixture tests/fixtures/phase6c/no_setup.json --no-send --no-db
```

`--send` on `lab desk run` is a gated Coord-pack POST (token required; pytest fail-closed). Default remains `--no-send`. `mm_delivery.SEND_ENABLED` stays false so send is never implicit. See [telegram.md](telegram.md).

Same fixture twice → identical `content_hash` (desk run and mesh dry).

## Mesh (Phase 6a)

Principal lock: **bus = Postgres LISTEN/NOTIFY**. Redis is not used.

| Piece | Behaviour |
|---|---|
| Envelope header | `desk`, `as_of` UTC + Sydney, `status`, `n`, `completeness`, `regime` (macro tag when 6b succeeds, else `unset`), `op=paper\|observation`, `universe`, `sources` / `missing` |
| Cadence | `config/desks/cadence.yaml` (default `daily`) |
| `content_hash` | SHA-256 of canonical header+body. ULID `envelope_id` is not hashed. |
| Persist | Market Memory `desk_envelope` + `desk_health` |
| NOTIFY | Lightweight keys only (`id`, `desk`, `as_of`, `content_hash`, `channel`, `status`) |
| Channels | `desk.<slug>.output`, `desk.<slug>.alert`, `coord.assemble`, `dq.event` |
| Coord worker | Subscribe, track health, assemble pack from Memory |
| Missing desk | Assemble anyway: that desk `FAILED` + `error_class` (`desk_killed` / `desk_missing`) |

`--no-db` uses an in-memory bus with the same channel names. Pass `--dsn` (or `POSTGRES_DSN`) after `lab migrate` to exercise real NOTIFY.

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
Intel → 3a Crypto | 3b Equities → flow → macro → Quant → Skeptic → Risk → Coord pack
```

Paper / Principal remain human gates. Runners do **not** open paper. Telegram send is a separate Coordinator step (`lab deliver`), default dry-run.

## Desks

| Slug | Tier | Behaviour |
|---|---|---|
| `intel` | 2 | Read-only assemble of ingest/health feeds. Facts only. Missing required feed → `DEGRADED`, never invent. |
| `crypto` | 3a | Crypto tape note from fixture/Memory facts. No HL client. |
| `equities` | 3b | Equity tape note. Polygon client stays in `mm_ingest`. |
| `flow` | flow | Liquidity metrics from existing HL + equity tape. Verdict `OK\|THIN\|UNTRADEABLE_AT_SIZE`. Not an order. |
| `macro` | macro | Cross-asset regime tag (VIX+DXY YAML) + EVENT_RISK. Missing feeds → `DEGRADED`. |
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
| `tests/fixtures/phase5d/frozen_day.json` | Happy path, all `OK` (includes 6b flow/macro extras) |
| `tests/fixtures/phase5d/missing_feed.json` | Intel `DEGRADED` (polygon unavailable) |
| `tests/fixtures/phase5d/skeptic_fail.json` | Skeptic FAIL return |
| `tests/fixtures/phase5d/risk_block.json` | Risk BLOCK (SOL not allowlisted) |
| `tests/fixtures/phase6b/frozen_day.json` | 6b happy path: regime tag + liquidity OK |
| `tests/fixtures/phase6b/event_risk.json` | EVENT_RISK haircut |
| `tests/fixtures/phase6b/untradeable.json` | UNTRADEABLE_AT_SIZE auto-block |
| `tests/fixtures/phase6b/missing_feeds.json` | flow/macro DEGRADED, never invent |
| `tests/fixtures/phase6b/lookahead_trap.json` | Adversarial PIT |

## Import walls (CI)

`scripts/check_import_boundaries.py` (also a job in `.github/workflows/test.yml`):

- `packages/research_kit`, `packages/desks`, `packages/quant`, `packages/delivery`, `packages/flow`, `packages/macro` must not import `mm_execution` / `mm_execution_service` or signing / live-trade surfaces.
- Intel `packages/ingest` must not import opine packages: `mm_research_kit`, `mm_desks`, `mm_quant`, `mm_delivery`, `mm_flow`, `mm_macro`.

The Intel *desk runner* lives in `mm_desks.intel` and only assembles fixture/health facts. Ingest does not import it.

## Output contract

Principal-facing desk product copy uses [templates/output-contract.md](../../templates/output-contract.md). Trade ideas are **intent-only**. Writer hard rules are on that template.

## PLAYBOOK (Phase 6c)

`lab playbook run --fixture PATH --no-send` emits `DAILY_BIAS`, `EDGE_SCAN`, `INTEL_PACKET`, `CHART_ARTIFACT`, `OFFICIAL_BRIEF`, `STATE_CARD` sharing `run_id` + `content_hash`. Quant computes R once (`mm_quant.trade_math`); mismatch is a failed run. LLM is WRITER/CRITIC only — a no-setup fixture makes zero LLM calls. See [../playbook.md](../playbook.md) and [llm-budget.md](llm-budget.md).

## Gates kept

`live_trading_enabled: false`. `risk-config-guard`. `promote-gate`. Point-in-time law. Degrade-never-invent. No secrets in git.

## Not this phase

Listings/IPO desk (IMP-017 / 6d, parked). Scorecards automation (6e). Strategy decay-watch remainder (6f). Live trading, signing, Redis, paid deps, live LLM HTTP. Risk *service* (`apps/risk-service`) stays a stub — `mm_risk.evaluate` is the library used by the Risk desk.

Telegram: [telegram.md](telegram.md). LLM budget: [llm-budget.md](llm-budget.md). PLAYBOOK: [../playbook.md](../playbook.md). Factor math: [quant-desk.md](quant-desk.md). Flow: [flow-desk.md](flow-desk.md). Macro: [macro-desk.md](macro-desk.md). Polygon + HL structure ingest: [polygon-hl-structure.md](polygon-hl-structure.md).
