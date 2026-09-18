# PLAN — IMP-012 Phase 5d desk runners

**Report status:** IN_REVIEW (this PR).  
**Owner:** Don / Chief of Staff (Coordinator) with Crypto / Equities / Quant / Skeptic / Risk as consumers  
**Scope:** Desk orchestration that calls `mm_quant` + frozen Memory/fixture facts and writes desk artifacts. No Telegram. No execution. No `live.yaml`.

## Why

Phase 5c landed the factor library. Desks still had skeleton packages (`mm_desks`) without runners. Principal lock: one phase per PR.

## Outcome

- Protocol: each desk `run(as_of, ctx) -> DeskOutput` with `OK|DEGRADED|FAILED`, `completeness_pct`, `provenance_ids`, artifacts.
- Intel (read-only assemble from ingest/health fixture), Crypto, Equities, Quant (`mm_quant` factors/cards), Skeptic (FAIL return → `in_research` or FAIL archive → `rejected`), Risk (deterministic allow/block from versioned YAML, no LLM), Coord/Ops (calendar stub + output-contract pack).
- Lifecycle transitions logged (`actor`, `ts`, `reason`) via the Phase 5a hook; illegal transitions rejected.
- CLI: `lab desk run --desk <slug>|--all --fixture <frozen day> --no-send` is deterministic (identical content hash on double run).
- Delivery prepares payload strings only (`SEND_ENABLED = False`).

## Tests

- `tests/unit/test_phase5d_desks.py` — happy, DEGRADED missing feed, Skeptic FAIL, Risk BLOCK, illegal transitions
- `tests/unit/test_phase5d_cli.py` — CLI `--no-send` double-run hash
- `tests/unit/test_phase5d_queue.py`
- `tests/adversarial/test_phase5d_point_in_time.py`
- Import-boundary CI unchanged (desks/research/quant/delivery vs execution; Intel vs opine)

## Gates kept

`live_trading_enabled: false`. risk-config-guard. promote-gate. PIT law (`as_of_knowledge` = knowledge clock). Degrade-never-invent. No secrets in git. No new network/keys/order dependency.

## Non-goals

Telegram / 5e. Signing. `live.yaml`. Paid data. Reopening IMP-011 factor math except queue hygiene. Phase 6 bus. Order endpoints. Redis.

## Status

IN_REVIEW (this PR). IMP-011 is DONE (#42). IMP-013 Phase 5e is READY/PARKED — do not implement Telegram send here.
