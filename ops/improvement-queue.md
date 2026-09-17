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
| **Evidence** | `research/queue/QUANT-20260917-active-calls.md` (historical filename retained); `config/universe.yaml` membership partitions (now `in_universe` / `watch_only` after IMP-005; not a Quant verdict); desk charter Quant section. |
| **Proposed outcome** | A Quant Review Board that emits **one verdict + reason code per instrument**: `RESEARCH_PRIORITY` \| `MONITOR` \| `DEFER` \| `REJECT` \| `INSUFFICIENT_DATA`. Forbidden language: “active call,” “make,” “buy,” “sell,” “high confidence.” Relative-value/reclaim candidate unless executable-arb criteria are fully met. |
| **Definition of done** | `lab quant-review` generator; Board + one Quant Card per reviewed name; closed verdicts `RESEARCH_PRIORITY \| MONITOR \| DEFER \| REJECT \| INSUFFICIENT_DATA` with reason codes; relative-value/reclaim unless Track D executable-arb is complete; language gate (no active call / make / buy / sell / high confidence / sizing); tests + sample board artifact; still not a trading decision. |
| **Non-goals** | No Market Pulse work (IMP-002). No order path, no sizing, no live.yaml, no risk-limit edits. Principal universe membership rename is IMP-005 (was out of scope here). |
| **Dependencies** | IMP-000 (charter + language rules) — **DONE** (#28). Data freshness for any live-looking inputs. |
| **Risk level** | Medium (language and process can be misread as calls). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/31 |
| **Lesson learned** | Merged to `main` (#31). Board + Quant Cards use a closed verdict set and a language gate. Historical `research/queue/` packs remain evidence; they are not the Board. Membership-key rename was deferred to IMP-005. |

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
| **Non-goals** | Turning macro into allocation; enabling live FRED as a silent default; dashboard product; Quant Board rewrite; watchlist recommendation loops; live.yaml / risk-limit edits; execution/signing. |
| **Dependencies** | IMP-000 DONE (#28). IMP-001 DONE (#31) — do not reopen. Benefits from Data DQ reports (not blocking). |
| **Risk level** | Low–medium (partial macro data can be over-read). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/32 |
| **Lesson learned** | Merged to `main` (#32). Live `lab brief preopen --live --no-db` ran `data_quality=partial` with honest unavailable slots: Stooq failed for all five symbols in the agent environment; FRED stayed unavailable without `FRED_API_KEY` (not committed). CoinGecko + allowlisted HL `/info` were fresh. Dual-write DoD path `briefs/YYYY-MM-DD/us-pre-market.md` plus legacy `preopen.md`. Standing DQ/source-health was a named benefit, not blocking — now IMP-003. |

### IMP-003 — Standing data-quality / source-health report

| Field | Value |
|---|---|
| **ID** | IMP-003 |
| **Priority** | P1 |
| **Type** | Desk product / data quality |
| **Desk** | Data & Market Memory Desk |
| **Owner** | Don/Data |
| **Problem** | Charters name a standing DQ / source-health artifact, but no generator exists. IMP-002 Pulse ran `data_quality=partial` with Stooq and FRED honestly unavailable and no desk product to re-check sources independently of a market brief. |
| **Evidence** | [desk-charters.md](desk-charters.md) Data desk artifacts; IMP-002 sample `briefs/2026-09-16/us-pre-market.md`; this queue’s former Gap row. |
| **Proposed outcome** | Repeatable read-only `lab data source-health` writes a versioned health/provenance report for configured Memory and Pulse sources. Never invents prints. |
| **Definition of done** | Command writes `ops/reports/source-health/YYYY-MM-DD.md`; inventory always listed (HL `/info`, CoinGecko, Stooq, FRED, calendar YAML, Postgres, object store); per source `ok\|degraded\|unavailable` plus latency/error class, last success when known, credentials/env missing without printing secrets, Pulse required vs optional; missing env does not crash; forbidden HL types still blocked; tests + sample from a real read-only run; short runbook. |
| **Non-goals** | Paid-data purchases; committing FRED secrets; ToS-violating Stooq scrape fixes; Quant Board; watchlist recommendation loops; execution; live.yaml; risk limits; post-IPO reclaim product. |
| **Dependencies** | IMP-002 DONE (#32) — evidence, not a blocker. |
| **Risk level** | Low (read-only probes). Process risk if operators treat health copy as a brief. |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/33 |
| **Lesson learned** | Merged to `main` (#33). `lab data source-health` writes versioned health/provenance reports; Pulse required vs optional inventory is always listed. Stooq/FRED failures are classified without scrape workarounds or committed secrets. Pulse source hardening (retries / failure-class ops) was split out as IMP-004 and remains PARKED (#34) — not this thread. |

### IMP-004 — Pulse source hardening (Stooq/FRED)

| Field | Value |
|---|---|
| **ID** | IMP-004 |
| **Priority** | P2 |
| **Type** | Desk product / data quality |
| **Desk** | Data & Market Memory Desk + Macro & Cross-Asset Desk |
| **Owner** | Don/Data |
| **Problem** | IMP-002/IMP-003 honestly report Stooq timeout/ToS-class failures and FRED missing-key unavailability. Pulse still has no bounded retry / failure-class hardening, and FRED key ops are not a standing procedure. |
| **Evidence** | IMP-002 sample `briefs/2026-09-16/us-pre-market.md`; IMP-003 report `ops/reports/source-health/2026-09-17.md`; former Gap row “Pulse source hardening”. |
| **Proposed outcome** | Classify Stooq/FRED failure classes; bounded retries where lawful; FRED key ops without committing secrets. |
| **Definition of done** | See open PR #34. Not active on this thread. |
| **Non-goals** | ToS-violating Stooq scrapes; committing `FRED_API_KEY`; Quant Board rewrite; universe expansion; execution; live.yaml. |
| **Dependencies** | IMP-003 DONE (#33). |
| **Risk level** | Low–medium (network/ToS). |
| **Status** | PARKED |
| **PR** | https://github.com/ElChopa11/market-memory/pull/34 |
| **Lesson learned** | Open PR, CI green, **not this thread**. Do not continue IMP-004 here. |

### IMP-005 — Active-call language debt (membership vocabulary)

| Field | Value |
|---|---|
| **ID** | IMP-005 |
| **Priority** | P1 |
| **Type** | Hygiene / docs + config |
| **Desk** | Principal + Quant & Market Structure Desk |
| **Owner** | Don/Quant |
| **Problem** | Historical Principal-universe field names and queue prose (`active_calls` / “active call”, MAKE-as-recommendation) conflate **universe membership** with Quant/trade recommendations. IMP-001 locked closed verdicts and banned investment-call language; leftover keys still read like calls. |
| **Evidence** | `config/universe.yaml` former `active_calls` / `watch_only`; `research/queue/` packs; IMP-001 language gate (`packages/research_kit/.../language.py`); desk charter Quant section. |
| **Proposed outcome** | Canonical Principal membership vocabulary only: `in_universe` / `watch_only` (plus `membership` = full locked ingest/briefing set). Quant verdicts stay the closed set `RESEARCH_PRIORITY \| MONITOR \| DEFER \| REJECT \| INSUFFICIENT_DATA`. Membership sets unchanged. |
| **Definition of done** | Plan file; inventory then rename/rewrite lab-owned config/docs/templates/queue prose; loaders/tests/schemas on new keys; regression that canonical membership config keys are not `active_calls`; language gates intact (and cheap template lint if present); `uv run pytest` + lifecycle; non-draft PR to main; do not merge. |
| **Non-goals** | No merge of #34; no Pulse/Stooq/FRED code; no universe expansion (ticker set stays the same); no Quant Board rewrite; no MAKE/buy/sell recommendations; no sizing; no execution; no live.yaml; no secrets; no paid data; no Telegram; no invented market prints. |
| **Dependencies** | IMP-001 DONE (#31). |
| **Risk level** | Low (rename/docs). Process risk if operators still read membership as a call. |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/35 |
| **Lesson learned** | Merged to `main` (#35). Canonical membership keys are `in_universe` / `watch_only`. Ticker sets unchanged. There is no `active_calls` key. Historical pack filenames that contain `active-calls` stay as evidence ids. |

### IMP-006 — Post-IPO reclaim screen product

| Field | Value |
|---|---|
| **ID** | IMP-006 |
| **Priority** | P1 |
| **Type** | Desk product / research screen |
| **Desk** | Equities & Post-IPO Desk |
| **Owner** | Don/Equities |
| **Problem** | Charters name a post-IPO reclaim screen, but no generator exists. Quant Board Track C is a one-line list, not a standing Equities product with provenance, freshness, and honest unavailable metrics. Language rules (IMP-001) and membership vocab (IMP-005) are done; this screen was blocked on those. |
| **Evidence** | [desk-charters.md](desk-charters.md) Equities artifacts; Quant Board `## Post-IPO reclaim list`; this queue’s former Gap row; IMP-001 closed verdicts; IMP-005 membership keys. |
| **Proposed outcome** | Repeatable read-only `lab equities reclaim-screen` writes a versioned triage screen of Post-IPO / reclaim **candidates** (relative-value framing) with source + freshness. Closed Quant verdicts only. Not a trading decision. |
| **Definition of done** | Queue hygiene (IMP-005 DONE #35; IMP-004 PARKED #34; this item IN_PROGRESS); plan file; screen-only config (does not expand `in_universe`); CLI writes `research/screens/post-ipo-reclaim/YYYY-MM-DD.md`; each row has instrument, as-of, reclaim/relative metrics with source + freshness, `fresh\|stale\|partial\|unavailable`, Quant verdict + reason code; informational footer + Principal gate; never invent prints; runbook + charter link; tests + committed fixture sample; `uv run pytest` + lifecycle. |
| **Non-goals** | No merge of #34; no Pulse/Stooq/FRED; no execution/signing/`live.yaml`/risk-limit edits; no paid data; no ToS-violating scrapes; no Principal membership rename or ticker expansion; no Telegram; no secrets; no MAKE/buy/sell/sizing. |
| **Dependencies** | IMP-001 DONE (#31). IMP-005 DONE (#35). IMP-004 stays PARKED (#34). |
| **Risk level** | Medium (language and drawdowns can be misread as calls). |
| **Status** | IN_PROGRESS |
| **PR** | *(this PR)* |
| **Lesson learned** | *(fill at close)* |

---

## Status board

| ID | Desk | Owner | Status | Notes |
|---|---|---|---|---|
| IMP-000 | Chief of Staff / Hive Coordinator | Don | DONE | [#28](https://github.com/ElChopa11/market-memory/pull/28) merged |
| IMP-001 | Quant & Market Structure Desk | Don/Quant | DONE | [#31](https://github.com/ElChopa11/market-memory/pull/31) merged |
| IMP-002 | Macro & Cross-Asset Desk | Don | DONE | [#32](https://github.com/ElChopa11/market-memory/pull/32) merged |
| IMP-003 | Data & Market Memory Desk | Don/Data | DONE | [#33](https://github.com/ElChopa11/market-memory/pull/33) merged |
| IMP-004 | Data & Market Memory Desk + Macro | Don/Data | PARKED | [#34](https://github.com/ElChopa11/market-memory/pull/34) — not this thread |
| IMP-005 | Principal + Quant & Market Structure Desk | Don/Quant | DONE | [#35](https://github.com/ElChopa11/market-memory/pull/35) merged |
| IMP-006 | Equities & Post-IPO Desk | Don/Equities | IN_PROGRESS | this PR — only active implementation |

`IN_PROGRESS` count: **1** (IMP-006 Post-IPO reclaim screen). IMP-000–IMP-003 and IMP-005 are `DONE`. IMP-004 is `PARKED`.

---

## Map: existing capabilities → desks

Short form. Full table: [desk-charters.md — capability map](desk-charters.md#capability-map-repo--desk).

| Area | Desk | Owner (accountable) |
|---|---|---|
| Market Memory, ingest, provenance, schemas, PIT | Data & Market Memory Desk | Data desk (unassigned human; Coordinator until named) |
| Crypto thesis / HL structure research | Crypto Desk | Research (Coordinator assigns per card) |
| Equity / post-IPO cards and screens | Equities & Post-IPO Desk | Don/Equities (IMP-006 IN_PROGRESS) |
| US Market Pulse, calendar, macro config | Macro & Cross-Asset Desk | Don (IMP-002 DONE) |
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
| Dedicated crypto / equity thesis-card templates | Crypto Desk; Equities & Post-IPO Desk | Generic `templates/thesis.md` suffices until a later intake |
| Equity-feed ingest; on-chain ingest | Data & Market Memory Desk | Mandate/paid-data/ToS — Principal gate |
| `risk-review.md` + portfolio exposure report | Risk (independent veto) | Risk *service* is out of Phase 4 |
| Quant pack rewrite (templates / pack workflow) | Quant & Market Structure Desk | IMP-001 plan placeholder; **not** assigned IMP-003 (source-health took that ID) |
| Cross-asset regime note cadence | Macro & Cross-Asset Desk | Deferred from IMP-002 |
| Execution order-state / recon | Execution & Fund Ops | Future only; Principal enablement required |
| Fund P&L / investor reporting | Execution & Fund Ops | Future only; legal approval required |

Pulse source hardening (Stooq timeout/ToS class; FRED key ops) was a Gap; it is now **IMP-004 PARKED** (#34) — not active, not this thread.

Historical “active calls” language debt was a Gap; it is now **IMP-005 DONE** (#35).

Post-IPO reclaim screen product was a Gap; it is now **IMP-006 IN_PROGRESS**.

## Reconciliation notes

- No `ops/improvement-queue.md` existed on `main` or on parked agent branches.
- `origin/cursor/ops-scan-proposals-2158` has `ops/README.md` plus proposal/draft playbooks. Those are **not** this queue; they were not used as the base. Fresh branch from `main`.
- `research/queue/` remains artifact storage for research packs. It is not an improvement backlog. New implementation work is IMP-* here, then artifacts there if the owning desk produces them.
- IMP-003 merged as #33 while the queue still said `IN_PROGRESS` — hygiene fixed on IMP-005.
- IMP-005 merged as #35 while the queue still said `IN_PROGRESS` — hygiene fixed on IMP-006.
- IMP-004 (#34) stays PARKED; do not continue Pulse/source-health code on this thread.
