# ADR 0016 — Unconditional event-class base rates

- **Status:** Accepted
- **Phase:** IMP-039 Phase 1. No live trading. No signing. No Redis. No candidate studies.

## Context

C-001 (supply/demand zone), C-002 (triple RSI MR), and C-003 (second-entry pullback) are Quant HYPOTHESIS cards on the candidate intake shelf (PR #61). Principal lock: nothing is computed on those candidates until unconditional base rates for the event classes they measure against exist in Market Memory.

## Decision

Quant owns three fixture-deterministic event classes and stores a snapshot with provenance:

| Class | Benchmark for |
|---|---|
| `dip_touch` | C-002 |
| `zone_boundary_touch` | C-001 |
| `pullback_ema_touch` | C-003 |

`lab base-rate compute --fixture --no-db` writes `research/quant/base-rates/`. Optional DSN persist uses table `event_base_rate` with `as_of_knowledge = ingested_at`. `base_rate` is a Quant sleeve, not a sixth desk. `n < n_min` → no claim.

## Consequences

- Candidate studies (IMP-040) stay `INTAKE_ONLY` until they can cite `params_hash` + `as_of_knowledge`.
- IMP-034 on main remains ticker/licence (#60). The candidate shelf is a separate intake.
- No sizing, no scan-gate, no Telegram send, no LLM on the fixture path.
