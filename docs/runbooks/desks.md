# Desk runners (Phase 5d) + mesh (Phase 6a) + flow/macro sleeves (Phase 6b) + five-desk roster (Phase 6c-1) + naming (Phase 6c-2) + watchlist monitor (Phase 6c-4)

Private research lab control plane. **Five publishing desks.** Names are single-sourced in [`config/desks/naming.yaml`](../../config/desks/naming.yaml) and `mm_common.naming`. Postgres `LISTEN/NOTIFY` mesh is **Phase 6a** (`lab mesh dry`). Flow/liquidity + macro regime are Intel sleeves (**Phase 6b**). Hive PLAYBOOK + Ops-owned Telegram fan-out are **Phase 6c** (`lab playbook run`, `lab deliver fanout`; default `--no-send`). Watchlist monitor is **Phase 6c-4** (`lab watchlist scan`; default `--no-send`). No live trading. **No Redis.**

Canonical names and charters: [ops/desk-charters.md](../../ops/desk-charters.md). ADR: [ADR/0009-phase6c4-watchlist.md](../../ADR/0009-phase6c4-watchlist.md), [ADR/0008-phase6c2-naming.md](../../ADR/0008-phase6c2-naming.md), [ADR/0007-phase6c1-desk-roster.md](../../ADR/0007-phase6c1-desk-roster.md). Permissions: [AGENTS.md](../../AGENTS.md). Telegram runbook: [telegram.md](telegram.md). Watchlist: [watchlist.md](watchlist.md).

## 6c-1 cutover (11 → 5)

Principal resume-build order 2026-09-19. Publishing roster is exactly:

| Slug | Desk | Retired sleeves mapped in |
|---|---|---|
| `intel` | Intel (Market Intelligence) | flow, macro, briefing |
| `research` | Research (Investment Research) | crypto, equities, chart, watchlist |
| `quant` | Quant | — |
| `ic_risk` | IC/Risk | skeptic + risk **gates** (not two desks) |
| `ops` | Ops | coord pack + delivery |

Don/Coord is orchestration only (`coord.assemble` is a bus channel, not a desk). `lab desk run --desk crypto|flow|macro|skeptic|risk|coord` is rejected.

Rollback: revert the IMP-018 PR for roster; revert IMP-019 for display names. No live path to unwind.

## Naming (Phase 6c-2)

Do not invent desk titles in artifacts, Telegram headers, mesh envelopes, CLI help, or runbooks. Lookup:

| Machine id | Human label |
|---|---|
| `intel` | Intel (Market Intelligence) |
| `research` | Research (Investment Research) |
| `quant` | Quant |
| `ic_risk` | IC/Risk (Investment Committee & Risk) |
| `ops` | Ops |
| `coord` | Coord (orchestration) — **not a publishing desk** |

PLAYBOOK types (`DAILY_BIAS`, `EDGE_SCAN`, `INTEL_PACKET`, `CHART_ARTIFACT`, `OFFICIAL_BRIEF`, `STATE_CARD`) keep those machine ids; human labels are Daily Bias, Edge Scan, Intel Packet, Chart Artifact, Official Brief, State Card. Unknown slug → fail closed.

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

# Watchlist monitor (Phase 6c-4; locked in_universe ∪ watch_only; not a call)
uv run lab watchlist scan --fixture tests/fixtures/phase6c4/locked_scan.json --no-send --no-db
```

`--send` on `lab desk run` is a gated Ops-pack POST (token required; pytest fail-closed). Default remains `--no-send`. `mm_delivery.SEND_ENABLED` stays false so send is never implicit. See [telegram.md](telegram.md).

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
Intel → Research → Quant → IC/Risk (Skeptic gate then Risk gate) → Ops pack
```

Paper / Principal remain human gates. Runners do **not** open paper. Telegram send is Ops-owned (`lab deliver`), default dry-run.

## Desks

| Slug | Behaviour |
|---|---|
| `intel` | Market Intelligence: ingest/health assemble + flow + macro sleeves. Facts only. Missing required feed → `DEGRADED`, never invent. |
| `research` | Investment Research: crypto + equities tape notes + chart product. Polygon client stays in `mm_ingest`. |
| `quant` | Calls `mm_quant` FactorRegistry + QuantCard. Closed verdict set. Not a call. |
| `ic_risk` | Two gates: Skeptic FAIL **return** / **archive**; Risk allow/block from `config/risk/*`. **BLOCK is terminal**. No LLM. No self-approve. |
| `ops` | Calendar stub + pack assembly. Delivery owner. Coord/Don does not publish. |

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

## Watchlist monitor (Phase 6c-4)

`lab watchlist scan --fixture PATH --no-send` lists every locked `in_universe` ∪ `watch_only` name with membership, monitor_state, freshness, and provenance. `deferred_must_cut` stays archived. PLAYBOOK setups are flagged only — trade math stays on the ladder. See [watchlist.md](watchlist.md).

## Gates kept

`live_trading_enabled: false`. `risk-config-guard`. `promote-gate`. Point-in-time law. Degrade-never-invent. No secrets in git.

## Not this phase

Listings/IPO (IMP-017 / 6d, parked until 6c-1..6c-5). Scorecards automation (6e). Strategy decay-watch remainder (6f). Live trading, signing, Redis, paid deps, live LLM HTTP. 6c-5 delivery expansion. Risk *service* (`apps/risk-service`) stays a stub — `mm_risk.evaluate` is the library used by the IC/Risk Risk gate.

Telegram: [telegram.md](telegram.md). LLM budget: [llm-budget.md](llm-budget.md). PLAYBOOK: [../playbook.md](../playbook.md). Factor math: [quant-desk.md](quant-desk.md). Flow: [flow-desk.md](flow-desk.md). Macro: [macro-desk.md](macro-desk.md). Polygon + HL structure ingest: [polygon-hl-structure.md](polygon-hl-structure.md).
