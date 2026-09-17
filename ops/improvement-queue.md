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
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/28 |
| **Lesson learned** | Merged to `main` (#28). Desk charters, decision rights, and this queue are source of truth. Quant Board was explicitly out of scope and is IMP-001. |

### IMP-001 — Quant Review Board

| Field | Value |
|---|---|
| **ID** | IMP-001 |
| **Priority** | P1 |
| **Type** | Process / desk product |
| **Desk** | Quant & Market Structure Desk |
| **Owner** | Don/Quant |
| **Problem** | Opportunity triage is ad-hoc queue packs that use Principal “active call” language. There is no daily Board, no instrument Quant Card, and no closed verdict set. |
| **Evidence** | `research/queue/QUANT-20260917-active-calls.md`; `config/universe.yaml` `active_calls` / `watch_only` (Principal membership, not a Quant verdict); desk charter Quant section. |
| **Proposed outcome** | A Quant Review Board that emits **one verdict + reason code per instrument**: `RESEARCH_PRIORITY` \| `MONITOR` \| `DEFER` \| `REJECT` \| `INSUFFICIENT_DATA`. Forbidden language: “active call,” “make,” “buy,” “sell,” “high confidence.” Relative-value/reclaim candidate unless executable-arb criteria are fully met. |
| **Definition of done** | `lab quant-review` generator; Board + one Quant Card per reviewed name; closed verdicts `RESEARCH_PRIORITY \| MONITOR \| DEFER \| REJECT \| INSUFFICIENT_DATA` with reason codes; relative-value/reclaim unless Track D executable-arb is complete; language gate (no active call / make / buy / sell / high confidence / sizing); tests + sample board artifact; still not a trading decision. |
| **Non-goals** | No Market Pulse work (IMP-002). No order path, no sizing, no live.yaml, no risk-limit edits, no renaming Principal universe `active_calls` fields unless Principal asks. |
| **Dependencies** | IMP-000 (charter + language rules) — **DONE** (#28). Data freshness for any live-looking inputs. |
| **Risk level** | Medium (language and process can be misread as calls). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/31 |
| **Lesson learned** | Merged to `main` (#31). Board + Quant Cards use a closed verdict set and a language gate. Historical `research/queue/` packs remain evidence; they are not the Board. |

### IMP-002 — US Market Pulse vertical slice

| Field | Value |
|---|---|
| **ID** | IMP-002 |
| **Priority** | P2 |
| **Type** | Desk product / briefing |
| **Desk** | Macro & Cross-Asset Desk |
| **Owner** | Don |
| **Problem** | Phase 3 Pulse exists as code and runbook, but it is not operated as a Macro desk vertical slice with NY/Sydney clocks, DST session status, always-listed cross-asset slots, per-source quality, and an explicit no-decision footer. |
| **Evidence** | `packages/briefing`, `docs/runbooks/market-pulse.md`, `config/briefing/*`, `config/schedules/market-pulse.yaml`; closed PR #29; charter gap: Pulse not yet a standing desk product. |
| **Proposed outcome** | One versioned US pre-market brief from retained Market Memory / approved read-only sources. Dual-write DoD path `briefs/YYYY-MM-DD/us-pre-market.md` plus legacy `preopen.md`. Regime note explicitly deferred. |
| **Definition of done** | Manual `lab brief preopen` produces one versioned US pre-market brief: NY + Sydney generation time; DST-aware US session status; as-of on every market-data section; per-source `fresh\|stale\|partial\|unavailable`; slots always listed (crypto, equity-index proxy, rates, USD, oil, vol); attributable calendar; HL via allowlisted `/info` only; what changed since prior US close from recorded observations when available; informational / no-decision footer; provenance + memory watermark; never invent missing data; tests + committed sample. |
| **Non-goals** | Turning macro into allocation; enabling live FRED as a silent default; dashboard product; Quant Board rewrite; watchlist MAKE/active-call loops; live.yaml / risk-limit edits; execution/signing. |
| **Dependencies** | IMP-000 DONE (#28). IMP-001 DONE (#31) — do not reopen. Benefits from Data DQ reports (not blocking). |
| **Risk level** | Low–medium (partial macro data can be over-read). |
| **Status** | IN_PROGRESS |
| **PR** | https://github.com/ElChopa11/market-memory/pull/32 |
| **Lesson learned** | *(fill at close)* Standing cross-asset regime note is **deferred** (not in this slice). |

---

## Status board

| ID | Desk | Owner | Status | Notes |
|---|---|---|---|---|
| IMP-000 | Chief of Staff / Hive Coordinator | Don | DONE | [#28](https://github.com/ElChopa11/market-memory/pull/28) merged |
| IMP-001 | Quant & Market Structure Desk | Don/Quant | DONE | [#31](https://github.com/ElChopa11/market-memory/pull/31) merged |
| IMP-002 | Macro & Cross-Asset Desk | Don | IN_PROGRESS | [#32](https://github.com/ElChopa11/market-memory/pull/32) — only active implementation |

`IN_PROGRESS` count: **1** (IMP-002 US Market Pulse). IMP-000 and IMP-001 are `DONE`.

---

## Map: existing capabilities → desks

Short form. Full table: [desk-charters.md — capability map](desk-charters.md#capability-map-repo--desk).

| Area | Desk | Owner (accountable) |
|---|---|---|
| Market Memory, ingest, provenance, schemas, PIT | Data & Market Memory Desk | Data desk (unassigned human; Coordinator until named) |
| Crypto thesis / HL structure research | Crypto Desk | Research (Coordinator assigns per card) |
| Equity / post-IPO cards and screens | Equities & Post-IPO Desk | Research (Coordinator assigns per card) |
| US Market Pulse, calendar, macro config | Macro & Cross-Asset Desk | Don (IMP-002) |
| Quant Review Board / cards | Quant & Market Structure Desk | Don/Quant (IMP-001 DONE) |
| `skeptic-review.md` / `lab skeptic` | Independent Skeptic | Independent reviewer (not the author) |
| `config/risk/*`, halt, live.yaml guard | Risk (independent veto) | Risk (Principal owns live.yaml) |
| Paper ledger `lab paper` | Principal-gated lab control | Principal enables; Coordinator operates CLI |
| `packages/execution`, `apps/execution-service` | Execution & Fund Ops | **Dormant / future only** |
| Fund ledger, tax, investor reporting | Execution & Fund Ops | **Absent / future only** |

## Gaps (not yet queued)

These are identified so they are not silently treated as existing desks. They are **not** `IN_PROGRESS` and are not seeded as IMP items until Chief of Staff intakes them.

| Gap | Desk that would own | Why not queued now |
|---|---|---|
| Standing DQ / source-health report | Data & Market Memory Desk | Charter names the artifact; no generator this cycle |
| Dedicated crypto / equity thesis-card templates | Crypto Desk; Equities & Post-IPO Desk | Generic `templates/thesis.md` suffices until Board exists |
| Post-IPO reclaim screen product | Equities & Post-IPO Desk | Needs Quant language rules (IMP-001) first |
| Equity-feed ingest; on-chain ingest | Data & Market Memory Desk | Mandate/paid-data/ToS — Principal gate |
| `risk-review.md` + portfolio exposure report | Risk (independent veto) | Risk *service* is out of Phase 4 |
| Quant Board generator + Quant Cards | Quant & Market Structure Desk | **IMP-001 DONE** (#31) |
| Cross-asset regime note cadence | Macro & Cross-Asset Desk | Covered by IMP-002 scope |
| Execution order-state / recon | Execution & Fund Ops | Future only; Principal enablement required |
| Fund P&L / investor reporting | Execution & Fund Ops | Future only; legal approval required |
| Rename historical “active calls” in universe/queue files | Principal + Quant & Market Structure Desk | Membership language vs Quant vocabulary; not this PR |

## Reconciliation notes

- No `ops/improvement-queue.md` existed on `main` or on parked agent branches.
- `origin/cursor/ops-scan-proposals-2158` has `ops/README.md` plus proposal/draft playbooks. Those are **not** this queue; they were not used as the base. Fresh branch from `main`.
- `research/queue/` remains artifact storage for research packs. It is not an improvement backlog. New implementation work is IMP-* here, then artifacts there if the owning desk produces them.
