# Ops

Desk operating model for Market Memory as a **private research lab**. This tree is documentation and the single improvement queue. It is not live logic, not a fund offering, and not an execution path.

| Path | What it is |
|---|---|
| [desk-charters.md](desk-charters.md) | Desk mandates, forbidden actions, artifacts, pipeline, reporting template, capability map |
| [decision-rights.md](decision-rights.md) | Who proposes / challenges / vetoes / approves; Principal-only gates |
| [improvement-queue.md](improvement-queue.md) | Single continuous-improvement queue; every item has a desk and one accountable owner |
| [plans/](plans/) | IMP implementation plans |
| [reports/source-health/](reports/source-health/) | Standing DQ / source-health reports (`lab data source-health`) |
| [reports/scheduler/](reports/scheduler/) | SCHED-001 root cause + miss-sweep backfill (`lab schedule miss-check`). known-missed baseline: `--baseline-before today` |

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
- Phase 6d listings/IPO (IMP-017) is **DONE** (#54).
- Phase 6e pack scorecards + queue hygiene (IMP-030) is **DONE** (#55).
- Phase 6f decay-watch (IMP-031) is **DONE** (#56).
- Call-card vs Quant SoT (IMP-032) is **DONE** (#57).
- Canonical watchlist monitor.yaml (IMP-033) is **DONE** (#59).
- Ticker resolutions + licence_verdict schema (IMP-034) are **DONE** (#60).
- FRED full-stack (IMP-022) is **DONE** (run_id `fred-fullstack-20260919-101938-aest`). `--no-db` = ELIGIBLE only. SRC-STOOQ-404 stays OPEN. SRC-FRED-MISSING-ENV is CLOSED.
- SEC EDGAR wire (IMP-024) is **DONE** (#63). CBRS/SPCX lockup formulas persist as observations. `--no-db` = ELIGIBLE only.
- Phase 1 unconditional base rates (IMP-040) is **DONE** (#66). Candidate strategy intake (IMP-039 / #61) stays **READY**; card status remains `INTAKE_ONLY`. Expand beyond fixture is L2 P1.
- Desk knowledge base (IMP-041) is **DONE** (#67). Cached prompt prefix. A prior never triggers or sizes.
- Scheduler miss detector (IMP-042) is **DONE** (#68). Heartbeat-on-fire is a log. **SCHED-001 CLOSED** (run_id `actions-b1-35727756341`).
- Hybrid Step 2 delivery env-file + preflight (IMP-043) is **DONE** (#71). `--no-send` only.
- Hybrid Step 4 Hive CLI completion rows (IMP-046) is **DONE** (#72).
- Hybrid Step 5a DM-only live send (IMP-047) is **IN_PROGRESS** (this PR). Hive group / desk pack `--send` stays SEND_FROZEN. `--i-mean-it` alone does not lift the group freeze. Weekly review CLI (IMP-048), Hybrid clock prompt read-back (IMP-049), and per-channel `send_enabled` (IMP-050) are BACKLOG — do not build. Delivery isolation (IMP-044) and per-desk topics vs groups (IMP-045) are BACKLOG — do not build.
- Principal FREE SOURCE PRIORITY 2026-09-19: IMP-022 DONE → IMP-024 DONE → IMP-035 READY → IMP-023 READY → IMP-036–038 BACKLOG.
- Execution & Fund Ops is **future-only** until the Principal separately activates it.
