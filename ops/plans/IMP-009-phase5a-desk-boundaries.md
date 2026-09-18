# PLAN — IMP-009 Phase 5a desk boundaries

**Report status:** IN_REVIEW  
**Owner:** Don (Chief of Staff / Hive Coordinator)  
**Scope:** docs + CI + skeletons. No Polygon client, no new market-data adapters, no Telegram send, no quant-factor implementations, no execution/signing, no `live.yaml` edits.

## Why

Principal approved Phase 5a–5e (equities default Polygon) as **one phase per PR**. Hive roles and IMP-000 charters do not encode the numbered Tier 0–7 model, import walls, Skeptic FAIL return/archive, or Risk BLOCK as terminal. IMP-008 locked-membership Quant pass is merged (#38).

## Path choice

| Role | Path |
|---|---|
| Tiers / escalation | `AGENTS.md`, `ops/desk-charters.md`, `ops/decision-rights.md` |
| Architecture | `ADR/0002-desk-delivery-architecture.md` (5b–5e named, not built) |
| Runbook | `docs/runbooks/desks.md` (boundaries only) |
| Import walls | `scripts/check_import_boundaries.py` + `.github/workflows/test.yml` |
| Skeletons | `packages/desks`, `packages/quant`, `packages/delivery` |
| Lifecycle | `mm_research_kit.state_machine` + thin `thesis_status_event` |
| Output contract | `templates/output-contract.md` |
| Next slice | IMP-010 READY (Phase 5b) — **not this PR** |

## Non-goals

Polygon / HL new adapters. `packages/quant` factor math. `packages/desks` full runners. Telegram client. Schedules. Secrets. `live.yaml`. Order/signing code. Paid deps. Risk *service*. Simulated execution. Phase 5e delivery.

## Tests

See `tests/unit/test_state_machine.py`, `tests/unit/test_import_boundaries.py`, `tests/unit/test_output_contract.py`, `tests/unit/test_phase5a_desk_boundaries.py`. Integration: `thesis_status_event` exists at head revision `0006_phase5a_status_events`.

## Gates kept

`live_trading_enabled: false`. risk-config-guard. promote-gate. PIT law. Degrade-never-invent. No secrets in git.
