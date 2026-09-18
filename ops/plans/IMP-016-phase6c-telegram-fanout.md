# PLAN — IMP-016 Phase 6c per-desk Telegram + PLAYBOOK + token budget/grounding

**Report status:** IN_REVIEW (this PR).  
**Owner:** Don / Chief of Staff (Coordinator)  
**Scope:** Phase 6c — per-desk Telegram channels + presentation layer + chart desk + read-only inbound + Hive PLAYBOOK artifact ladder + Quant-owned trade math + Principal addendum 6c-0 (TOKEN BUDGET + GROUNDING, including prompt versioning pulled from 6f). No live trading. No execution. No `live.yaml`. No Redis.

## Why

Phase 5e delivers Telegram as a single Coordinator sink. Phase 6a/6b publish per-desk envelopes on Postgres NOTIFY. Operators lacked a desk→chat_id fan-out, a presentation formatter, a chart desk, and read-only inbound beyond `/status` `/brief` `/desk`.

The Hive PLAYBOOK (artifact ladder + Quant-owned R) applies from 6c onward and is absorbed here — not IMP-015. Addendum 6c-0 is **in this PR**, not deferred to 6f except leftover strategy decay-watch.

## Outcome

- Queue: IMP-015 DONE (#46). This item the implementation thread. IMP-017 Phase 6d parked.
- Config-driven desk → `TELEGRAM_CHAT_ID_<DESK>` (env-only secrets) fan-out of already-built `--no-send` payloads. Coord mirror = same `content_hash` + footer, never re-rendered.
- Presentation layer (`mm_delivery.present`): one formatter (tick, %, $M/$B, z, signed deltas). Unknowns are `?` named in gaps. Max 3 ideas; cut is stated.
- Chart desk: prior H/L, session VWAP+AVWAP, value area, range, gaps computed once. PNG filename = `content_hash`. Stdlib PNG.
- Read-only inbound `/status` `/desk` `/brief` `/idea` `/gaps` `/halt`. Unknown uid → silent drop + audit. Never trading.
- Idempotency `(desk, as_of, content_hash)`. MarkdownV2 escape property test. 4096 N/M chunking. Alert dedupe / rate-limit / quiet hours. Retry 429/5xx honouring `Retry-After`. Exhausted retries write `FAILED` + Coord escalation (never silent drop).
- Hive PLAYBOOK: one run emits `DAILY_BIAS`, `EDGE_SCAN`, `INTEL_PACKET`, `CHART_ARTIFACT`, `OFFICIAL_BRIEF`, `STATE_CARD` sharing `run_id` + `content_hash`. Trade-math mismatch = failed run.
- Quant (`mm_quant.trade_math`) computes R once. Every `p` has provenance; `prior(judgement)` excluded from expectancy/sizing; `n < min_sample` → `size_pct=0`. Vol-targeted sizing; leverage is a ceiling only.
- Drawdown YAML; invalidation lookback; concentration from trailing-corr config; mandatory post-mortem; DQ = completeness ratio (no letter grades).
- **6c-0:** LLM is WRITER/CRITIC only. `config/llm/budgets.yaml` enforced at the client. Exceed per_run → `DEGRADED` templated `budget_exceeded` + ops escalation (never silent truncate). Exceed per_day → disable LLM until Principal reset. Numeric / render / named-entity / no-backfill locks. Versioned `config/prompts/`. Ledger per `run_id`. A no-setup fixture day makes **zero LLM calls**.
- Quiet hours / completeness / dedupe from IMP-013 stay in force.
- Bus remains Postgres NOTIFY. Redis stays forbidden.
- Runbooks + ADR 0006. README Phase 6 in progress (6c). Alembic `0008_phase6c_delivery`.

## Tests

- `tests/unit/test_phase6c_playbook.py` — no-setup zero LLM; double-run hashes; envelope round-trip; math mismatch; prior excluded; budget_exceeded DEGRADED; digit/ticker grounding; FRED gaps; low-completeness no-idea; schema retry; chart PNG filename
- `tests/unit/test_phase6c_present.py` — MarkdownV2 escape property; formatter units; unknowns in gaps; max-3 cut
- `tests/unit/test_phase6c_delivery.py` — coord mirror hash; unknown uid silent drop; inbound read-only; Retry-After; FAILED sink
- `tests/unit/test_phase6c_risk_playbook.py` — n=1 drawdown noop; sleeve half / dry; cluster YAML not hand-named in engine; invalidation; post-mortem block
- `tests/unit/test_phase6c_cli.py` — `lab playbook run --no-send`
- `tests/unit/test_phase6c_queue.py` — IMP-015 DONE, IMP-016 IN_REVIEW, IMP-017 parked

Pytest unsets `TELEGRAM_BOT_TOKEN` and blocks `api.telegram.org`. No live LLM HTTP.

## Gates kept

`live_trading_enabled: false`. risk-config-guard. promote-gate. PIT. degrade-never-invent. No secrets in git. Import walls. Ask before any new network/keys/order dependency.

## Non-goals

Live trading. Signing. `live.yaml`. Redis. Listings/IPO desk (6d). Scorecards automation (6e). Strategy decay-watch remainder (6f). Reopening IMP-015 except queue hygiene. Paid Telegram/LLM SDKs. A live LLM HTTP provider. Implementing the Hive PLAYBOOK in 6b.

## Status

IN_REVIEW (this PR). IMP-015 is DONE (#46). IMP-017 Phase 6d is READY/PARKED — do not implement listings/IPO here.
