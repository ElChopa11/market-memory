# PLAN — IMP-017 Phase 6d listings / IPO

**Report status:** PARKED. Blocked until 6c-1..6c-5 complete per Principal resume-build order 2026-09-19. **Do not implement in the 6c-1 PR.**  
**Owner:** Ops (queue) / Research (listings sleeve when unparked)  
**Scope (when started):** Phase 6d — listings / IPO product on the five-desk roster + 6c PLAYBOOK + Ops-owned Telegram. No live trading. No execution. No `live.yaml`. No Redis.

## Why

Phase 6c-1 cuts the roster to five desks. A listings / IPO product is a separate phase and must not sneak into 6c-1.

## Proposed outcome (later PR)

- Research listings / IPO sleeve that publishes via the existing PG NOTIFY mesh and 6c fan-out (Ops-owned).
- Honest unavailable when a listing feed is missing. Never invent a print. Closed Quant verdicts only.
- PLAYBOOK artifacts inherit Quant math; LLM remains WRITER/CRITIC only under `config/llm/budgets.yaml`.

## Non-goals

Live trading. Signing. `live.yaml`. Redis. Scorecards automation (6e). Strategy decay-watch (6f). Implementing listings in 6c-1.

## Dependencies

IMP-018 (6c-1), IMP-019 (6c-2), IMP-016/6c-3 (#47 DONE), IMP-020 (6c-4), IMP-021 (6c-5) must be DONE.

## Status

PARKED (blocked until 6c-1..6c-5 complete).
