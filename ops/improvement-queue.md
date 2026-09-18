# Improvement queue

Single continuous-improvement list for Market Memory. The lab runs a **desk model** ([desk-charters.md](desk-charters.md)): every work item belongs to one desk and has **one accountable owner**. Chief of Staff (Don) maintains this file, assigns desks, and enforces **single-threaded implementation** — at most one item in `IN_PROGRESS`. Ready work is parked, not started in parallel.

This queue is the operating system, not an investment book. It does not authorise trades, enable execution, or waive Skeptic / Principal gates ([decision-rights.md](decision-rights.md)).

## Operating rules

1. **Intake** only through this file. Research cards under `research/queue/` are evidence or artifacts, not a second backlog.
2. **One `IN_PROGRESS` implementation item.** Review (`IN_REVIEW`) of docs is allowed while implementation stays parked.
3. **No duplicate research.** If an artifact already answers the question, close or merge the item with a lesson.
4. **Reusable artifacts.** Prefer templates, schema records, and desk products over one-off commentary.
5. Status vocabulary: `OPEN` (ops incident, not closed) → `BACKLOG` → `READY` → `IN_PROGRESS` → `IN_REVIEW` → `DONE` | `PARKED` | `REJECTED`. `OPEN` items are logged incidents; they are **not** closed and do not occupy the single `IN_PROGRESS` implementation slot.

## Required fields (every item)

Each item must include at least: **ID**, **Priority**, **Type**, **Desk**, **Owner**, **Problem**, **Evidence**, **Proposed outcome**, **Definition of done**, **Non-goals**, **Dependencies**, **Risk level**, **Status**, **PR**, **Lesson learned**.

---

## Active / seeded items

### SCHED-001 — Sydney 08:00 digest never fired

| Field | Value |
|---|---|
| **ID** | SCHED-001 |
| **Priority** | P1 |
| **Type** | Scheduler reliability |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | Sydney 08:00 digest was configured and never fired. Root cause unknown. |
| **Evidence** | Routine `sydney-morning-digest-8am` showed never-run while sibling NY-cron briefs completed. Do not treat as closed. |
| **Proposed outcome** | Find why the Sydney 08:00 job did not fire; restore or document the miss without closing until verified. |
| **Definition of done** | Root cause recorded; job either fires on the next Sydney 08:00 window or the miss is explained with a fix queued. Still OPEN until then. |
| **Non-goals** | Closing the ticket on config-exists-therefore-done; live trading; 6c-5 delivery expansion. |
| **Dependencies** | None. |
| **Risk level** | Medium (missed Principal digest). |
| **Status** | OPEN |
| **PR** | — |
| **Lesson learned** | *(open — do not close)* |

### BRIEF-TAG-20260918 — Fri 18 Sep pre-market fired ~90m pre-open

| Field | Value |
|---|---|
| **ID** | BRIEF-TAG-20260918 |
| **Priority** | P2 |
| **Type** | Scorecard hygiene / tagging |
| **Desk** | Ops / Quant scorecard |
| **Owner** | Ops/Quant scorecard |
| **Problem** | Fri 18 Sep pre-market artifact fired ~90m pre-open (08:00 NY / 22:00 Syd) vs current 30m-pre-open anchor (09:00 NY / 23:00 Syd). Like-for-like scorecard compare is invalid. |
| **Evidence** | Config `config/schedules/market-pulse.yaml` `pre_open.local_time: "08:00"` America/New_York; Principal 30m-pre-open anchor is 09:00 NY / 23:00 Syd. |
| **Proposed outcome** | Tag that artifact so scorecards do not compare like-for-like vs 30m-pre-open packs. |
| **Definition of done** | Artifact tagged; scorecard docs note the 90m vs 30m mismatch; item stays OPEN until the tag is applied. |
| **Non-goals** | Rewriting Pulse; 6c-5; treating the 18 Sep pack as a 30m-pre-open golden. |
| **Dependencies** | None. |
| **Risk level** | Low (comparability). |
| **Status** | OPEN |
| **PR** | — |
| **Lesson learned** | *(open — do not close)* |

### SRC-STOOQ-404 — stooq http_404, 2 consecutive

| Field | Value |
|---|---|
| **ID** | SRC-STOOQ-404 |
| **Priority** | P1 |
| **Type** | Source health |
| **Desk** | Intel |
| **Owner** | Intel |
| **Problem** | Stooq HTTP 404, two consecutive observations. Pulse/source-health already classify `http_404` as terminal (IMP-004). Still OPEN. |
| **Evidence** | [`ops/reports/source-health/2026-09-17.md`](reports/source-health/2026-09-17.md) Stooq canary HTTP 404; IMP-002/IMP-003/IMP-004 lessons. Two consecutive. |
| **Proposed outcome** | Intel owns the source: confirm whether 404 is IP/ToS/path; keep honest unavailable; no scrape fallback. |
| **Definition of done** | Consecutive-404 record in this queue; Intel note on next source-health run; not closed by IMP-004 (hardening already shipped). |
| **Non-goals** | ToS-violating scrape URLs; paid data; inventing prints. |
| **Dependencies** | IMP-004 DONE (#34) — classification exists; this is the open consecutive-404 incident. |
| **Risk level** | Low–medium (optional Pulse slot stays unavailable). |
| **Status** | OPEN |
| **PR** | — |
| **Lesson learned** | *(open — do not close)* |

### SRC-FRED-MISSING-ENV — fred missing_env

| Field | Value |
|---|---|
| **ID** | SRC-FRED-MISSING-ENV |
| **Priority** | P1 |
| **Type** | Secrets / env |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | FRED `missing_env` (`FRED_API_KEY` unset). |
| **Evidence** | Source-health 2026-09-17 FRED `missing_env`; IMP-002/IMP-003 lessons. |
| **Proposed outcome** | Set `FRED_API_KEY` in repo secrets + env. **Queued for Principal — Don does not decide secrets.** |
| **Definition of done** | Principal sets the env/secret; next source-health is not `missing_env`. Stays OPEN until Principal acts. |
| **Non-goals** | Committing the key; Don/Coord deciding secrets; inventing FRED prints. |
| **Dependencies** | Principal (secrets). |
| **Risk level** | Low (honest unavailable until keyed). |
| **Status** | OPEN |
| **PR** | — |
| **Lesson learned** | *(open — queued for Principal; Don does not decide secrets)* |

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
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/40 |
| **Lesson learned** | Merged to `main` (#40). Tier 0–7, import-boundary CI, lifecycle skeleton, output-contract template. Polygon/Telegram/factors/runners stayed out of 5a. IMP-010 is the 5b implementation thread. |

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
| **Definition of done** | Queue hygiene: IMP-009 DONE (#40). This item the only implementation thread. Polygon default equities adapter (swappable; Ask N/A); HL public `/info` funding/OI/basis/l2 + optional public spot DQ; FRED + fixture calendar; typed models; retry/backoff; `config/ingest.yaml` rate-limit budgets; fixtures + adversarial PIT (`as_of_knowledge`/`ingested_at`); source-health inventory; runbook; README 5b; no signing/`live.yaml`/Telegram/factors/runners. `uv run pytest` + lifecycle + import-boundary. |
| **Non-goals** | Desk runners; quant factors (IMP-011); Telegram/5e; signing; `live.yaml`; paid deps without Principal ask; Redis; reopening IMP-009. |
| **Dependencies** | IMP-009 DONE (#40). |
| **Risk level** | Medium (vendor ToS, secrets in env, over-reading structure as a call). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/41 |
| **Lesson learned** | Merged to `main` (#41). Polygon equities adapter + HL public `/info` structure (funding/OI/basis/L2/predicted funding) + spot DQ + FRED/calendar into Memory. Fixtures + adversarial PIT. Quant factors stayed out of 5b and are IMP-011. |

### IMP-011 — Phase 5c quant factor library

| Field | Value |
|---|---|
| **ID** | IMP-011 |
| **Priority** | P1 |
| **Type** | Quant / research library |
| **Desk** | Quant & Market Structure Desk |
| **Owner** | Don/Quant |
| **Problem** | `packages/quant` is an empty FactorRegistry skeleton from 5a. Structure and equity tape landed in 5b; factor math must not sneak into the ingest PR. |
| **Evidence** | IMP-009 skeleton; ADR 0002 follow-on 5c; IMP-010 DONE #41. |
| **Proposed outcome** | Research-only factor implementations with PIT watermarks, YAML regime thresholds, stat/sizing helpers, QuantCard. Not a trading decision. |
| **Definition of done** | Queue hygiene: IMP-010 DONE (#41). This item the only implementation thread. `mm_quant` factor library (momentum, realised vol, ADX-style, z-score, funding/basis carry from 5b fields, RS vs BTC and sector/ETF, breadth, corr, beta); regime tag+confidence+inputs from `config/quant/*.yaml`; stats + intent-level budget-fraction helpers; `QuantCard` → `templates/quant-factor-card.md` with provenance; fixtures + adversarial PIT; degrade-never-invent; runbook; README 5c; import-boundary CI; no runners/Telegram/`live.yaml`/signing. `uv run pytest` + lifecycle. |
| **Non-goals** | Desk runners (IMP-012); Telegram/5e; signing; `live.yaml`; reopening IMP-010 adapters; paid deps; LLM at decision time; order endpoints. |
| **Dependencies** | IMP-010 DONE (#41). |
| **Risk level** | Medium (look-ahead in factors). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/42 |
| **Lesson learned** | Merged to `main` (#42). `mm_quant` factor library with PIT watermarks, YAML regime thresholds, QuantCard, degrade-never-invent. Desk runners stayed out of 5c and are IMP-012. |

### IMP-012 — Phase 5d desk runners

| Field | Value |
|---|---|
| **ID** | IMP-012 |
| **Priority** | P1 |
| **Type** | Orchestration / desk product |
| **Desk** | Chief of Staff / Hive Coordinator |
| **Owner** | Don |
| **Problem** | Factor math landed in 5c; desk packages were still 5a skeletons. Runners must not sneak into the factor PR. |
| **Evidence** | IMP-009 skeletons; ADR 0002 follow-on 5d; IMP-011 DONE #42. |
| **Proposed outcome** | Coordinator-run desk jobs: each desk `run(as_of, ctx) -> DeskOutput`. Intel assemble, Crypto/Equities notes, Quant calls `mm_quant`, Skeptic FAIL return/archive, Risk allow/block from versioned config, Coord pack into the output contract. `--no-send` only. |
| **Definition of done** | Queue hygiene: IMP-011 DONE (#42). This item the only implementation thread. Desk protocol `OK\|DEGRADED\|FAILED` + completeness_pct + provenance_ids + artifacts; Intel/Crypto/Equities/Quant/Skeptic/Risk/Coord wired; lifecycle transitions logged (actor, ts, reason) and illegal edges rejected; `lab desk run --desk <slug>\|--all --fixture --no-send` deterministic content hash; fixtures for happy / missing-feed DEGRADED / Skeptic FAIL / Risk BLOCK; import-boundary CI holds; runbook + README 5d; no Telegram send, no `live.yaml`, no signing, no Phase 6 bus. `uv run pytest` + lifecycle. |
| **Non-goals** | Telegram/5e; signing; `live.yaml`; reopening IMP-011 factor math; Phase 6 bus; order endpoints; Redis; paid deps. |
| **Dependencies** | IMP-011 DONE (#42). |
| **Risk level** | Medium (runners can skip gates or look like calls). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/43 |
| **Lesson learned** | Merged to `main` (#43). Desk runners Intel→3a\|3b→Quant→Skeptic→Risk→Coord pack with `--no-send` payloads. Telegram send stayed out of 5d and is IMP-013. |

### IMP-013 — Phase 5e Telegram delivery

| Field | Value |
|---|---|
| **ID** | IMP-013 |
| **Priority** | P2 |
| **Type** | Delivery / schedules |
| **Desk** | Chief of Staff / Hive Coordinator |
| **Owner** | Don |
| **Problem** | 5d prepares `--no-send` payload strings only. Principal briefing still has no Telegram Bot API send, schedules, or secrets handling. |
| **Evidence** | ADR 0002 follow-on 5e; `packages/delivery` `SEND_ENABLED = False` after #43; IMP-012 DONE #43. Principal already has `TELEGRAM_*` on the bot box. |
| **Proposed outcome** | Telegram client + config + dry-run payloads + gates. Send remains opt-in (`SEND_ENABLED` stays false). Multi-channel mesh stays Phase 6. |
| **Definition of done** | Queue hygiene: IMP-012 DONE (#43). This item the only implementation thread. `mm_delivery` httpx Bot API (`sendMessage`; optional document/photo); `config/delivery/telegram.yaml` desk→chat_id_env + thread_id; secrets env-only (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_CHAT_ID_<DESK>`); MarkdownV2 + 4096 sequenced chunks; idempotency `(desk, as_of, content_hash)`; threshold / quiet hours / dedupe TTL / rate-limit; `--no-send` golden payload; `lab deliver` + desk `--no-send`; inbound `/status` `/brief` `/desk` stubs; runbook + ADR 0003; README Phase 5 complete; IMP-014 parked; import walls; pytest never hits live API; `uv run pytest` + lifecycle. |
| **Non-goals** | Live trading; signing; `live.yaml`; Phase 6 PG NOTIFY bus; Redis; paid Telegram SDKs; reopening IMP-012 runners except queue hygiene. |
| **Dependencies** | IMP-012 DONE (#43). |
| **Risk level** | Medium (secrets, ToS, alert spam). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/44 |
| **Lesson learned** | Merged to `main` (#44). Telegram Bot API client over httpx; `--no-send` default; secrets env-only. Multi-channel mesh stayed out of 5e and is IMP-014. |

### IMP-014 — Phase 6a PG LISTEN/NOTIFY mesh

| Field | Value |
|---|---|
| **ID** | IMP-014 |
| **Priority** | P1 |
| **Type** | Control plane / bus |
| **Desk** | Chief of Staff / Hive Coordinator |
| **Owner** | Don |
| **Problem** | 5e delivers Telegram as a single Coordinator channel. Per-desk workers and extra channels have no durable notify bus. Principal locked Phase 6a–6f with **bus = Postgres LISTEN/NOTIFY (no Redis)**. |
| **Evidence** | ADR 0003; IMP-013 DONE #44; Principal Phase 6 lock (PG NOTIFY, no Redis). |
| **Proposed outcome** | Desk protocol hardening (cadence + envelope + `content_hash`) and a Postgres `LISTEN/NOTIFY` mesh so desk products fan out. Telegram remains one sink. |
| **Definition of done** | Queue hygiene: IMP-013 DONE (#44). This item the only implementation thread. Envelope header (desk, as_of UTC+Sydney, status, n, completeness, regime placeholder, op=paper\|observation, universe, sources/missing); `content_hash` idempotency (same as_of → identical hash unless new observations); PG NOTIFY channels `desk.<slug>.output` / `alert`, `coord.assemble`, `dq.event`; persist envelopes in Memory (NOTIFY is ids only); Coord worker stub assembles from Memory; missing/killed desk → FAILED + error_class; `lab mesh dry` + `lab desk run` fixtures; ADR 0004 + runbook mesh section; README Phase 6 in progress (6a); IMP-015 parked; import walls; no Redis; `uv run pytest` + lifecycle. |
| **Non-goals** | Redis; flow/macro packages (IMP-015 / 6b); per-desk Telegram fan-out (6c); listings/IPO desk (6d); scorecards (6e); decay/prompt versioning (6f); live trading; signing; `live.yaml`; order endpoints; paid deps. |
| **Dependencies** | IMP-013 DONE (#44). |
| **Risk level** | Medium (fan-out, duplicate notifies). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/45 |
| **Lesson learned** | Merged to `main` (#45). Envelope header + `content_hash` + Postgres LISTEN/NOTIFY mesh (no Redis). Coord assembles when a desk is missing/killed. Regime stayed `unset` until IMP-015. |

### IMP-015 — Phase 6b flow + macro + regime

| Field | Value |
|---|---|
| **ID** | IMP-015 |
| **Priority** | P2 |
| **Type** | Data / macro |
| **Desk** | Macro & Cross-Asset Desk + Data & Market Memory Desk |
| **Owner** | Don/Macro+Data |
| **Problem** | 6a ships envelope `regime: unset`. Flow and macro market-data packages do not exist. Cross-asset regime notes were deferred from IMP-002. |
| **Evidence** | ADR 0004; IMP-014 DONE #45; IMP-002 lesson (regime note deferred). |
| **Proposed outcome** | Read-only flow + macro into Memory and a real regime tag on envelopes. Telegram remains a sink. |
| **Definition of done** | Queue hygiene: IMP-014 DONE (#45). This item the only implementation thread. `mm_flow` liquidity metrics (funding z, OI delta, basis, depth/spread, ADV/turnover, slippage @ clips) + verdict `OK\|THIN\|UNTRADEABLE_AT_SIZE` + max clip; `mm_macro` FRED/curve/DXY/credit/commodities/VIX as available + econ/CB calendar + regime tag+confidence+two driving inputs from `config/macro/regimes.yaml`; missing feeds → unavailable/DEGRADED; envelope `regime` filled when macro succeeds; `EVENT_RISK` within N minutes + `rule_id`; Risk YAML auto-block UNTRADEABLE_AT_SIZE + EVENT_RISK haircut (no LLM); desk runners publish via 6a mesh; Coord assembles if one fails; fixtures + adversarial PIT; runbooks + ADR 0005; README Phase 6 in progress (6b); IMP-016 parked; import walls; no Redis; `uv run pytest` + lifecycle. |
| **Non-goals** | Live trading; signing; `live.yaml`; Redis; 6c–6f products; reopening IMP-014 except queue hygiene; new paid data vendors. |
| **Dependencies** | IMP-014 DONE (#45). |
| **Risk level** | Medium (vendor ToS, over-reading regime as a call). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/46 |
| **Lesson learned** | Merged to `main` (#46). `mm_flow` + `mm_macro` desk runners; envelope `regime` from YAML; EVENT_RISK + UNTRADEABLE_AT_SIZE Risk stubs. Per-desk Telegram fan-out and the Hive PLAYBOOK stayed out of 6b and are IMP-016. |

### IMP-016 — Phase 6c per-desk Telegram + PLAYBOOK + token budget/grounding

| Field | Value |
|---|---|
| **ID** | IMP-016 |
| **Priority** | P2 |
| **Type** | Delivery / desk product |
| **Desk** | Chief of Staff / Hive Coordinator |
| **Owner** | Don |
| **Problem** | 5e Telegram is a single Coordinator sink. 6a/6b publish per-desk envelopes on PG NOTIFY, but there is no desk→chat_id fan-out matrix, presentation layer, chart desk, or read-only inbound. The Hive PLAYBOOK (artifact ladder + Quant-owned trade math) and addendum 6c-0 (token budget + grounding + prompt versioning) apply from 6c onward. |
| **Evidence** | ADR 0003; ADR 0005; IMP-015 DONE #46; Principal-locked 6c DoD + Hive PLAYBOOK + addendum 6c-0. |
| **Proposed outcome** | Per-desk Telegram channels + presentation layer + chart desk + read-only inbound. Hive PLAYBOOK (artifact ladder + Quant-owned trade math + sizing/DD/invalidation/concentration/post-mortem/DQ%). LLM is WRITER/CRITIC only with hard token budgets and grounding locks. Bus stays Postgres NOTIFY. |
| **Definition of done** | Queue hygiene: IMP-015 DONE (#46). This item the only implementation thread. Plan [plans/IMP-016-phase6c-telegram-fanout.md](plans/IMP-016-phase6c-telegram-fanout.md). Per-desk fan-out + coord mirror same `content_hash`; presentation formatter; chart PNG filename=`content_hash`; inbound `/idea` `/gaps` `/halt` + unknown-uid silent drop; PLAYBOOK ladder; Quant `compute_trade_math` inherited hash; drawdown/cluster YAML; post-mortem gate; `config/llm/budgets.yaml` + `config/prompts/`; no-setup zero LLM; grounding locks; ledger; ADR 0006 + runbooks; README 6c; IMP-017 parked; import walls; no Redis; pytest never hits live Telegram/LLM; `uv run pytest` + lifecycle. |
| **Non-goals** | Live trading; signing; `live.yaml`; Redis; 6d listings/IPO; 6e scorecards automation; 6f strategy decay-watch remainder; reopening IMP-015 except queue hygiene; live LLM HTTP provider; paid Telegram/LLM SDKs. |
| **Dependencies** | IMP-015 DONE (#46). |
| **Risk level** | Medium (secrets, ToS, alert spam, LLM backfill). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/47 |
| **Lesson learned** | Merged to `main` (#47). Per-desk fan-out + PLAYBOOK ladder + 6c-0 token budget/grounding. Phase 6c-1 desk consolidation (11→5) is IMP-018. 6c-3 ladder/math stays on main via #47. |

### IMP-017 — Phase 6d listings / IPO desk

| Field | Value |
|---|---|
| **ID** | IMP-017 |
| **Priority** | P2 |
| **Type** | Desk product |
| **Desk** | Research (Investment Research) — listings sleeve; not a sixth desk |
| **Owner** | Ops (queue) / Research (when unparked) |
| **Problem** | 6c ships PLAYBOOK + Telegram fan-out. There is still no listings / IPO desk product. Principal 2026-09-19: 6d is blocked until 6c-1..6c-5 complete. |
| **Evidence** | ADR 0006; ADR 0007; IMP-016 DONE #47; Principal resume-build order 2026-09-19. |
| **Proposed outcome** | Listings / IPO product on the five-desk roster + 6c fan-out. Honest unavailable. Closed Quant verdicts. PLAYBOOK math inherited. |
| **Definition of done** | *(filled in the 6d PR)*. Plan stub: [plans/IMP-017-phase6d-listings-ipo.md](plans/IMP-017-phase6d-listings-ipo.md). Not started until 6c-1..6c-5 complete. |
| **Non-goals** | Live trading; signing; `live.yaml`; Redis; 6e–6f products; implementing listings in 6c-1. |
| **Dependencies** | IMP-018 (6c-1), IMP-019 (6c-2), IMP-016/6c-3 (#47 DONE), IMP-020 (6c-4), IMP-021 (6c-5) must be DONE. |
| **Risk level** | Medium (language, missing listing feeds). |
| **Status** | PARKED |
| **PR** | — |
| **Lesson learned** | Parked. Blocked until 6c-1..6c-5 complete per Principal order. Do not implement listings/IPO in this PR. |

### IMP-018 — Phase 6c-1 desk consolidation (11 → 5)

| Field | Value |
|---|---|
| **ID** | IMP-018 |
| **Priority** | P0 |
| **Type** | Desk operating model / cutover |
| **Desk** | Ops |
| **Owner** | Don/Ops |
| **Problem** | Publishing roster still has Phase-5/6a slugs (crypto, equities, flow, macro, skeptic, risk, coord-as-desk, chart, briefing). Principal hive is five desks. |
| **Evidence** | Principal resume-build order 2026-09-19; IMP-016 DONE #47. |
| **Proposed outcome** | Exactly five publishing desks: Intel, Research, Quant, IC/Risk (two gates), Ops. Coord/Don orchestration only. Delivery Ops-owned. |
| **Definition of done** | Queue OPEN incidents logged; 5-desk roster on main path; cadence/telegram/runners/tests/runbooks/charters updated; import-boundary statement-match test; `--no-send` fixtures; no 6c-2/4/5/6d. |
| **Non-goals** | 6c-2 naming; 6c-3 math (already #47); 6c-4 watchlist; 6c-5 delivery expansion; 6d listings; live/signing; Redis; new paid deps. |
| **Dependencies** | IMP-016 DONE (#47). |
| **Risk level** | Medium (cutover misses a sleeve). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/49 |
| **Lesson learned** | Merged to `main` (#49, 2026-09-18). Publishing roster is exactly five desks (`intel` `research` `quant` `ic_risk` `ops`). Coord/Don is orchestration only. Delivery is Ops-owned. Naming/display layer is IMP-019. Do not reopen the roster cutover. |

### IMP-019 — Phase 6c-2 naming layer

| Field | Value |
|---|---|
| **ID** | IMP-019 |
| **Priority** | P2 |
| **Type** | Presentation / naming |
| **Desk** | Ops |
| **Owner** | Don/Ops |
| **Problem** | 6c-1 cuts the roster. Display names / Principal-facing naming layer are still Phase-5 strings in places. |
| **Evidence** | Principal 6c-2; IMP-018 DONE #49. |
| **Proposed outcome** | Single naming module + `config/desks/naming.yaml` for the five-desk roster, PLAYBOOK artifact labels, Coord orchestration labels, and sleeve/gate titles. Used by artifacts, Telegram headers, mesh envelopes, CLI, and runbooks. |
| **Definition of done** | Canonical slugs + display names for intel/research/quant/ic_risk/ops (+ coord orchestration labels). Artifact type machine ids vs human labels (`DAILY_BIAS`…`STATE_CARD`). Unknown slug fails closed. Publishing paths resolve through `mm_common.naming`. Runbooks on five-desk vocabulary. Tests green. `--no-send`. No 6c-4/5/6d. |
| **Non-goals** | Reopening the 6c-1 roster; 6c-4 watchlist; 6c-5 delivery expansion; 6d listings; live/signing; Redis; new paid deps. |
| **Dependencies** | IMP-018 DONE (#49). |
| **Risk level** | Low. |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/51 |
| **Lesson learned** | Merged to `main` (#51, 2026-09-18). Canonical slugs + display names live in `mm_common.naming` / `config/desks/naming.yaml`. Unknown slug fails closed. Watchlist monitor is IMP-020. Do not reopen the naming layer. |

### IMP-020 — Phase 6c-4 watchlist monitor

| Field | Value |
|---|---|
| **ID** | IMP-020 |
| **Priority** | P2 |
| **Type** | Desk product |
| **Desk** | Research |
| **Owner** | Research |
| **Problem** | No standing Research product scans the Principal-locked universe (`in_universe` ∪ `watch_only`) each day with provenance. Membership still risks being misread as a call. |
| **Evidence** | Principal 6c-4; IMP-019 DONE #51; `config/universe.yaml`; PLAYBOOK `EDGE_SCAN` is idea-gated, not a locked-universe inventory. |
| **Proposed outcome** | Daily watchlist monitor on the five-desk roster. Deterministic artifact + `as_of_knowledge` + `content_hash`. Naming via `mm_common.naming`. Mesh envelope on `desk.research.output`. No trade calls. |
| **Definition of done** | Queue: IMP-019 DONE (#51). This item the only implementation thread. Plan [plans/IMP-020-phase6c4-watchlist.md](plans/IMP-020-phase6c4-watchlist.md). `lab watchlist scan --fixture --no-send` covers locked `in_universe` ∪ `watch_only`; `deferred_must_cut` excluded; monitor states `COVERED\|PARTIAL\|UNAVAILABLE`; degrade-never-invent; naming sleeve `watchlist` (not a sixth desk); Research mesh envelope; PLAYBOOK setup flag only (no inherited trade math); zero LLM on fixtures; `--no-send`; tests + runbook + ADR 0009; IMP-017/021 PARKED; OPEN incidents untouched. `uv run pytest` + import-boundary. |
| **Non-goals** | 6c-5 delivery expansion; 6d listings; universe promotion; live/signing; Redis; new paid data; new Telegram routes; live LLM HTTP. |
| **Dependencies** | IMP-018 DONE (#49). IMP-019 DONE (#51). 6c-3 math already on main (#47). |
| **Risk level** | Medium (language and membership can be misread as calls). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/52 |
| **Lesson learned** | Merged to `main` (#52, 2026-09-18). Daily `lab watchlist scan` covers locked `in_universe` ∪ `watch_only`. Monitor states COVERED\|PARTIAL\|UNAVAILABLE. Not a call. Telegram fan-out of the scan is IMP-021. Do not reopen the monitor. |

### IMP-021 — Phase 6c-5 delivery expansion

| Field | Value |
|---|---|
| **ID** | IMP-021 |
| **Priority** | P2 |
| **Type** | Delivery |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | 6c-1 only cuts Telegram routes over to five desks. Watchlist (IMP-020) has no Telegram path. Coordinator copy still reads like the publisher. |
| **Evidence** | Principal 6c-5; IMP-020 DONE #52; ADR 0009 (no new Telegram route in 6c-4); `docs/runbooks/telegram.md` leftover Coordinator-as-publisher language. |
| **Proposed outcome** | Ops-owned delivery expansion: naming-bound channel matrix, presentation headers, watchlist fan-out, Coord is not the publisher. |
| **Definition of done** | Queue: IMP-020 DONE (#52). This item the only implementation thread. Plan [plans/IMP-021-phase6c5-delivery.md](plans/IMP-021-phase6c5-delivery.md). Telegram yaml `owner`/`publisher` = `ops`; desks = naming `ROUTE_SLUGS`; unknown/retired slug fails closed. `lab deliver watchlist --fixture --no-send` presents IMP-020 scan (no invented ideas) + research/Ops mirror inheriting `content_hash`. Quiet hours, idempotency, rate limits, numeric `watchlist` threshold. Pytest never hits live Telegram. Runbooks + ADR 0010. IMP-017 PARKED. OPEN incidents untouched. `uv run pytest` + import-boundary. |
| **Non-goals** | 6d listings/IPO; live/signing/`live.yaml`; Redis; universe promotion; new paid data; waiving gates; closing OPEN incidents. |
| **Dependencies** | IMP-018 DONE (#49). IMP-019 DONE (#51). IMP-020 DONE (#52). 6c-3 math already on main (#47). |
| **Risk level** | Medium (secrets, ToS, alert spam). |
| **Status** | IN_REVIEW |
| **PR** | *(this PR)* |
| **Lesson learned** | *(fill at close)* |

### IMP-022 — Enable FRED (env) + ALFRED vintages (Treasury/Fed series)

| Field | Value |
|---|---|
| **ID** | IMP-022 |
| **Priority** | P1 |
| **Type** | Data / operator + later ingest (docs recommendation) |
| **Desk** | Ops (secrets) + Intel (series/vintages) |
| **Owner** | Ops (Principal for secrets) / Intel |
| **Problem** | Pulse, source-health, and macro still show FRED `missing_env`. Rates / curve / credit slots are NO DATA. ALFRED vintages are not used, so revisions would be look-ahead if a later adapter overwrote prints. |
| **Evidence** | OPEN incident `SRC-FRED-MISSING-ENV`; [ops/reports/source-health/2026-09-17.md](reports/source-health/2026-09-17.md); [ops/reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md) (adopt #1). FRED adapter already exists (`mm_ingest` / Pulse). |
| **Proposed outcome** | Principal sets `FRED_API_KEY` in gitignored env / CI secrets (Don does not decide secrets). Later (not this docs PR): ALFRED `realtime_start` / `realtime_end` so each vintage is a new observation; expand **public-domain / citation-required** series only (e.g. DGS10, DGS2, T10Y2Y). Telegram cites “via FRED®” + API disclaimer. Skip CBOE/S&P **Pre-approval required** series. |
| **Definition of done** | Key present locally/CI without ever appearing in git; source-health FRED row `credentials_present=yes` and not `missing_env` on an operator run; no prints/secrets in reports. Vintage ingest + series expansion only in a later implementation PR with tests. `SRC-FRED-MISSING-ENV` may close only after a real health run shows the env present. |
| **Non-goals** | Committing the key; scraping Stooq; VIXCLS/SP500 until copyright chip allows; adapters in the evaluation PR; 6c-1..6c-5 cutover; paid vendors; LLM training on FRED. |
| **Dependencies** | Principal secret. Do **not** take `IN_PROGRESS` while IMP-018 / 6c-1..6c-5 occupy the implementation thread. Evaluation: IMP-022–029 this PR. |
| **Risk level** | Low (env). Process: third-party FRED copyright; Telegram attribution. |
| **Status** | BACKLOG |
| **PR** | — (evaluation docs only) |
| **Lesson learned** | *(fill at close)* |

### IMP-023 — Binance market-data-only hosts (vision)

| Field | Value |
|---|---|
| **ID** | IMP-023 |
| **Priority** | P1 |
| **Type** | Data / ingest (docs recommendation) |
| **Desk** | Intel |
| **Owner** | Intel |
| **Problem** | Spot DQ uses `api.binance.com`, which returns HTTP 451 from Australia/cloud. `fapi.binance.com` is also 451. CVD and Binance history stay NO DATA. IMP-004 forbids scrape fallbacks. |
| **Evidence** | [ops/reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md) geo table: `api.binance.com` 451 vs `data-api.binance.vision` 200 (ping, ticker, aggTrades) and `data.binance.vision` bulk 200. Official FAQ: market-data-only URLs. |
| **Proposed outcome** | Point public Binance GETs at `https://data-api.binance.vision` (same `/api/v3/…` paths). Use `data.binance.vision` zip klines for Quant crypto history. Compute CVD from aggTrades (taker buy). HL remains perp structure. |
| **Definition of done** | Later implementation PR: config host change; 451 still classified `tos_or_blocked` if it returns; vision 200 path covered by tests/fixtures; no signed endpoints; no Bybit 403 workaround; source-health inventory lists the vision host. |
| **Non-goals** | Adapters in the evaluation PR; Bybit; CoinGlass scrape; live futures REST on `fapi`; 6c cutover. |
| **Dependencies** | Do not start while 6c-1..6c-5 is the implementation thread. |
| **Risk level** | Low (official host swap). Residual: UM live REST still geo-blocked. |
| **Status** | BACKLOG |
| **PR** | — (evaluation docs only) |
| **Lesson learned** | *(fill at close)* |

### IMP-024 — Official EDGAR + Treasury Fiscal Data + CB statistics / calendars

| Field | Value |
|---|---|
| **ID** | IMP-024 |
| **Priority** | P1 |
| **Type** | Data / filings + macro (docs recommendation) |
| **Desk** | Intel + Research |
| **Owner** | Intel (ingest) / Research (filings use) |
| **Problem** | Economic calendar is fixture-only. Filings, confirmed earnings, lockup text, and CB prints are unavailable. Paid calendar/news vendors fail Telegram ToS (Finnhub personal-use; Benzinga copyright). |
| **Evidence** | [ops/reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md) adopt #3. EDGAR submissions 200 with declared UA; ECB SDMX 200; Treasury Fiscal Data licence “free, without restriction… commercial or non-commercial”. |
| **Proposed outcome** | Lawful public ingest: `data.sec.gov` submissions + EDGAR indexes (10 rps, declared User-Agent); 8-K item 2.02 as **confirmed** earnings (estimates stay unavailable); S-1/424B4 lockup as text evidence; Treasury Fiscal Data; ECB SDMX + BoE/RBA official tables; BLS/BEA release calendars + ALFRED revisions as new observations. Gov/CB RSS only. |
| **Definition of done** | Later implementation PR: typed observations; PIT tests (file_date ≠ knowledge clock); missing feed → unavailable; no `api.nasdaq.com` scrape; no Yahoo RSS; import-boundary green. |
| **Non-goals** | Adapters in this PR; listings desk (IMP-017 PARKED); Street consensus; index-reconstitution licensed files; 6c cutover. |
| **Dependencies** | Do not start while 6c-1..6c-5 is the implementation thread. Complements IMP-022 (FRED). |
| **Risk level** | Medium (SEC fair-access blocks; PAC deletes). |
| **Status** | BACKLOG |
| **PR** | — (evaluation docs only) |
| **Lesson learned** | *(fill at close)* |

### IMP-025 — Alternative.me Fear & Greed (attribution)

| Field | Value |
|---|---|
| **ID** | IMP-025 |
| **Priority** | P3 |
| **Type** | Ops / sentiment slot (docs recommendation) |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | Ops asked for a Fear & Greed slot. No lawful feed is configured. Social vendors (Santiment, LunarCrush) fail ToS or cost. |
| **Evidence** | [ops/reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md). Probe `https://api.alternative.me/fng/` HTTP 200. Vendor permits commercial use with adjacent attribution. |
| **Proposed outcome** | Optional sentiment observation with adjacent attribution. Never a regime input, never a Quant verdict. GDELT stays optional with 429 backoff (Project, not Cloud). |
| **Definition of done** | Later implementation PR: fixture + live degrade; attribution string in render; missing → unavailable; pytest never hits live unnecessarily. |
| **Non-goals** | Santiment/LunarCrush; GDELT Cloud; adapters in this PR; 6c cutover. |
| **Dependencies** | Do not start while 6c-1..6c-5 is the implementation thread. |
| **Risk level** | Low. |
| **Status** | BACKLOG |
| **PR** | — (evaluation docs only) |
| **Lesson learned** | *(fill at close)* |

### IMP-026 — Trial Coinalyze API (aggregated liq / L-S)

| Field | Value |
|---|---|
| **ID** | IMP-026 |
| **Priority** | P2 |
| **Type** | Data / trial (docs recommendation) |
| **Desk** | Intel |
| **Owner** | Intel |
| **Problem** | Cross-venue liquidations and exchange long/short are NO DATA. HL covers HL-only liq flags. Binance futures REST is 451. CoinGlass commercial is $299/mo. |
| **Evidence** | [ops/reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md). Coinalyze API is free; 40 rpm; cite + link requested for public use; intraday history rolling ~1500–2000 points (weak PIT). |
| **Proposed outcome** | Time-boxed trial after IMP-023: store Coinalyze L/S and liq as **vendor-aggregated** observations with attribution. Not a backtest tape. If coverage fails, escalate to IMP-027 (Principal paid). |
| **Definition of done** | Later PR: key env-only; rate-limit budget; attribution; degrade-never-invent; PIT tests that rolling intraday is not treated as full history. |
| **Non-goals** | CoinGlass scrape; Bybit 403 workaround; adapters in this PR; 6c cutover. |
| **Dependencies** | IMP-023 preferred first. Do not start while 6c-1..6c-5 is the implementation thread. |
| **Risk level** | Medium (aggregator quality; Telegram citation). |
| **Status** | BACKLOG |
| **PR** | — (evaluation docs only) |
| **Lesson learned** | *(fill at close)* |

### IMP-027 — Trial CoinGlass Standard (paid, Principal)

| Field | Value |
|---|---|
| **ID** | IMP-027 |
| **Priority** | P3 |
| **Type** | Paid data / trial — **Principal decision** |
| **Desk** | Intel |
| **Owner** | Principal (contract) / Intel (trial design) |
| **Problem** | If Coinalyze cannot fill aggregated liq/L-S, CoinGlass is the named remaining vendor. Hobbyist $29 is personal-use only and is not lawful for Telegram fan-out. |
| **Evidence** | [ops/reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md). Commercial rights start at Standard **$299/mo**. Free dashboard scrape = reject. |
| **Proposed outcome** | Principal yes/no on Standard. If yes: env key, attribution, commercial-tier confirmation in writing, no Hobbyist/Startup. If no: leave liq heatmap unavailable. |
| **Definition of done** | Principal recorded decision. If adopted later: tests, degrade-never-invent, no scrape. |
| **Non-goals** | Buying in this PR; scraping; Velo/CCData (ToS reject); 6c cutover. |
| **Dependencies** | IMP-026 trial outcome. **Paid-data gate: Principal only.** Do not start while 6c-1..6c-5 is the implementation thread. |
| **Risk level** | Medium (cost, ToS tier, vendor PIT). |
| **Status** | BACKLOG |
| **PR** | — (evaluation docs only) |
| **Lesson learned** | *(fill at close)* |

### IMP-028 — Polygon entitlement audit (SI / options OI / not ES-NQ)

| Field | Value |
|---|---|
| **ID** | IMP-028 |
| **Priority** | P2 |
| **Type** | Data / existing-vendor audit — paid upgrade is **Principal decision** |
| **Desk** | Intel + Quant |
| **Owner** | Intel / Quant |
| **Problem** | Options OI and short interest were named gaps. Equities default is already Polygon. A new vendor is the wrong first move. True ES/NQ still need CME. |
| **Evidence** | [ops/reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md). Massive docs: short interest on **all stocks plans**; options chain/OI on **Options Starter $29/mo+** (not stocks); futures/indices are separate products + CME pass-through. |
| **Proposed outcome** | Document current `POLYGON_API_KEY` plan vs SI / ticker-events / options OI. Enable SI if already entitled. Options OI only if Principal pays Options Starter. Do **not** buy Polygon Futures to dodge CME. |
| **Definition of done** | Written entitlement matrix in a later PR or runbook; 403 stays `tos_or_blocked`; no invented OI; no ES/NQ label on SPY/QQQ unless Principal expands membership and the proxy is named as an ETF. |
| **Non-goals** | CME licence; Stooq scrape; adapters in this PR; 6c cutover. |
| **Dependencies** | Existing Polygon lock (IMP-010). Paid options/futures SKUs: Principal. Do not start while 6c-1..6c-5 is the implementation thread. |
| **Risk level** | Low–medium (plan 403s already handled). |
| **Status** | BACKLOG |
| **PR** | — (evaluation docs only) |
| **Lesson learned** | *(fill at close)* |

### IMP-029 — Trial EODHD (or Polygon Starter) for 5y daily + delisted

| Field | Value |
|---|---|
| **ID** | IMP-029 |
| **Priority** | P3 |
| **Type** | Quant history path — **Principal decision** if paid |
| **Desk** | Quant |
| **Owner** | Quant |
| **Problem** | Quant 5y daily and delisted retention are weak on Polygon Basic (~2y, 5 rpm). Survivorship bias if delisted names vanish. |
| **Evidence** | [ops/reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md). EODHD documents delisted lists + EOD; from ~$19.99/mo. Polygon Starter ~$29/mo keeps the locked vendor. Tiingo delisted incomplete. Alpha Vantage free RPM too low. |
| **Proposed outcome** | Prefer **Polygon Starter** if the only need is longer US history on locked names. Trial **EODHD** only if delisted retention is the Quant requirement. Telegram tables need a display-rights check before reprint. |
| **Definition of done** | Principal recorded yes/no. If trialled later: bulk CSV, delisted fixture, PIT `available_at`, no Yahoo. |
| **Non-goals** | Adapters in this PR; Databento/CME; 6c cutover. |
| **Dependencies** | IMP-028 (do not dual-pay Polygon Starter + EODHD without a reason). **Paid-data gate: Principal only.** Do not start while 6c-1..6c-5 is the implementation thread. |
| **Risk level** | Medium (second equity vendor vs Principal Polygon lock). |
| **Status** | BACKLOG |
| **PR** | — (evaluation docs only) |
| **Lesson learned** | *(fill at close)* |

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
| IMP-009 | Chief of Staff / Hive Coordinator | Don | DONE | [#40](https://github.com/ElChopa11/market-memory/pull/40) Phase 5a desk boundaries |
| IMP-010 | Data & Market Memory Desk | Don/Data | DONE | [#41](https://github.com/ElChopa11/market-memory/pull/41) Phase 5b Polygon + HL structure |
| IMP-011 | Quant & Market Structure Desk | Don/Quant | DONE | [#42](https://github.com/ElChopa11/market-memory/pull/42) Phase 5c quant factors |
| IMP-012 | Chief of Staff / Hive Coordinator | Don | DONE | [#43](https://github.com/ElChopa11/market-memory/pull/43) Phase 5d desk runners |
| IMP-013 | Chief of Staff / Hive Coordinator | Don | DONE | [#44](https://github.com/ElChopa11/market-memory/pull/44) Phase 5e Telegram |
| IMP-014 | Chief of Staff / Hive Coordinator | Don | DONE | [#45](https://github.com/ElChopa11/market-memory/pull/45) Phase 6a PG NOTIFY mesh |
| IMP-015 | Macro & Cross-Asset Desk + Data & Market Memory Desk | Don/Macro+Data | DONE | [#46](https://github.com/ElChopa11/market-memory/pull/46) Phase 6b flow+macro+regime |
| IMP-016 | Ops (was CoS) | Don | DONE | [#47](https://github.com/ElChopa11/market-memory/pull/47) Phase 6c PLAYBOOK + fan-out + 6c-0 |
| IMP-017 | Research (listings sleeve) | Ops/Research | PARKED | Phase 6d listings/IPO — blocked until 6c-1..6c-5 |
| IMP-018 | Ops | Don/Ops | DONE | [#49](https://github.com/ElChopa11/market-memory/pull/49) Phase 6c-1 desk consolidation 11→5 |
| IMP-019 | Ops | Don/Ops | DONE | [#51](https://github.com/ElChopa11/market-memory/pull/51) Phase 6c-2 naming layer |
| IMP-020 | Research | Research | DONE | [#52](https://github.com/ElChopa11/market-memory/pull/52) Phase 6c-4 watchlist monitor |
| IMP-021 | Ops | Ops | IN_REVIEW | Phase 6c-5 delivery expansion — this PR |
| IMP-022 | Ops + Intel | Ops (Principal for secrets) / Intel | BACKLOG | Adopt FRED env + ALFRED — evaluation 2026-09-18; do not start during 6c-1..6c-5 |
| IMP-023 | Intel | Intel | BACKLOG | Adopt Binance vision hosts — evaluation 2026-09-18 |
| IMP-024 | Intel + Research | Intel / Research | BACKLOG | Adopt EDGAR + Treasury + CB calendars — evaluation 2026-09-18 |
| IMP-025 | Ops | Ops | BACKLOG | Adopt Alternative.me Fear & Greed — evaluation 2026-09-18 |
| IMP-026 | Intel | Intel | BACKLOG | Trial Coinalyze (free, cite) — evaluation 2026-09-18 |
| IMP-027 | Intel | Principal / Intel | BACKLOG | Trial CoinGlass Standard **$299/mo — Principal paid** |
| IMP-028 | Intel + Quant | Intel / Quant | BACKLOG | Polygon SI / options OI audit; paid SKUs **Principal** |
| IMP-029 | Quant | Quant | BACKLOG | Trial EODHD or Polygon Starter for 5y/delisted — **Principal paid** |

`IN_PROGRESS` count: **0**. IMP-000–IMP-016 and IMP-018–IMP-020 are `DONE`. IMP-021 is `IN_REVIEW` (this PR). IMP-017 is `PARKED`. IMP-022–IMP-029 are `BACKLOG` (source-evaluation 2026-09-18; no adapters). OPEN incidents: SCHED-001, BRIEF-TAG-20260918, SRC-STOOQ-404, SRC-FRED-MISSING-ENV (not closed).

| ID | Desk | Owner | Status | Notes |
|---|---|---|---|---|
| SCHED-001 | Ops | Ops | OPEN | Sydney 08:00 digest never fired |
| BRIEF-TAG-20260918 | Ops / Quant scorecard | Ops/Quant | OPEN | 18 Sep pack ~90m pre-open vs 30m anchor |
| SRC-STOOQ-404 | Intel | Intel | OPEN | stooq http_404, 2 consecutive; evaluation 2026-09-18 rejects scrape — lawful proxy is not ES/NQ futures |
| SRC-FRED-MISSING-ENV | Ops | Ops (Principal for secrets) | OPEN | fred missing_env; Don does not decide secrets; adopt path is IMP-022 |


---

## Map: existing capabilities → desks

Short form. Full table: [desk-charters.md — capability map](desk-charters.md#capability-map-repo--desk).

| Area | Desk | Owner (accountable) |
|---|---|---|
| Market Memory, ingest, provenance, schemas, PIT, flow, macro, Pulse | Intel (Market Intelligence) | Intel |
| Crypto / equity / chart research cards and screens | Research (Investment Research) | Research |
| Quant Review Board / cards / factor math | Quant | Quant |
| Skeptic gate + Risk gate | IC/Risk (two gates, not two desks) | IC/Risk |
| Queue, delivery, pack assemble | Ops | Ops (Don/Coord orchestrates; not a publishing desk) |
| Paper ledger `lab paper` | Principal-gated lab control | Principal enables; Ops operates CLI |
| `packages/execution`, `apps/execution-service` | Execution & Fund Ops | **Dormant / future only** |
| Fund ledger, tax, investor reporting | Execution & Fund Ops | **Absent / future only** |

## Gaps (not yet queued)

These are identified so they are not silently treated as existing desks. They are **not** `IN_PROGRESS` and are not seeded as IMP items until Chief of Staff intakes them.

| Gap | Desk that would own | Why not queued now |
|---|---|---|
| Equity-feed ingest (Polygon); HL structure | Data & Market Memory Desk | IMP-010 DONE (#41) |
| `risk-review.md` + portfolio exposure report | Risk (independent veto) | Risk *service* is out of Phase 4 |
| Quant pack rewrite (templates / pack workflow) | Quant & Market Structure Desk | IMP-001 plan placeholder; **not** assigned IMP-003 (source-health took that ID) |
| Cross-asset regime note cadence | Macro & Cross-Asset Desk | IMP-015 DONE (#46) |
| Execution order-state / recon | Execution & Fund Ops | Future only; Principal enablement required |
| Fund P&L / investor reporting | Execution & Fund Ops | Future only; legal approval required |

Pulse source hardening (Stooq timeout/ToS class; FRED key ops) was a Gap; it is now **IMP-004 DONE** (#34).

Historical “active calls” language debt was a Gap; it is now **IMP-005 DONE** (#35). Do not reopen.

Post-IPO reclaim screen product was a Gap; it is now **IMP-006 DONE** (#36). Do not reopen.

Dedicated crypto / equity thesis-card templates were a Gap; they are now **IMP-007 DONE** (#37). Generic `thesis.md` stays the lifecycle spine. Do not reopen.

Quant RESEARCH_PRIORITY pass on locked membership was a Gap; it is now **IMP-008 DONE** (#38). Screenshot/TV board remains IMP-001. Do not treat membership as a Quant verdict.

Phase 5 desk/delivery architecture is **IMP-009 DONE** (#40). Polygon equities + HL structure is **IMP-010 DONE** (#41). Quant factor library is **IMP-011 DONE** (#42). Desk runners are **IMP-012 DONE** (#43). Telegram delivery is **IMP-013 DONE** (#44). Phase 6a PG NOTIFY mesh is **IMP-014 DONE** (#45). Phase 6b flow+macro+regime is **IMP-015 DONE** (#46). Phase 6c PLAYBOOK + fan-out is **IMP-016 DONE** (#47). Phase 6c-1 five-desk roster is **IMP-018 DONE** (#49). Phase 6c-2 naming layer is **IMP-019 DONE** (#51). Phase 6c-4 watchlist monitor is **IMP-020 DONE** (#52). Phase 6c-5 delivery expansion is **IMP-021 IN_REVIEW** (this PR). Phase 6d listings/IPO is **IMP-017 PARKED** until 6c-1..6c-5 complete. Do not start 6d in this PR.

Source evaluation 2026-09-18 is **docs only** ([reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md)). Adopt/trial intake is **IMP-022–IMP-029 BACKLOG**. No adapters in the evaluation PR. Do not take those items `IN_PROGRESS` while 6c-1..6c-5 occupy the implementation thread.

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
- IMP-009 merged as #40 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-010.
- IMP-010 merged as #41 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-011.
- IMP-011 merged as #42 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-012.
- IMP-012 merged as #43 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-013.
- IMP-013 merged as #44 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-014.
- IMP-014 merged as #45 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-015.
- IMP-015 merged as #46 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-016.
- IMP-016 merged as #47 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-018.
- IMP-018 merged as #49 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-019.
- IMP-019 merged as #51 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-020.
- IMP-020 merged as #52 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-021.
- IMP-021 intakes Phase 6c-5 Ops-owned delivery expansion per Principal resume-build (ops / Operation Lunch Money). IMP-020 DONE (#52). IMP-017 remains PARKED until 6c-1..6c-5 complete. OPEN incidents untouched. Bus = Postgres NOTIFY, no Redis. Single-threaded: no item remains `IN_PROGRESS` (`IN_REVIEW` pending merge).
- Source evaluation 2026-09-18 (docs-only) intakes IMP-022–IMP-029 as `BACKLOG` adopt/trial recommendations. Does not modify IMP-018/6c-1 cutover, does not close OPEN incidents, does not add adapters or keys. Paid items (IMP-027 CoinGlass Standard, IMP-028 paid Polygon SKUs, IMP-029 EODHD/Starter) are Principal decision.
