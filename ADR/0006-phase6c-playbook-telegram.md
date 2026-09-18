# ADR 0006 — Deterministic-first PLAYBOOK + per-desk Telegram (Phase 6c)

- **Status:** Accepted (Phase 6c / IMP-016, including Principal addendum 6c-0 TOKEN BUDGET + GROUNDING).
- **Date:** 2026-09-18
- **Deciders:** Principal (Phase 6a–6f locked; **bus = Postgres LISTEN/NOTIFY, no Redis**; LLM is WRITER/CRITIC only)
- **Phase:** 6c per-desk Telegram fan-out + presentation + chart desk + inbound + Hive PLAYBOOK artifact ladder + Quant-owned trade math + token budgets + grounding locks. No live trading. No signing. No Redis. No 6d listings.

## Context

Phase 5e delivers Telegram as a single Coordinator sink. Phase 6a/6b publish per-desk envelopes on Postgres NOTIFY. Operators still lacked a desk→chat_id fan-out, a presentation formatter, a chart desk, and read-only inbound beyond `/status` `/brief` `/desk`.

Separately, the Hive PLAYBOOK (artifact ladder + Quant-owned R / expectancy / sizing) applies from 6c onward. Prompt versioning was originally parked in 6f; addendum 6c-0 pulled **token budgets, grounding locks, and versioned prompts** into this PR. Strategy decay-watch stays 6f.

Without this ADR, later slices can sneak live LLM providers, silent context truncation, model-emitted numbers, Redis, listings desks, or scorecard automation into the first PLAYBOOK phase.

## Decision

### Deterministic-first

LLM is **WRITER and CRITIC only**. Never calculator, data source, or router.

| Code-only (zero tokens) | LLM allowed | LLM forbidden |
|---|---|---|
| Indicators, R, expectancy, sizing, base rates, cluster netting, liquidity verdict, regime tag, risk allow/block, routing, formatting, chunking, dedupe, scheduling, scorecards | Skeptic adversarial review; prose of `OFFICIAL_BRIEF` and `EDGE_SCAN`; post-mortem narrative | Any numeric output; any control-flow; risk gating; delivery routing; DQ scoring |

`SCAN_CARD`, `STATE_CARD`, `DAILY_BIAS`, `CHART_ARTIFACT` are templates (zero LLM). A no-setup fixture day **must** run with zero LLM calls. This PR ships **no live LLM HTTP provider** (Ask before any new network/keys). Completers are injected for tests.

### PLAYBOOK ladder

One `lab playbook run` emits `DAILY_BIAS`, `EDGE_SCAN`, `INTEL_PACKET`, `CHART_ARTIFACT`, `OFFICIAL_BRIEF`, `STATE_CARD` sharing `run_id` + `content_hash`. Trade-math mismatch is a **failed run**. Quant (`mm_quant.trade_math`) computes R once; artifacts inherit `trade_math_hash`. `prior(judgement)` is excluded from expectancy and sizing. `n < min_sample` → `size_pct=0`. Vol-targeted sizing; leverage is a ceiling only.

### Telegram + presentation

Extend `mm_delivery`: desk → `TELEGRAM_CHAT_ID_<DESK>` + optional thread; coord mirror of the **same** `content_hash` plus footer (never re-rendered); MarkdownV2 escape; 4096 N/M chunking; alert dedupe / rate-limit / quiet hours; retry 429/5xx honouring `Retry-After`; exhausted retries write `FAILED` + coord escalation (never silent drop). `--no-send` default. Pytest unsets `TELEGRAM_BOT_TOKEN` and blocks `api.telegram.org`. Inbound `/status` `/desk` `/brief` `/idea` `/gaps` `/halt`; unknown uid → silent drop + audit. Never trading.

Chart PNG filename = `content_hash`. Stdlib PNG (no matplotlib, no paid deps).

### Token budgets (enforced at the client)

`config/llm/budgets.yaml`: `per_call_max_input_tokens`, `per_call_max_output_tokens`, `per_run_token_budget`, `per_day_token_budget`, `per_desk_share`.

- Exceed **per_run**: complete with templated output, status `DEGRADED`, `error_class=budget_exceeded`, ops escalation. **Never** silently truncate context and answer.
- Exceed **per_day**: disable LLM until Principal reset (`config/llm/disabled.flag`, gitignored); deterministic desks keep running.

### Grounding (blocking)

- **NUMERIC LOCK:** the model does not emit numbers. Prose uses `{{btc_last}}` / `{{r_target_1}}` substituted by the renderer from provenance-backed rows. A literal digit outside a placeholder is a failed run.
- **RENDER ASSERTION:** every numeric token in the published body resolves to a `provenance_id`; unresolved = failed run, never publish.
- **NAMED-ENTITY LOCK:** instruments / sources / dates in prose must be in the run evidence set.
- **ABSTENTION IS CORRECT:** no-setup / n/a / ? / DEGRADED are successful. Fixture completeness ~30% must yield a gaps-heavy no-idea brief, not a confident one.
- **CLAIM TAGS:** `(observed)` / `(computed)` / `(inference)`. Inference cannot trigger or size.
- **HEARSAY BAN:** news as "source X reported Y at T", never fact.
- **NO BACKFILL FROM MODEL MEMORY:** a missing feed must not be filled from general knowledge. FRED unavailable → no rates figure in the body; rates named in gaps.

Schema fail = retry **once**, then templated fallback + `DEGRADED`. One call per artifact that needs prose — no multi-turn refinement. Temperature is low and fixed in config, recorded on every ledger row.

### Accountability + prompt versioning

Every LLM call logs `prompt_file`, `prompt_hash`, `model`, `model_version`, `temperature`, input/output/cached tokens, latency, cost, `schema_valid`, `retry_count`, `run_id`, `desk_slug`, `artifact_type`. Prompts live under `config/prompts/` as versioned files; changing a prompt is a PR. Weekly ops report shape is stubbed (no live publisher).

### What 6c includes vs defers

| Include in 6c | Defer |
|---|---|
| Per-desk Telegram fan-out + coord mirror | 6d listings / IPO desk |
| Presentation formatter (one module) | 6e scorecards automation |
| Chart desk (stdlib PNG; filename = content_hash) | 6f strategy decay-watch remainder |
| Read-only inbound `/idea` `/gaps` `/halt` + unknown-uid silent drop | Redis, live trading, signing, paid LLM/Telegram SDKs |
| PLAYBOOK ladder + Quant-owned trade math | Risk *service*, execution service |
| Token budgets + grounding + versioned prompts (pulled from 6f) | Live LLM HTTP provider (Ask first) |

## Consequences

- **Positive:** A no-setup day costs zero tokens. Math cannot drift across artifacts. Telegram fan-out cannot re-render. Grounding failures never publish invented numbers or missing-feed backfill.
- **Negative:** Writer prose is placeholder-heavy until the renderer substitutes provenance rows. Completeness below the DQ threshold publishes a no-idea brief even when ideas exist in the fixture.
- **Follow-ups:** IMP-017 / Phase 6d listings-IPO — READY/PARKED.

## Notes

Live trading remains disabled (`live_trading_enabled: false`). Research / desks / quant / delivery / flow / macro must not import `mm_execution`. Do not add Redis. Ask before new network/keys/order deps.
