# LLM budget + grounding (Phase 6c / IMP-016 addendum 6c-0)

Deterministic-first. LLM is **WRITER and CRITIC only** — never calculator, data source, or router. Architecture: [ADR/0006-phase6c-playbook-telegram.md](../../ADR/0006-phase6c-playbook-telegram.md). PLAYBOOK: [playbook.md](playbook.md).

There is **no live LLM HTTP provider** in this phase. Completers are injected in tests. Ask the Principal before adding network, keys, or a vendor SDK.

## What operators can do

```bash
# No-setup fixture: zero LLM calls, templated ladder
uv run lab playbook run --fixture tests/fixtures/phase6c/no_setup.json --no-send --repo-root .

# Ideas fixture still defaults to templates unless a completer is injected (CLI does not call a vendor)
uv run lab playbook run --fixture tests/fixtures/phase6c/ideas.json --no-send --out /tmp/playbook
```

`--no-send` is the default. Pytest never hits a model API.

## Hard budgets (`config/llm/budgets.yaml`)

Enforced at `mm_desks.llm.client.LlmClient` **before** the completer runs. Never silently truncate context and answer.

| Key | Meaning |
|---|---|
| `per_call_max_input_tokens` | Refuse the call if the estimated prompt exceeds this |
| `per_call_max_output_tokens` | Reserved output; refuse if it cannot fit |
| `per_run_token_budget` | Sum of input+output for the playbook `run_id` |
| `per_day_token_budget` | Sum across runs; exhausting it disables LLM |
| `per_desk_share` | Fraction of the per-run budget per desk slug |
| `temperature` | Low + fixed; recorded on every ledger row |
| `max_retries_on_schema` | One retry, then templated fallback |
| `summary_row_cap` | Max computed summary rows in a prompt |
| `disable_flag` | `config/llm/disabled.flag` (gitignored) |

### Exceed per_run

Complete with **templated** output. Status `DEGRADED`. `error_class=budget_exceeded`. Ops escalation to Coord. No idea published from the writer.

### Exceed per_day

Write `config/llm/disabled.flag`. LLM stays off until the **Principal** deletes the flag (reset). Deterministic desks (Intel, flow, macro, Quant math, Risk, chart, templates) keep running.

## Context discipline

- No table dumps, full history, or whole config in prompts.
- Computed summary rows capped at `summary_row_cap`.
- Retrieval scoped by `as_of` **and** instrument **and** cluster.
- Prior desk output enters as **ENVELOPE + numbers only**, never full prose.
- Static prompt prefix is cache-keyed; cache hit rate is on the budget object.
- Structured JSON (`prose` + `claim_tags`) is validated. Free-form only inside the prose block.
- Schema fail → retry once → templated fallback + `DEGRADED`.
- One call per artifact that needs prose. No multi-turn refinement.

## Grounding (blocking)

| Lock | Failure |
|---|---|
| NUMERIC LOCK | Literal digit in LLM output not inside `{{placeholder}}` → failed run |
| RENDER ASSERTION | Numeric token in published body without `provenance_id` → failed run, never publish |
| NAMED-ENTITY LOCK | Instrument / source / date not in the run evidence set → failed run |
| NO BACKFILL | FRED unavailable → no rates figure in the body; `rates` named in gaps (2026-09-18 incident) |
| HEARSAY | News as `source X reported Y at T`, never fact |
| CLAIM TAGS | `(observed)` / `(computed)` / `(inference)`. Inference cannot trigger or size |

**Abstention is correct.** no-setup / n/a / `?` / `DEGRADED` are successful. Low completeness (~30%) must yield a gaps-heavy **no-idea** brief, not a confident one.

Placeholders such as `{{btc_last}}` and `{{r_target_1}}` are substituted by the renderer from provenance-backed rows. The model must not invent the number.

## Ledger

Every call (including budget refusals and schema retries) records: `prompt_file`, `prompt_hash`, `model`, `model_version`, `temperature`, input/output/cached tokens, latency, cost, `schema_valid`, `retry_count`, `run_id`, `desk_slug`, `artifact_type`.

Persisted table: `llm_call` (Alembic `0008_phase6c_delivery`). Weekly ops report **shape** lives in `mm_desks.llm.ledger.weekly_ops_report_shape` (stub publisher — no live send).

## Prompt versioning

Files under [`config/prompts/`](../../config/prompts/). Hash is recorded on every output row. **Changing a prompt is a PR.**

| File | Artifact |
|---|---|
| `official_brief.v1.txt` | `OFFICIAL_BRIEF` writer |
| `edge_scan.v1.txt` | `EDGE_SCAN` writer |
| `skeptic_review.v1.txt` | Skeptic critic (allowed; not a calculator) |
| `post_mortem.v1.txt` | Post-mortem narrative |

`DAILY_BIAS`, `STATE_CARD`, `CHART_ARTIFACT`, `SCAN_CARD`, `INTEL_PACKET` are template-only (`LlmForbidden` if a caller tries).

## Template-only vs writer

A no-setup fixture day **must not** invoke the completer. Ideas with no injected completer stay on templates. CLI `lab playbook run` does not open a vendor client.

## Not this phase

Listings/IPO (6d). Scorecards automation (6e). Strategy decay-watch remainder (6f). Redis. Live/signing. A live LLM HTTP client.
