# Ops

Desk operating model for Market Memory as a **private research lab**. This tree is documentation and the single improvement queue. It is not live logic, not a fund offering, and not an execution path.

| Path | What it is |
|---|---|
| [desk-charters.md](desk-charters.md) | Desk mandates, forbidden actions, artifacts, pipeline, reporting template, capability map |
| [decision-rights.md](decision-rights.md) | Who proposes / challenges / vetoes / approves; Principal-only gates |
| [improvement-queue.md](improvement-queue.md) | Single continuous-improvement queue; every item has a desk and one accountable owner |
| [plans/](plans/) | IMP implementation plans |
| [reports/source-health/](reports/source-health/) | Standing DQ / source-health reports (`lab data source-health`) |
| [reports/source-evaluation/](reports/source-evaluation/) | Principal source-evaluation research (recommend only; no adapters) |

Hard constraints (same as [AGENTS.md](../AGENTS.md)):

- No trading credentials, signing, wallets, or `hl_trade` / `mm_execution` usage from this tree.
- Do not edit `config/risk/environments/live.yaml` from ops docs work.
- Quant Review Board (IMP-001) is **DONE** (#31). Do not rewrite the board in a Pulse or DQ PR.
- US Market Pulse vertical slice (IMP-002) is **DONE** (#32).
- Standing source-health report (IMP-003) is **DONE** (#33).
- Pulse source hardening (IMP-004) is **DONE** (#34). Read-only; no execution.
- Membership vocabulary (IMP-005) is **DONE** (#35). Keys are `in_universe` / `watch_only`.
- Post-IPO reclaim screen (IMP-006) is **DONE** (#36). Equities desk product; not a trading decision.
- Dedicated crypto / equities thesis-card templates (IMP-007) are **DONE** (#37). Generic `thesis.md` stays the lifecycle spine.
- Quant locked-membership RESEARCH_PRIORITY pass (IMP-008) is **DONE** (#38).
- Phase 5a desk boundaries (IMP-009) is **DONE** (#40). Tiers 0–7; import walls.
- Phase 5b Polygon equities + HL structure (IMP-010) is **DONE** (#41).
- Phase 5c quant factor library (IMP-011) is **DONE** (#42).
- Phase 5d desk runners (IMP-012) is **DONE** (#43).
- Phase 5e Telegram delivery (IMP-013) is **DONE** (#44).
- Phase 6a PG LISTEN/NOTIFY mesh (IMP-014) is **DONE** (#45).
- Phase 6b flow/macro/regime (IMP-015) is **DONE** (#46).
- Phase 6c per-desk Telegram + PLAYBOOK + 6c-0 (IMP-016) is **DONE** (#47).
- Phase 6c-1 five-desk roster (IMP-018) is **DONE** (#49).
- Phase 6c-2 naming layer (IMP-019) is **DONE** (#51).
- Phase 6c-4 watchlist monitor (IMP-020) is **DONE** (#52).
- Phase 6c-5 delivery expansion (IMP-021) is **DONE** (#53).
- Phase 6d listings/IPO (IMP-017) is **IN_REVIEW** (this PR).
- Source evaluation 2026-09-18 (IMP-022–IMP-029) is **BACKLOG** docs recommendation. Do not implement adapters in that PR.
- Execution & Fund Ops is **future-only** until the Principal separately activates it.
