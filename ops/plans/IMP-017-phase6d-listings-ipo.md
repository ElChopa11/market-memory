# PLAN — IMP-017 Phase 6d listings / IPO desk

**Report status:** READY (parked until IMP-016 merges). **Do not implement in the 6c PR.**  
**Owner:** Don / Equities & Post-IPO Desk  
**Scope (when started):** Phase 6d — listings / IPO desk product on top of the 6c PLAYBOOK + Telegram fan-out. No live trading. No execution. No `live.yaml`. No Redis.

## Why

Phase 6c ships per-desk Telegram, the PLAYBOOK ladder, Quant-owned trade math, and token-budget/grounding locks. A listings / IPO desk is a separate product and must not sneak into 6c.

## Proposed outcome (later PR)

- Equities listings / IPO desk runner that publishes via the existing PG NOTIFY mesh and 6c fan-out.
- Honest unavailable when a listing feed is missing. Never invent a print. Closed Quant verdicts only.
- PLAYBOOK artifacts inherit Quant math; LLM remains WRITER/CRITIC only under `config/llm/budgets.yaml`.

## Non-goals

Live trading. Signing. `live.yaml`. Redis. Scorecards automation (6e). Strategy decay-watch (6f). Reopening IMP-016 except queue hygiene. Paid data vendors without Principal ask. Implementing listings in 6c.

## Dependencies

IMP-016 Phase 6c per-desk Telegram + PLAYBOOK + 6c-0 — this item stays READY/PARKED until that PR is `DONE`.

## Status

READY (parked; single-threaded — do not move to `IN_PROGRESS` while IMP-016 is open).
