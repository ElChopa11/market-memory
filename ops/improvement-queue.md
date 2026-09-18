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
| **Lesson learned** | Merged to `main` (#33). `lab data source-health` (alias `lab dq report`) writes `ops/reports/source-health/YYYY-MM-DD.md`. Honest degraded sample: overall=`degraded`; Stooq canary HTTP 404 (`http_error`); FRED `missing_env` without `FRED_API_KEY`; Postgres `unreachable`; object_store `missing_env`; HL `/info` + CoinGecko + `calendar.yaml` `ok`. Pulse-required sources stayed up so overall was degraded, not unavailable. Inventory always listed; no prints/secrets. Retry/timeout/`http_404` hardening is IMP-004 (#34). |

### IMP-004 — Pulse source hardening

| Field | Value |
|---|---|
| **ID** | IMP-004 |
| **Priority** | P1 |
| **Type** | Reliability / read-only client hardening |
| **Desk** | Data & Market Memory Desk + Macro & Cross-Asset Desk |
| **Owner** | Don/Data+Macro |
| **Problem** | IMP-002 Pulse and IMP-003 source-health both observed honest unavailability: Stooq canary/CSV HTTP 404 and timeouts, FRED `missing_env` without `FRED_API_KEY`. Failure classes were coarse (404 lumped as `http_error`), Pulse used a 20s timeout with no bounded retry, and operators lacked a runbook for setting FRED locally/CI without committing the key. |
| **Evidence** | IMP-002 lesson (#32) live brief `data_quality=partial`; IMP-003 sample [`ops/reports/source-health/2026-09-17.md`](reports/source-health/2026-09-17.md) (Stooq HTTP 404, FRED missing_env, Postgres unreachable, object_store missing_env); former Gaps row “Pulse source hardening”. |
| **Proposed outcome** | Shared GET helper for Pulse + source-health: closed error classes (`timeout`, `http_404`, `http_5xx`, …), 8s timeout, one idempotent retry only on timeout/connect/429/5xx, clearer FRED missing-env copy, ops notes. Reports and briefs stay honest (`ok\|degraded\|unavailable` / `fresh\|stale\|partial\|unavailable`). Dual-write briefs unchanged. |
| **Definition of done** | Queue: IMP-003 DONE #33 with lesson; this item closed on #34. Plan `ops/plans/IMP-004-pulse-source-hardening.md`. Shared helper used by briefing + source_health. Stooq: classify timeout/404/5xx; bounded GET retry; **no** scrape URLs. FRED: env-only key; missing_env operator hint; never commit. Tests for classification/retry. Runbook updates. No secrets, no invented prints. |
| **Non-goals** | Paid data; committing `FRED_API_KEY`; Stooq ToS-violating scrape alternatives; Quant Board rewrite; watchlist recommendation loops; `live.yaml` / risk-limit edits / execution / signing / wallet HL endpoints; post-IPO reclaim product; universe membership rename (IMP-005). |
| **Dependencies** | IMP-003 DONE (#33). IMP-002 DONE (#32). |
| **Risk level** | Low (read-only). Residual: Stooq 404 from cloud IPs stays unavailable; FRED stays unavailable until operators set the env. |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/34 |
| **Lesson learned** | Shared GET helper (`mm_common.http`) classifies `timeout` / `http_404` / `http_5xx`; 8s timeout; one idempotent retry on timeout/5xx/429 only; 404 is terminal. FRED stays env-only with clearer `missing_env` operator copy. No Stooq scrape fallbacks or committed secrets. |

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
| **Definition of done** | Plan file; inventory then rename/rewrite lab-owned config/docs/templates/queue prose; loaders/tests/schemas on new keys; regression that canonical membership config keys are not `active_calls`; language gates intact (and cheap template lint if present); `uv run pytest` + lifecycle; merged to main as #35. |
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
| **Definition of done** | Plan file; screen-only config (does not expand `in_universe`); CLI writes `research/screens/post-ipo-reclaim/YYYY-MM-DD.md`; each row has instrument, as-of, reclaim/relative metrics with source + freshness, `fresh\|stale\|partial\|unavailable`, Quant verdict + reason code; informational footer + Principal gate; never invent prints; runbook + charter link; tests + committed fixture sample; `uv run pytest` + lifecycle. |
| **Non-goals** | No Pulse/Stooq/FRED; no execution/signing/`live.yaml`/risk-limit edits; no paid data; no ToS-violating scrapes; no Principal membership rename or ticker expansion; no Telegram; no secrets; no MAKE/buy/sell/sizing. |
| **Dependencies** | IMP-001 DONE (#31). IMP-005 DONE (#35). |
| **Risk level** | Medium (language and drawdowns can be misread as calls). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/36 |
| **Lesson learned** | Merged to `main` (#36). `lab equities reclaim-screen` writes a screen-only Post-IPO/reclaim triage (`config/equities/post_ipo_reclaim.yaml`); closed Quant verdicts; does not expand `in_universe`. Fixture sample CRCL/HOOD `DEFER` / `partial`. Not a trading decision. |

### IMP-007 — Dedicated crypto + equities thesis-card templates

| Field | Value |
|---|---|
| **ID** | IMP-007 |
| **Priority** | P1 |
| **Type** | Docs / desk product (templates) |
| **Desk** | Crypto Desk + Equities & Post-IPO Desk |
| **Owner** | Don/Research |
| **Problem** | Charters name crypto and equity thesis cards, but only generic `templates/thesis.md` exists. Cards lack IMP-001 closed verdicts, IMP-005 membership vocabulary, provenance fields, and an Independent Skeptic stub. Queue packs are not reusable desk cards. |
| **Evidence** | [desk-charters.md](desk-charters.md) Crypto / Equities artifacts; this queue’s former Gap row; generic `templates/thesis.md`; IMP-001 closed verdicts; IMP-005 `in_universe` / `watch_only`. |
| **Proposed outcome** | Dedicated `templates/crypto-thesis-card.md` and `templates/equities-thesis-card.md`. Generic `thesis.md` stays the lifecycle spine. `lab thesis new` copies the matching desk card for locked membership names. |
| **Definition of done** | Queue hygiene: IMP-004/005/006 DONE. Plan file; two templates with closed verdicts, membership keys, provenance, Skeptic stub, explicit non-goals; short runbook; language lint + unit tests; `uv run pytest` + lifecycle; merged to main as #37. |
| **Non-goals** | No Pulse/Stooq/FRED; no execution/signing/`live.yaml`/risk-limit edits; no paid data; no ToS-violating scrapes; no universe expansion; no Telegram; no secrets; no MAKE/buy/sell/sizing; no replacing `thesis.md`; no Quant Board rewrite. |
| **Dependencies** | IMP-001 DONE (#31). IMP-005 DONE (#35). IMP-006 DONE (#36) for Equities screen vs card boundary. |
| **Risk level** | Low (templates). Process risk if operators treat a desk card as a call or skip Skeptic. |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/37 |
| **Lesson learned** | Merged to `main` (#37). Dedicated `templates/crypto-thesis-card.md` and `templates/equities-thesis-card.md` sit beside generic `thesis.md`. `lab thesis new --instrument` copies the matching desk card for locked membership names. Do not reopen template work. |

### IMP-008 — Quant RESEARCH_PRIORITY pass (locked universe only)

| Field | Value |
|---|---|
| **ID** | IMP-008 |
| **Priority** | P1 |
| **Type** | Desk product / Quant pass |
| **Desk** | Quant & Market Structure Desk |
| **Owner** | Don/Quant |
| **Problem** | IMP-001 Board scored a screenshot/TV watchlist (36 names), not the Principal-locked membership. There is no fresh RESEARCH_PRIORITY pass on `in_universe` ∪ `watch_only` as-of 2026-09-18 Sydney. IMP-007 hygiene was still showing IN_PROGRESS after #37 merged. |
| **Evidence** | `config/universe.yaml`; `research/quant/2026-09-17/`; Skeptic scorecard PR #22; FAIL patches PR #23; WATCHLIST-DD cut-review; source-health 2026-09-17 (Stooq/FRED degraded); SEC PR 2026-90 (2026-09-17). |
| **Proposed outcome** | Dated locked-membership Quant Review Board + per-name cards. Closed verdicts only. Zero forced RESEARCH_PRIORITY. UNI/AAVE re-evaluated against SEC PR 2026-90 only if falsifiable. IMP-007 marked DONE. |
| **Definition of done** | IMP-007 DONE (#37). This item the only implementation thread while open. Plan file. Board covers BTC, NVDA, AVGO, MSFT, META, JPM, XOM, ETH, UNI, AAVE, SMH, XLF. No deferred_must_cut members. Counts + RESEARCH_PRIORITY list (or none). Language gate. Tests. `uv run pytest` + lifecycle. PR to main. No secrets, no live path, no paid-data. |
| **Non-goals** | Screenshot-board rewrite; universe expansion; thesis-card reopen; Pulse/Stooq scrape; paid data; execution/`live.yaml`; MAKE/buy/sell/sizing; inventing prints. |
| **Dependencies** | IMP-001 DONE (#31). IMP-005 DONE (#35). IMP-007 DONE (#37). |
| **Risk level** | Medium (language and membership can be misread as calls). Residual: equity tape still missing. |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/38 |
| **Lesson learned** | Merged to `main` (#38). Locked-membership pass is a desk re-score, not a rubber-stamp of screenshot-engine overlay rel. RESEARCH_PRIORITY names: **none**. MONITOR: ETH (BTC-beta), UNI (SEC PR 2026-90 mapping test). DEFER: BTC, NVDA, JPM, AAVE, SMH, XLF. INSUFFICIENT_DATA: AVGO, MSFT, META, XOM. Stooq/FRED remain degraded. Do not reopen. |

### IMP-009 — Phase 5a desk boundaries

| Field | Value |
|---|---|
| **ID** | IMP-009 |
| **Priority** | P0 |
| **Type** | Docs / CI / skeletons |
| **Desk** | Chief of Staff / Hive Coordinator |
| **Owner** | Don |
| **Problem** | Principal approved Phase 5a–5e (equities default Polygon), one phase per PR. Hive roles and IMP-000 charters do not encode Tier 0–7, import walls, Skeptic FAIL return/archive, or Risk BLOCK as terminal. Delivery details would otherwise leak into 5a. |
| **Evidence** | [AGENTS.md](../AGENTS.md); [desk-charters.md](desk-charters.md); ADR 0001; IMP-008 DONE #38; Principal Phase 5 brief (5a desk boundaries). |
| **Proposed outcome** | 5a commits the desk/delivery architecture. Skeletons + CI only. 5b–5e named as follow-ons. |
| **Definition of done** | IMP-008 DONE (#38). Tiers in AGENTS + charters; ADR 0002; import-boundary CI; lifecycle state-machine skeleton + transition log hook (`actor`, `ts`, `reason`); output-contract template; `docs/runbooks/desks.md`; IMP-010 stubbed READY; README Phase 5 in progress (5a); `uv run pytest` + lifecycle + guards. No Polygon/Telegram/factors/runners/`live.yaml`. |
| **Non-goals** | Polygon/HL adapters; quant factor implementations; desk full runners; Telegram client; schedules; secrets; `live.yaml`; signing/order code; paid deps; risk *service*; 5e delivery. |
| **Dependencies** | IMP-008 DONE (#38). |
| **Risk level** | Low (docs/CI). Process risk if 5b is started in this PR. |
| **Status** | IN_REVIEW |
| **PR** | https://github.com/ElChopa11/market-memory/pull/40 |
| **Lesson learned** | *(fill at close)* |

### IMP-010 — Phase 5b Polygon equities + HL structure

| Field | Value |
|---|---|
| **ID** | IMP-010 |
| **Priority** | P1 |
| **Type** | Data / ingest |
| **Desk** | Data & Market Memory Desk |
| **Owner** | Don/Data |
| **Problem** | Equities have no durable tape in Memory. Crypto funding/OI/basis/depth is not a standing ingest product. Principal lock: equities default Polygon. |
| **Evidence** | IMP-008 residual: no equity-feed ingest; IMP-009 ADR 0002 follow-on; `config/universe.yaml` equity membership. |
| **Proposed outcome** | Polygon equities adapter + HL funding/OI/basis/depth + spot cross-check into Market Memory. Read-only. Degrade-never-invent. Universe ticker set unchanged unless Principal expands membership. |
| **Definition of done** | *(filled in the 5b PR)*. Plan stub: [plans/IMP-010-phase5b-polygon-hl-structure.md](plans/IMP-010-phase5b-polygon-hl-structure.md). Not started while IMP-009 is open. |
| **Non-goals** | Desk runners; quant factors; Telegram/5e; signing; `live.yaml`; paid deps without Principal ask; reopening IMP-009. |
| **Dependencies** | IMP-009 (this PR) must be DONE. |
| **Risk level** | Medium (vendor ToS, secrets in env, over-reading structure as a call). |
| **Status** | READY |
| **PR** | — |
| **Lesson learned** | Parked. Do not implement in IMP-009. |

---

---

## Status board


| ID | Desk | Owner | Status | Notes |
|---|---|---|---|---|
| IMP-000 | Chief of Staff / Hive Coordinator | Don | DONE | [#28](https://github.com/ElChopa11/market-memory/pull/28) merged |
| IMP-001 | Quant & Market Structure Desk | Don/Quant | DONE | [#31](https://github.com/ElChopa11/market-memory/pull/31) merged |
| IMP-002 | Macro & Cross-Asset Desk | Don | DONE | [#32](https://github.com/ElChopa11/market-memory/pull/32) merged |
| IMP-003 | Data & Market Memory Desk | Don/Data | DONE | [#33](https://github.com/ElChopa11/market-memory/pull/33) merged |
| IMP-004 | Data & Market Memory Desk + Macro & Cross-Asset Desk | Don/Data+Macro | DONE | [#34](https://github.com/ElChopa11/market-memory/pull/34) — Pulse source hardening |
| IMP-005 | Principal + Quant & Market Structure Desk | Don/Quant | DONE | [#35](https://github.com/ElChopa11/market-memory/pull/35) merged |
| IMP-006 | Equities & Post-IPO Desk | Don/Equities | DONE | [#36](https://github.com/ElChopa11/market-memory/pull/36) merged |
| IMP-007 | Crypto Desk + Equities & Post-IPO Desk | Don/Research | DONE | [#37](https://github.com/ElChopa11/market-memory/pull/37) merged |
| IMP-008 | Quant & Market Structure Desk | Don/Quant | DONE | [#38](https://github.com/ElChopa11/market-memory/pull/38) merged |
| IMP-009 | Chief of Staff / Hive Coordinator | Don | IN_REVIEW | [#40](https://github.com/ElChopa11/market-memory/pull/40) Phase 5a desk boundaries |
| IMP-010 | Data & Market Memory Desk | Don/Data | READY | Phase 5b Polygon + HL structure — parked; do not implement here |

`IN_PROGRESS` count: **0**. IMP-000–IMP-008 are `DONE`. IMP-009 is `IN_REVIEW` (DoD met in this PR). IMP-010 is `READY` (parked until 009 merges).


---

## Map: existing capabilities → desks

Short form. Full table: [desk-charters.md — capability map](desk-charters.md#capability-map-repo--desk).

| Area | Desk | Owner (accountable) |
|---|---|---|
| Market Memory, ingest, provenance, schemas, PIT | Data & Market Memory Desk | Data desk (unassigned human; Coordinator until named) |
| Crypto thesis / HL structure research | Crypto Desk | Don/Research (IMP-007 thesis cards DONE #37) |
| Equity / post-IPO cards and screens | Equities & Post-IPO Desk | Don/Research (IMP-006 screen DONE; IMP-007 thesis cards DONE #37) |
| US Market Pulse, calendar, macro config | Macro & Cross-Asset Desk | Don (IMP-002 DONE; IMP-004 DONE) |
| Quant Review Board / cards | Quant & Market Structure Desk | Don/Quant (IMP-001 DONE; IMP-008 locked-membership pass DONE #38) |
| `skeptic-review.md` / `lab skeptic` | Independent Skeptic | Independent reviewer (not the author) |
| `config/risk/*`, halt, live.yaml guard | Risk (independent veto) | Risk (Principal owns live.yaml) |
| Paper ledger `lab paper` | Principal-gated lab control | Principal enables; Coordinator operates CLI |
| `packages/execution`, `apps/execution-service` | Execution & Fund Ops | **Dormant / future only** |
| Fund ledger, tax, investor reporting | Execution & Fund Ops | **Absent / future only** |

## Gaps (not yet queued)

These are identified so they are not silently treated as existing desks. They are **not** `IN_PROGRESS` and are not seeded as IMP items until Chief of Staff intakes them.

| Gap | Desk that would own | Why not queued now |
|---|---|---|
| Equity-feed ingest; on-chain ingest | Data & Market Memory Desk | Mandate/paid-data/ToS — Principal gate |
| `risk-review.md` + portfolio exposure report | Risk (independent veto) | Risk *service* is out of Phase 4 |
| Quant pack rewrite (templates / pack workflow) | Quant & Market Structure Desk | IMP-001 plan placeholder; **not** assigned IMP-003 (source-health took that ID) |
| Cross-asset regime note cadence | Macro & Cross-Asset Desk | Deferred from IMP-002 |
| Execution order-state / recon | Execution & Fund Ops | Future only; Principal enablement required |
| Fund P&L / investor reporting | Execution & Fund Ops | Future only; legal approval required |

Pulse source hardening (Stooq timeout/ToS class; FRED key ops) was a Gap; it is now **IMP-004 DONE** (#34).

Historical “active calls” language debt was a Gap; it is now **IMP-005 DONE** (#35). Do not reopen.

Post-IPO reclaim screen product was a Gap; it is now **IMP-006 DONE** (#36). Do not reopen.

Dedicated crypto / equity thesis-card templates were a Gap; they are now **IMP-007 DONE** (#37). Generic `thesis.md` stays the lifecycle spine. Do not reopen.

Quant RESEARCH_PRIORITY pass on locked membership was a Gap; it is now **IMP-008 DONE** (#38). Screenshot/TV board remains IMP-001. Do not treat membership as a Quant verdict.

Phase 5 desk/delivery architecture is **IMP-009 IN_REVIEW** (5a only). Polygon equities + HL structure is **IMP-010 READY** (parked; 5b). Do not start 5b in this PR.

## Reconciliation notes

- No `ops/improvement-queue.md` existed on `main` or on parked agent branches.
- `origin/cursor/ops-scan-proposals-2158` has `ops/README.md` plus proposal/draft playbooks. Those are **not** this queue; they were not used as the base. Fresh branch from `main`.
- `research/queue/` remains artifact storage for research packs. It is not an improvement backlog. New implementation work is IMP-* here, then artifacts there if the owning desk produces them.
- IMP-003 merged as #33 while the queue still said `IN_PROGRESS` — hygiene fixed on IMP-005.
- IMP-005 merged as #35 while the queue still said `IN_PROGRESS` — hygiene fixed on IMP-006.
- IMP-006 merged as #36 while the queue still said `IN_PROGRESS` — hygiene fixed on IMP-004 rebase onto `main`.
- IMP-004 (#34) rebased onto `main` after #35/#36; Pulse/source-health hardening lands here. Membership vocab stays `in_universe` / `watch_only`.
- IMP-007 merged as #37 while the queue still said `IN_PROGRESS` — hygiene fixed on IMP-008.
- IMP-008 merged as #38 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-009.
- IMP-009 intakes Phase 5a desk boundaries (Principal-approved 5a–5e; one phase per PR). Single-threaded: no item remains `IN_PROGRESS` (`IN_REVIEW` pending merge). IMP-010 is READY/parked for 5b.
