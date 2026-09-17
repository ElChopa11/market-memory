# Improvement queue

Single continuous-improvement list for Market Memory. The lab runs a **desk model** ([desk-charters.md](desk-charters.md)): every work item belongs to one desk and has **one accountable owner**. Chief of Staff (Don) maintains this file, assigns desks, and enforces **single-threaded implementation** — at most one item in `IN_PROGRESS`. Ready work is parked, not started in parallel.

This queue is the operating system, not an investment book. It does not authorise trades, enable execution, or waive Skeptic / Principal gates ([decision-rights.md](decision-rights.md)).

## Operating rules

1. **Intake** only through this file. Research cards under `research/queue/` are evidence or artifacts, not a second backlog.
2. **One `IN_PROGRESS` implementation item.** Review (`IN_REVIEW`) of docs is allowed while implementation stays parked.
3. **No duplicate research.** If an artifact already answers the question, close or merge the item with a lesson.
4. **Reusable artifacts.** Prefer templates, schema records, and desk products over one-off commentary.
5. Status vocabulary: `BACKLOG` → `READY` → `IN_PROGRESS` → `IN_REVIEW` → `DONE` | `PARKED` | `REJECTED`.

## Required fields (every item)

Each item must include at least: **ID**, **Priority**, **Type**, **Desk**, **Owner**, **Problem**, **Evidence**, **Proposed outcome**, **Definition of done**, **Non-goals**, **Dependencies**, **Risk level**, **Status**, **PR**, **Lesson learned**.

---

## Active / seeded items

### IMP-000 — Desk operating model docs

| Field | Value |
|---|---|
| **ID** | IMP-000 |
| **Priority** | P0 |
| **Type** | Docs / operating system |
| **Desk** | Chief of Staff / Hive Coordinator |
| **Owner** | Don |
| **Problem** | Hive roles exist in AGENTS.md, but desks, decision rights, and a single owner-tagged queue do not. Work can duplicate, skip gates, or read like a fund/trading book. |
| **Evidence** | [AGENTS.md](../AGENTS.md), [docs/founding-brief.md](../docs/founding-brief.md), [docs/research-lifecycle.md](../docs/research-lifecycle.md); no `ops/desk-charters.md` / `ops/decision-rights.md` on `main`; ad-hoc `research/queue/` packs. |
| **Proposed outcome** | Charters, decision-rights table, and this queue live on `main` after Principal-visible review. Pipeline and future-only desks are explicit. |
| **Definition of done** | `ops/desk-charters.md`, `ops/decision-rights.md`, `ops/improvement-queue.md` present; every item has Desk + Owner; capability map + gaps written; pipeline documented; Quant Board **not** implemented; no trading/keys/execution enablement. |
| **Non-goals** | Quant Review Board generator; risk/execution services; live.yaml edits; new ingest; fund ops. |
| **Dependencies** | None (docs on current `main`). |
| **Risk level** | Low (documentation). Process risk if desks ignore the pipeline after merge. |
| **Status** | IN_REVIEW |
| **PR** | https://github.com/ElChopa11/market-memory/pull/28 |
| **Lesson learned** | *(fill at close)* Parked-agent `ops/` on `cursor/ops-scan-proposals-2158` had proposal drafts, not an improvement queue — rebased from `main` rather than that branch. |

### IMP-001 — Quant Review Board

| Field | Value |
|---|---|
| **ID** | IMP-001 |
| **Priority** | P1 |
| **Type** | Process / desk product |
| **Desk** | Quant & Market Structure |
| **Owner** | Don/Quant |
| **Problem** | Opportunity triage is ad-hoc queue packs that use Principal “active call” language. There is no daily Board, no instrument Quant Card, and no closed verdict set. |
| **Evidence** | `research/queue/QUANT-20260917-active-calls.md`; `config/universe.yaml` `active_calls` / `watch_only` (Principal membership, not a Quant verdict); desk charter Quant section. |
| **Proposed outcome** | A Quant Review Board that emits **one verdict + reason code per instrument**: `RESEARCH_PRIORITY` \| `MONITOR` \| `DEFER` \| `REJECT` \| `INSUFFICIENT_DATA`. Forbidden language: “active call,” “make,” “buy,” “sell,” “high confidence.” Relative-value/reclaim candidate unless executable-arb criteria are fully met. |
| **Definition of done** | Board + Quant Card templates; verdict/reason-code vocabulary; arb vs non-arb divergence rule; wired to Data DQ + research cards; still not a trading decision. Separate implementation PR after this docs PR merges. |
| **Non-goals** | **Do not implement in IMP-000.** No order path, no sizing, no live.yaml, no renaming Principal universe fields in the same change as the Board unless Principal asks. |
| **Dependencies** | IMP-000 (charter + language rules). Data freshness for any live-looking inputs. |
| **Risk level** | Medium (language and process can be misread as calls). |
| **Status** | READY (parked; not implementing in this PR) |
| **PR** | — |
| **Lesson learned** | *(fill at close)* Historical packs remain evidence; they are not the Board. |

### IMP-002 — US Market Pulse vertical slice

| Field | Value |
|---|---|
| **ID** | IMP-002 |
| **Priority** | P2 |
| **Type** | Desk product / briefing |
| **Desk** | Macro & Cross-Asset |
| **Owner** | Don |
| **Problem** | Phase 3 Pulse exists as code and runbook, but it is not operated as a Macro desk vertical slice with the reporting template, regime note, and explicit “macro ≠ allocation” cadence. |
| **Evidence** | `packages/briefing`, `docs/runbooks/market-pulse.md`, `config/briefing/*`, `config/schedules/market-pulse.yaml`; charter gap: no standing cross-asset regime note. |
| **Proposed outcome** | One vertical slice: US pre-open/open/close context → Pulse brief + optional regime note; desk report fields only; threshold-gated alerts unchanged. |
| **Definition of done** | Documented desk cadence on top of existing Pulse; regime-note artifact (or explicit deferral); DQ/partial macro quality visible in the report; no new execution or alert-without-threshold path. |
| **Non-goals** | Turning macro into allocation; enabling live FRED as a silent default; dashboard product; Quant Board. |
| **Dependencies** | IMP-000. Benefits from Data DQ reports (not blocking). |
| **Risk level** | Low–medium (partial macro data can be over-read). |
| **Status** | BACKLOG |
| **PR** | — |
| **Lesson learned** | *(fill at close)* |

---

## Status board

| ID | Desk | Owner | Status | Notes |
|---|---|---|---|---|
| IMP-000 | Chief of Staff | Don | IN_REVIEW | [#28](https://github.com/ElChopa11/market-memory/pull/28) |
| IMP-001 | Quant & Market Structure | Don/Quant | READY | Parked; do not start while IMP-000 is the active docs change |
| IMP-002 | Macro & Cross-Asset | Don | BACKLOG | After Board/charter usage is real |

`IN_PROGRESS` count: **0** (IMP-000 is `IN_REVIEW`). Next implementation candidate after IMP-000 closes: IMP-001, still only if Chief of Staff moves it to `IN_PROGRESS`.

---

## Map: existing capabilities → desks

Short form. Full table: [desk-charters.md — capability map](desk-charters.md#capability-map-repo--desk).

| Area | Desk | Owner (accountable) |
|---|---|---|
| Market Memory, ingest, provenance, schemas, PIT | Data & Market Memory | Data desk (unassigned human; Coordinator until named) |
| Crypto thesis / HL structure research | Crypto | Research (Coordinator assigns per card) |
| Equity / post-IPO cards and screens | Equities & Post-IPO | Research (Coordinator assigns per card) |
| US Market Pulse, calendar, macro config | Macro & Cross-Asset | Don (IMP-002) |
| Quant packs / future Board | Quant & Market Structure | Don/Quant (IMP-001) |
| `skeptic-review.md` / `lab skeptic` | Research Review Office | Independent reviewer (not the author) |
| `config/risk/*`, halt, live.yaml guard | Risk & Portfolio Construction | Risk (Principal owns live.yaml) |
| Paper ledger `lab paper` | Principal-gated lab control | Principal enables; Coordinator operates CLI |
| `packages/execution`, `apps/execution-service` | Execution & Trade Operations | **Dormant / future only** |
| Fund ledger, tax, investor reporting | Fund Operations | **Absent / future only** |

## Gaps (not yet queued)

These are identified so they are not silently treated as existing desks. They are **not** `IN_PROGRESS` and are not seeded as IMP items until Chief of Staff intakes them.

| Gap | Desk that would own | Why not queued now |
|---|---|---|
| Standing DQ / source-health report | Data & Market Memory | Charter names the artifact; no generator this cycle |
| Dedicated crypto / equity thesis-card templates | Crypto; Equities | Generic `templates/thesis.md` suffices until Board exists |
| Post-IPO reclaim screen product | Equities & Post-IPO | Needs Quant language rules (IMP-001) first |
| Equity-feed ingest; on-chain ingest | Data | Mandate/paid-data/ToS — Principal gate |
| `risk-review.md` + portfolio exposure report | Risk | Risk *service* is out of Phase 4 |
| Quant Board generator + Quant Cards | Quant | **IMP-001 READY, parked** |
| Cross-asset regime note cadence | Macro | Covered by IMP-002 scope |
| Execution order-state / recon | Execution | Future only; Principal enablement required |
| Fund P&L / investor reporting | Fund Operations | Future only; legal approval required |
| Rename historical “active calls” in universe/queue files | Principal + Quant | Membership language vs Quant vocabulary; not this PR |

## Reconciliation notes

- No `ops/improvement-queue.md` existed on `main` or on parked agent branches.
- `origin/cursor/ops-scan-proposals-2158` has `ops/README.md` plus proposal/draft playbooks. Those are **not** this queue; they were not used as the base. Fresh branch from `main`.
- `research/queue/` remains artifact storage for research packs. It is not an improvement backlog. New implementation work is IMP-* here, then artifacts there if the owning desk produces them.
