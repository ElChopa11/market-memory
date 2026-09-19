# Improvement queue

Single continuous-improvement list for Market Memory. The lab runs a **desk model** ([desk-charters.md](desk-charters.md)): every work item belongs to one desk and has **one accountable owner**. Chief of Staff (Don) maintains this file, assigns desks, and enforces **single-threaded implementation** — at most one item in `IN_PROGRESS`. Ready work is parked, not started in parallel.

This queue is the operating system, not an investment book. It does not authorise trades, enable execution, or waive Skeptic / Principal gates ([decision-rights.md](decision-rights.md)).

## Operating rules

1. **Intake** only through this file. Research cards under `research/queue/` are evidence or artifacts, not a second backlog.
2. **One `IN_PROGRESS` implementation item.** Review (`IN_REVIEW`) of docs is allowed while implementation stays parked.
3. **No duplicate research.** If an artifact already answers the question, close or merge the item with a lesson.
4. **Reusable artifacts.** Prefer templates, schema records, and desk products over one-off commentary.
5. Status vocabulary: `OPEN` (ops incident, not closed) → `BACKLOG` → `READY` → `IN_PROGRESS` → `IN_REVIEW` → `DONE` | `PARKED` | `REJECTED` | `INTAKE_ONLY`. `OPEN` items are logged incidents; they are **not** closed and do not occupy the single `IN_PROGRESS` implementation slot. `INTAKE_ONLY` is a blocked shelf (specs only) and does not occupy the slot.
6. **Incident closure (Principal-locked 2026-09-19):** `OPEN` → `ELIGIBLE` → `CLOSED` (must cite `run_id`) | `RETIRED`. `--no-db` is **ELIGIBLE only**. A helper must not auto-close. SRC-STOOQ-404 stays `OPEN` (`http_404`).

## Principal L2 sprint (intake 2026-09-19)

Order of work. This PR is **P0 only**. Do not start P1/P2/P3 here.

| Priority | Work | Status this PR |
|---|---|---|
| **P0** | DM-only live path. Hive group stays frozen. SCHED-001 stays OPEN. | IMP-047 this thread (IMP-046 DONE #72; IMP-042 DONE #68 — do not touch miss detector). IMP-049 prompt read-back, IMP-050 per-channel `send_enabled`, and IMP-051 publisher inventory are BACKLOG — do not build. |
| **P1** | Phase-1 Memory rates — expand if #66 is fixture-only | IMP-040 DONE (#66). Expansion is later. |
| **P2** | Instance ledger | not this PR |
| **P3** | Truth-in-repo (source-health regen / desk naming / Telegram inventory). `SRC-object_store` is a named OPEN **DOWN SERVICE** on the services/infrastructure list — not a missing-env credential item. | not this PR |

Candidate cards stay `INTAKE_ONLY`. No study compute. No paid data. No new desks. No universe promotions. Canaries run outside this PR.

## Required fields (every item)

Each item must include at least: **ID**, **Priority**, **Type**, **Desk**, **Owner**, **Problem**, **Evidence**, **Proposed outcome**, **Definition of done**, **Non-goals**, **Dependencies**, **Risk level**, **Status**, **PR**, **Lesson learned**.

---

## Active / seeded items

### SCHED-001 — Sydney 08:00 digest never fired

| Field | Value |
|---|---|
| **ID** | SCHED-001 |
| **Priority** | P0 |
| **Type** | Scheduler reliability |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | Sydney 08:00 digest was configured and never fired. Weekday windows existed. NY-cron sibling briefs completed. Root cause still unexplained. |
| **Evidence** | Routine `sydney-morning-digest-8am` NEVER RUN. Report: [reports/scheduler/2026-09-19-sched-001-root-cause.md](reports/scheduler/2026-09-19-sched-001-root-cause.md). Lab yaml never contained a Sydney 08:00 job; no GitHub cron; no compose worker. Grok Bot is the only cited executor. Do **not** close on “no window yet”. Do not treat 06:30 / Fri 17:00 calendar hypothesis as this ticket. |
| **Proposed outcome** | Miss detector escalates closed-window-without-completion (the check that would have caught this). Verified on-anchor fire still required to close. |
| **Definition of done** | Root cause recorded (unexplained is an allowed cause). Miss sweep shipped. Job either fires on a verified Sydney 08:00 (or successor) window or the miss stays OPEN with a standing control. Still OPEN until a verified on-anchor fire. |
| **Non-goals** | Closing on config-exists-therefore-done; closing on pending/next-window; live trading; P1 base-rate expansion; canaries. |
| **Dependencies** | IMP-042 (miss detector). |
| **Risk level** | High (missed Principal digest; clock is not true). |
| **Status** | OPEN |
| **PR** | *(IMP-042 this PR — evidence only; does not close)* |
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
| **Evidence** | Config `config/schedules/market-pulse.yaml` `pre_open.local_time: "08:00"` America/New_York; Principal 30m-pre-open anchor is 09:00 NY / 23:00 Syd. The ~22:02 AEST fire is also **ungated** (pre-Hybrid Telegram; see `TG-UNGATED-PRE-HYBRID`). Scorecard mismatch and ungated are separate tags. |
| **Proposed outcome** | Tag that artifact so scorecards do not compare like-for-like vs 30m-pre-open packs. |
| **Definition of done** | Artifact tagged; scorecard docs note the 90m vs 30m mismatch; item stays OPEN until operators verify no 30m-golden misuse. Tag applied in IMP-030 `config/scorecards/tags.yaml`; incident remains OPEN. |
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

### SRC-FRED-MISSING-ENV — environment-propagation (not a key-absent close)

| Field | Value |
|---|---|
| **ID** | SRC-FRED-MISSING-ENV |
| **Priority** | P1 |
| **Type** | Environment-propagation / run env |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | Root cause is **environment-propagation**, not a simple missing key. Secrets-card / box config for `FRED_API_KEY` may be present while a failing run executes without that process env (config present, run env absent). Earlier `missing_env` symptoms are that class — do not close as key-absent. |
| **Evidence** | 2026-09-19 environment audit (Don): `FRED_API_KEY` was present on the Secrets card **and** process env at audit time. Prior CLOSED persist note (history retained, not erased): run_id `fred-fullstack-20260919-101938-aest`; pack [ops/reports/incident-closures/20260919-101938-aest-fred-fullstack-close.json](reports/incident-closures/20260919-101938-aest-fred-fullstack-close.json) (`secrets_printed: false`). Record correction: [ops/reports/incident-closures/20260919-environment-audit-record-correction.md](reports/incident-closures/20260919-environment-audit-record-correction.md). `--no-db` remains ELIGIBLE only for the IMP-022 persist criterion. |
| **Proposed outcome** | FRED-using runs inherit box/process env, or fail as an explicit propagation miss — not a key-absent close. Do not close on “key exists on the Secrets card.” IMP-022 persist path stays DONE. |
| **Definition of done** | Stays `OPEN` until operators show FRED-using runs inherit `FRED_API_KEY` from the box (or a documented propagation control). Persist run_id `fred-fullstack-20260919-101938-aest` is evidence that a keyed persist path exists; it is **not** a simple key-absent close. |
| **Non-goals** | Committing the key; treating IMP-022 DONE as this incident’s key-absent close; inventing FRED prints; closing on `--no-db`; scheduler code; equity work. |
| **Dependencies** | IMP-022 DONE (persist path; run_id cited above). |
| **Risk level** | Medium (honest unavailable mis-attributed to a missing key). |
| **Status** | OPEN |
| **PR** | Reopened 2026-09-19 (Principal record correction). Prior close [#62](https://github.com/ElChopa11/market-memory/pull/62) / pack kept as history; ELIGIBLE path [#60](https://github.com/ElChopa11/market-memory/pull/60). |
| **Lesson learned** | Closed on full-stack persist run_id `fred-fullstack-20260919-101938-aest` (not `--no-db`) — **that close is retained as persist history, then reopened under environment-propagation.** postgres_attached=true, created_rows=5, Pulse US10Y=4.94 via FRED, source-health fred=ok on that run. `--no-db` remains ELIGIBLE only. |

### SRC-OBJECT-STORE — object_store DOWN SERVICE (MinIO :9000)

| Field | Value |
|---|---|
| **ID** | SRC-OBJECT-STORE |
| **Priority** | P2 |
| **Type** | Services / infrastructure (DOWN SERVICE) |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | Object store is a **DOWN SERVICE**: MinIO `:9000` connection refused, no container. This is **not** a missing credential. `MINIO_*` keys may still be present as local defaults while the service is down. Source-health 2026-09-17 `missing_env` / credentials_present=no misreads a down daemon. Alias: `SRC-object_store` / source id `object_store`. |
| **Evidence** | Compose `minio` publishes `:9000` (`market-memory-minio`); no container → connection refused. 2026-09-19 environment audit (Don) + [ops/reports/incident-closures/20260919-environment-audit-record-correction.md](reports/incident-closures/20260919-environment-audit-record-correction.md). Last committed health [`ops/reports/source-health/2026-09-17.md`](reports/source-health/2026-09-17.md) labelled missing_env — corrected here. |
| **Proposed outcome** | Stay on the **services / infrastructure OPEN** list (not a missing-env credentials list). Bring MinIO up or document an explicit filesystem/none backend. Do not close by setting `MINIO_*`. |
| **Definition of done** | `:9000` reachable (or an operator-chosen durable backend) and a down daemon is not filed as missing credentials. Stays OPEN until then. |
| **Non-goals** | Treating compose/`.env.example` defaults as a credential incident; changing ingest; scheduler code; equity work. |
| **Dependencies** | None (infra). P3 named `SRC-object_store`; this is the logged OPEN incident, not an implementation thread. |
| **Risk level** | Medium (raw-object persist / charts fail closed). |
| **Status** | OPEN |
| **PR** | — |
| **Lesson learned** | *(open — DOWN SERVICE, not missing_env)* |

### TG-UNGATED-PRE-HYBRID — pre-Hybrid Telegram is ungated

| Field | Value |
|---|---|
| **ID** | TG-UNGATED-PRE-HYBRID |
| **Priority** | P2 |
| **Type** | Delivery / pipeline honesty |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | Every Telegram message published **before the Hybrid architecture change** is **ungated**: it did not pass lab delivery controls and must not be treated as evidence of a working pipeline. Hybrid = Ops-owned gated Telegram (IMP-013/018/021). Grok Bot and Coord-as-publisher fires sit outside that path. |
| **Evidence** | Policy note [ops/reports/20260919-telegram-ungated-pre-hybrid.md](reports/20260919-telegram-ungated-pre-hybrid.md). **Known fires (not an archive):** 18 Sep ~22:02 AEST pre-market (also BRIEF-TAG-20260918); 19 Sep 00:03 cash-open; Coord lines from the publisher audit. Quiet hours 22:00–07:00 Sydney; 22:02 and 00:03 did not pass those controls. Do not invent a full Telegram export. |
| **Proposed outcome** | Standing **ungated** tag on the pre-Hybrid class. Operators must not cite those fires as gated-pipeline proof. Later gated `lab deliver` sends (thresholds + Ops publisher) are a different class. |
| **Definition of done** | Policy recorded on this queue + ops note. Known fires listed. Incident stays OPEN until a gated send is the SoT for “pipeline works” (this item does not close SCHED-001 or BRIEF-TAG). |
| **Non-goals** | Inventing a Telegram archive; treating Grok Bot fire as `lab deliver` success; closing SCHED-001; live send; feature code. |
| **Dependencies** | None (record). IMP-013/018/021 DONE are the Hybrid cut, not a close of this tag. |
| **Risk level** | Medium (false confidence that delivery/gates work). |
| **Status** | OPEN |
| **PR** | — |
| **Lesson learned** | *(open — ungated ≠ working pipeline)* |

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
| **Definition of done** | Queue: IMP-021 DONE (#53). This item the only implementation thread. Plan [plans/IMP-017-phase6d-listings-ipo.md](plans/IMP-017-phase6d-listings-ipo.md). Research-owned `lab listings scan --fixture --no-send` (not a sixth desk); Ops `lab deliver listings` inherits `content_hash`; naming sleeve `listings`; PIT `as_of_knowledge`; never invent prints; closed Quant verdicts; inherit `trade_math_hash`; IC gates required; no universe promotion; `--no-send`; zero LLM on fixtures; OPEN incidents untouched; 6e/6f later. `uv run pytest` + import-boundary. |
| **Non-goals** | Live trading; signing; `live.yaml`; Redis; 6e–6f products; universe promotion; paid listing feeds; closing OPEN incidents; reopening the five-desk roster. |
| **Dependencies** | IMP-018 DONE (#49). IMP-019 DONE (#51). IMP-016/6c-3 DONE (#47). IMP-020 DONE (#52). IMP-021 DONE (#53). |
| **Risk level** | Medium (language, missing listing feeds). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/54 |
| **Lesson learned** | Merged to `main` (#54, 2026-09-18). Listings / IPO is a Research sleeve, not a sixth desk. `lab listings scan` + Ops `lab deliver listings` inherit `content_hash`. Screen-only; no universe promotion. Scorecards are IMP-030. Do not reopen listings as a sixth desk. |

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
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/53 |
| **Lesson learned** | Merged to `main` (#53, 2026-09-18). Ops-owned watchlist fan-out inherits `content_hash`. Coord is not the publisher. Listings Telegram cut is IMP-017. Do not reopen the 6c-5 expansion. |

### IMP-022 — Close SRC-FRED-MISSING-ENV full-stack (Postgres + provenance + published value)

| Field | Value |
|---|---|
| **ID** | IMP-022 |
| **Priority** | P0 |
| **Type** | Data / ingest (Principal FREE SOURCE PRIORITY #1, 2026-09-19) |
| **Desk** | Intel (ingest) + Ops (env) |
| **Owner** | Intel / Ops |
| **Problem** | Pulse, source-health, and macro still show FRED `missing_env` or `--no-db` dry-run only. Full-stack close needs Postgres attached, rows landed, provenance ids, and a value in a published artifact. Key is operator-env `FRED_API_KEY` (never git). |
| **Evidence** | Persist close pack (history retained): run_id `fred-fullstack-20260919-101938-aest`; [ops/reports/incident-closures/20260919-101938-aest-fred-fullstack-close.json](reports/incident-closures/20260919-101938-aest-fred-fullstack-close.json). Incident `SRC-FRED-MISSING-ENV` was later **reopened** under environment-propagation (Don 2026-09-19 audit) — this IMP stays DONE. Principal FREE SOURCE PRIORITY 2026-09-19; [ops/reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md) adopt #1. Adapter already exists (`mm_ingest.macro` / Pulse). `licence_verdict: ok_gov` on the FRED adapter. |
| **Proposed outcome** | Operator path: env key + `lab ingest` (not `--no-db`) persists FRED observations, writes provenance ids, and a published artifact may show the value (ok_gov). `--no-db` stays ELIGIBLE. ALFRED vintages later. Skip CBOE/S&P Pre-approval series. |
| **Definition of done** | Queue: IMP-033 DONE (#59). Plan [plans/IMP-022-fred-fullstack.md](plans/IMP-022-fred-fullstack.md). Fixture `--no-db` → `fred_stack.closure=ELIGIBLE` with value + `claim_hash` provenance; never `CLOSED`. Persist helper exists (`persist_envelopes` + `run_fred_stack`). `SRC-FRED-MISSING-ENV` CLOSED only after an operator cites a persist `run_id`. No secrets in git. Tests + import-boundary. Met: run_id `fred-fullstack-20260919-101938-aest`. |
| **Non-goals** | Committing the key; closing the incident on `--no-db`; scraping Stooq; VIXCLS/SP500 until copyright chip allows; paid vendors; LLM training on FRED; `live.yaml` / signing / Redis. |
| **Dependencies** | IMP-033 DONE (#59). IMP-034 DONE (#60). Principal env on the operator box. |
| **Risk level** | Low (env). Process: third-party FRED copyright; Telegram attribution. |
| **Status** | DONE |
| **PR** | operator full-stack close 2026-09-19 (run_id `fred-fullstack-20260919-101938-aest`); ELIGIBLE path [#60](https://github.com/ElChopa11/market-memory/pull/60) |
| **Lesson learned** | Closed SRC-FRED-MISSING-ENV on persist run_id `fred-fullstack-20260919-101938-aest` (postgres_attached=true, no_db=false, 5 observation_ids, Pulse US10Y=4.94 source=fred, source-health fred=ok). `--no-db` is still ELIGIBLE only. ALFRED vintages remain later. Next free-source thread is IMP-024 EDGAR. Principal record correction 2026-09-19: the incident is **OPEN** again under environment-propagation; this IMP stays DONE. |

### IMP-023 — Test data.binance.vision from AU (separate from geo-blocked API)

| Field | Value |
|---|---|
| **ID** | IMP-023 |
| **Priority** | P1 |
| **Type** | Data / ingest (Principal FREE SOURCE PRIORITY #4) |
| **Desk** | Intel |
| **Owner** | Intel |
| **Problem** | Spot DQ uses `api.binance.com`, which returns HTTP 451 from Australia/cloud. `fapi.binance.com` is also 451. CVD and Binance history stay NO DATA. Vision hosts must be tested from AU separately from the geo-blocked API. |
| **Evidence** | Principal FREE SOURCE PRIORITY 2026-09-19 item 4; [ops/reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md) geo table: `api.binance.com` 451 vs `data-api.binance.vision` / `data.binance.vision` 200. `licence_verdict: ok_attr` on `binance.vision`. |
| **Proposed outcome** | From AU: probe `data.binance.vision` / `data-api.binance.vision` independently of `api.binance.com`. Then point public GETs at the vision host. No signed endpoints. 451 stays `tos_or_blocked`. |
| **Definition of done** | AU probe recorded; config host change; 451 still classified; vision 200 path covered by tests/fixtures; source-health lists the vision host; no Bybit workaround. |
| **Non-goals** | Starting while IMP-024 occupies IN_PROGRESS; Bybit; CoinGlass scrape; live futures REST on `fapi`; closing SRC-STOOQ-404. |
| **Dependencies** | IMP-022 DONE (run_id `fred-fullstack-20260919-101938-aest`). Parked until IMP-024 leaves the slot. |
| **Risk level** | Low (official host swap). Residual: UM live REST still geo-blocked. |
| **Status** | READY |
| **PR** | — |
| **Lesson learned** | *(fill at close)* |

### IMP-024 — Wire SEC EDGAR (filings / IPO / lockups; CBRS+SPCX)

| Field | Value |
|---|---|
| **ID** | IMP-024 |
| **Priority** | P1 |
| **Type** | Data / filings (Principal FREE SOURCE PRIORITY #2) |
| **Desk** | Intel + Research |
| **Owner** | Intel (adapter + store) / Research (filings use) |
| **Problem** | Intel already recorded EDGAR dates for CBRS + SPCX in `monitor.yaml`. There is no EDGAR adapter or store. Filings / IPO / lockup text stay config-only. |
| **Evidence** | Principal FREE SOURCE PRIORITY 2026-09-19 item 2; `config/watchlist/monitor.yaml` `lockup_watch` (CBRS CIK 2021728, SPCX CIK 1181412); [ops/reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md). `licence_verdict: ok_gov` on `edgar` (free, no key). |
| **Proposed outcome** | Wire `data.sec.gov` adapter + store. Confirm CBRS+SPCX lockup from prospectus (already dated). 8-K 2.02 = confirmed earnings path on submissions. 10 rps, declared User-Agent. Treasury.gov is IMP-035 (do not bundle). |
| **Definition of done** | Queue: IMP-022 DONE (run_id `fred-fullstack-20260919-101938-aest`). Plan [plans/IMP-024-edgar-wire.md](plans/IMP-024-edgar-wire.md). Adapter + typed observations; PIT (`file_date` ≠ knowledge clock); CBRS+SPCX lockup persisted with `as_of_knowledge` + 424B4 provenance; `assume_180d: false`; `licence_verdict: ok_gov` (accurate redistributable_official); `--no-db` = ELIGIBLE only; Postgres persist via `run_edgar_stack`; missing feed → unavailable; no `api.nasdaq.com` scrape; no Yahoo RSS. OPEN Stooq untouched. Tests + import-boundary. |
| **Non-goals** | Closing SRC-STOOQ-404; Street consensus; Finnhub estimates; listings as a sixth desk; `live.yaml`; Treasury (IMP-035). |
| **Dependencies** | IMP-022 DONE (run_id `fred-fullstack-20260919-101938-aest`). IMP-017 DONE (#54) listings sleeve. IMP-034 licence schema (#60). |
| **Risk level** | Medium (SEC fair-access blocks; PAC deletes). |
| **Status** | DONE |
| **PR** | [#63](https://github.com/ElChopa11/market-memory/pull/63) |
| **Lesson learned** | Adapter + persist landed on #63 (CBRS/SPCX lockup observations, `assume_180d: false`). `--no-db` remains ELIGIBLE only. Slot freed for IMP-040 Phase 1 base rates. |

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

### IMP-030 — Phase 6e scorecards + queue automation

| Field | Value |
|---|---|
| **ID** | IMP-030 |
| **Priority** | P2 |
| **Type** | Desk product / Ops hygiene |
| **Desk** | Quant (score math) + Ops (queue + delivery) |
| **Owner** | Quant / Ops |
| **Problem** | Packs were compared by eye. BRIEF-TAG-20260918 (90m vs 30m pre-open) can be mis-scored as like-for-like. The single-threaded READY→IN_PROGRESS rule was documentation-only. |
| **Evidence** | ADR 0011; IMP-017 DONE #54; OPEN incident BRIEF-TAG-20260918; Principal Phase 6e lock (scorecards + queue automation; 6f decay-watch later). |
| **Proposed outcome** | Like-for-like pack scorecard with provenance. Tag incomparable artifacts. Queue hygiene helper enforces one IMP-* IN_PROGRESS. Decay inputs stubbed toward 6f. |
| **Definition of done** | Queue: IMP-017 DONE (#54). This item the only implementation thread. Plan [plans/IMP-030-phase6e-scorecards.md](plans/IMP-030-phase6e-scorecards.md). Quant-owned `lab scorecard compare --fixture --no-send` (not a sixth desk); Ops `lab deliver scorecard` inherits `content_hash`; naming sleeve `scorecard` → quant; like-for-like keys product/schedule_anchor/universe; BRIEF-TAG tagged and not scored as 30m; `lab queue check` / `scripts/check_queue.py` single-threaded READY→IN_PROGRESS aid (no auto-merge, no gate waiver); decay stub `watch_enabled: false`; IMP-031 PARKED; OPEN incidents untouched; `--no-send`; zero LLM on fixtures. `uv run pytest` + import-boundary. |
| **Non-goals** | Live trading; signing; `live.yaml`; Redis; full 6f decay-watch; universe promotion; auto-merge; auto-waive Skeptic/Risk; closing OPEN incidents; reopening the five-desk roster. |
| **Dependencies** | IMP-017 DONE (#54). Five-desk naming (IMP-019). Ops delivery (IMP-021). |
| **Risk level** | Low–medium (false like-for-like; treating a score as a call). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/55 |
| **Lesson learned** | Merged to `main` (#55, 2026-09-18). Like-for-like pack scorecards; BRIEF-TAG-20260918 stays `NOT_COMPARABLE`. Queue helper does not auto-merge or waive gates. Decay inputs were stubbed; full prompt-hash watch is IMP-031. |

### IMP-031 — Phase 6f strategy decay-watch

| Field | Value |
|---|---|
| **ID** | IMP-031 |
| **Priority** | P2 |
| **Type** | Quant / process |
| **Desk** | Quant |
| **Owner** | Quant |
| **Problem** | 6e records prompt SHA-256 inputs with `watch_enabled: false`. There is still no standing watch that alerts when a versioned prompt or strategy hash drifts. |
| **Evidence** | ADR 0012; IMP-030 DONE #55; `config/scorecards/decay.yaml`; Principal 6f remainder. |
| **Proposed outcome** | Prompt-hash strategy decay-watch on the five-desk roster. Honest unavailable. No auto-disable without Principal. |
| **Definition of done** | Queue: IMP-030 DONE (#55). This item the only implementation thread. Plan [plans/IMP-031-phase6f-decay-watch.md](plans/IMP-031-phase6f-decay-watch.md). Quant-owned `lab decay watch --fixture --no-send` (not a sixth desk); Ops `lab deliver decay` inherits `content_hash`; naming sleeve `decay` → quant; unknown slug fails closed; mismatch → NOTIFY `desk.quant.alert` + queue signal without writing the queue or waiving gates; prompt hashes pinned in `config/scorecards/decay.yaml`; scorecard `NOT_COMPARABLE` stays tagged (no invented numbers); `--no-send`; zero LLM on fixtures; OPEN incidents untouched. `uv run pytest` + import-boundary. |
| **Non-goals** | Live trading; signing; `live.yaml`; Redis; universe promotion; auto-merge; auto-waive Skeptic/Risk; auto-disable prompts; closing OPEN incidents; reopening the five-desk roster; inventing like-for-like scores for tagged incomparable packs. |
| **Dependencies** | IMP-030 DONE (#55). |
| **Risk level** | Medium (false decay alerts; prompt drift). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/56 |
| **Lesson learned** | Merged to `main` (#56, 2026-09-18). `lab decay watch` hashes versioned prompts + listed configs; mismatch → Quant alert without writing the queue or waiving gates. `--no-send`. OPEN incidents untouched. Call-card vs Quant SoT language alignment is IMP-032. |

### IMP-032 — Call-card language vs Quant SoT (2026-09-18)

| Field | Value |
|---|---|
| **ID** | IMP-032 |
| **Priority** | P1 |
| **Type** | Hygiene / docs |
| **Desk** | Ops + Quant |
| **Owner** | Don/Ops+Quant |
| **Problem** | UNIVERSE/call-cards still framed as post-#11 revise / “conditional” packs. BTC/NVDA/JPM read conditional vs Quant **DEFER**. AVGO/MSFT/META/XOM still “conditional” while Quant = **INSUFFICIENT_DATA**. Stale HL dayNtl/OI stamps sit in card prose as if live. |
| **Evidence** | Lunch Money Research L2; `research/queue/UNIVERSE-20260917-call-cards.md`; Quant Board `research/quant/2026-09-18/quant-review-board.md` (IMP-008 / #38). |
| **Proposed outcome** | Field-1 Expectation uses Quant closed-set vocabulary only. HL stamps quarantined appendix-only / **DO NOT SIZE**. Locked universe unchanged. Paper only. No new calls. |
| **Definition of done** | Queue: IMP-031 DONE (#56). This item the only implementation thread. Plan [plans/IMP-032-call-card-language-debt.md](plans/IMP-032-call-card-language-debt.md). Call-cards: BTC/NVDA/JPM **DEFER**; AVGO/MSFT/META/XOM **INSUFFICIENT_DATA**; ETH/UNI **MONITOR**; AAVE/SMH/XLF **DEFER**; RESEARCH_PRIORITY none. HL dayNtl/OI appendix-only / DO NOT SIZE. Language gate: no active-call / buy / sell. OPEN incidents untouched. No `live.yaml` / signing / wallets / Redis / paid deps / universe promotion. Tests green. |
| **Non-goals** | New calls; Quant Board rewrite; universe expansion; `live.yaml`; signing; Redis; paid data; closing OPEN incidents; reopening IMP-005 keys; execution. |
| **Dependencies** | IMP-008 DONE (#38). IMP-031 DONE (#56). |
| **Risk level** | Low (docs). Process risk if operators still read membership cards as calls. |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/57 |
| **Lesson learned** | Merged to `main` (#57, 2026-09-18). Call-card field 1 matches Quant SoT. HL dayNtl/OI appendix-only / DO NOT SIZE. Canonical watchlist monitor.yaml is IMP-033. |

### IMP-033 — Canonical watchlist monitor.yaml (Principal 2026-09-19)

| Field | Value |
|---|---|
| **ID** | IMP-033 |
| **Priority** | P1 |
| **Type** | Config / desk product |
| **Desk** | Intel / Ops |
| **Owner** | Intel (resolution + lockup) / Ops (queue + scan wire) |
| **Problem** | Principal locked the complete review list (Operation Lunch Money, 2026-09-19) and `config/watchlist/monitor.yaml` was missing on main. IMP-020 still scanned only `in_universe` ∪ `watch_only`. Ambiguous tickers and EDGAR lockups were not encoded. |
| **Evidence** | Principal 2026-09-19 crypto 06:30 / base 23:00 lists; EDGAR 424B4 CBRS CIK 2021728 and SPCX CIK 1181412; IMP-020 #52; universe.yaml 2026-09-17 lock. |
| **Proposed outcome** | Intel-owned `config/watchlist/monitor.yaml` is THE review list. `lab watchlist scan` walks it. Tiers / clusters / resolution / NEW_LISTING / lockup formulas encoded. No universe promotion. |
| **Definition of done** | Queue: IMP-032 DONE (#57). This item the only implementation thread. Plan [plans/IMP-033-canonical-watchlist-monitor.md](plans/IMP-033-canonical-watchlist-monitor.md). `config/watchlist/monitor.yaml` Principal-locked; owner intel; additions/removals Principal PR only. Universe tier matches `in_universe` (BTCUSD, NVDA). Blocked CASHCAT/PONSUSD. Unresolved only SAMSUN/KOSDA (equities/index, not HL). HL perps: VVVUSD→HL:VVV, PURR→HL:PURR, CHIPIUSD display→HL:CHIP (no CHIPI listing invented). NASDAQ:SPCX, NASDAQ:CBRS (semis_ai). EDGAR lockups confirmed, not flat 180d. NEW_LISTING → listings sleeve; SMA200 n/a string; gate 5 blackout if lockup inside horizon. Research states tier on every idea. OPEN incidents untouched. No `live.yaml` / signing / Redis / paid deps / universe promotion. Tests + import-boundary green. |
| **Non-goals** | Promoting monitor names into `in_universe`; guessing SAMSUN/KOSDA; live/signing; Redis; paid data; closing OPEN incidents; auto-merge; waiving Skeptic/Risk. |
| **Dependencies** | IMP-020 DONE (#52). IMP-017 DONE (#54). IMP-032 DONE (#57). |
| **Risk level** | Medium (operators may treat the review list as membership or invent unresolved ids). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/59 |
| **Lesson learned** | Merged to `main` (#59, 2026-09-19). Canonical `config/watchlist/monitor.yaml` is the review list. SAMSUN/KOSDA were left unresolved on purpose; Principal resolved them in IMP-034. Do not reopen the lock file. |

### IMP-034 — Principal ticker resolutions + licence_verdict schema

| Field | Value |
|---|---|
| **ID** | IMP-034 |
| **Priority** | P1 |
| **Type** | Config / schema |
| **Desk** | Intel + Ops |
| **Owner** | Intel (tickers) / Ops (queue + licence schema) |
| **Problem** | Principal resolved SAMSUN and KOSDA and locked a FREE SOURCE PRIORITY plus a standing redistribution rule. Verdicts lived only in docs. Unresolved flags were stale after #59. |
| **Evidence** | Principal 2026-09-19: SAMSUN → KRX:005930 (Samsung Electronics, KRW); KOSDA → KRX:KQ11 (KOSDAQ Composite, KRW); keep HL:CHIP/VVV/PURR and NASDAQ:SPCX/CBRS. Standing rule: terms that prohibit redistribution → internal compute only; never publish those values. |
| **Proposed outcome** | Clear unresolved flags. Record `licence_verdict` next to each adapter in `config/ingest.yaml`. Intake FREE SOURCE PRIORITY as ordered READY/BACKLOG. FRED full-stack is IMP-022 (the single IN_PROGRESS). |
| **Definition of done** | Queue: IMP-033 DONE (#59). Monitor: SAMSUN=`KRX:005930`, KOSDA=`KRX:KQ11`; unresolved empty; HL:CHIP/VVV/PURR and NASDAQ:SPCX/CBRS unchanged. `adapters.*.licence_verdict` closed set; standing rule in config. Queue items 1–7 ordered. Tests + import-boundary. Paper only. |
| **Non-goals** | Closing SRC-FRED or SRC-STOOQ; universe promotion; guessing other tickers; paid deps; `live.yaml` / signing / Redis. |
| **Dependencies** | IMP-033 DONE (#59). |
| **Risk level** | Low (config). Process: operators must not treat KRX ids as universe promotion. |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/60 |
| **Lesson learned** | Display labels stay SAMSUN/KOSDA. Exchange-qualified ids are KRX. `licence_verdict` is config, not a doc footnote. FRED close is IMP-022 (DONE on persist run_id `fred-fullstack-20260919-101938-aest`; `--no-db` is ELIGIBLE only). |

### IMP-035 — treasury.gov as FRED cross-check

| Field | Value |
|---|---|
| **ID** | IMP-035 |
| **Priority** | P1 |
| **Type** | Data / macro (Principal FREE SOURCE PRIORITY #3) |
| **Desk** | Intel |
| **Owner** | Intel |
| **Problem** | FRED is the rates adapter. There is no official Treasury Fiscal Data cross-check. A FRED outage or vintage miss leaves rates as a single-vendor slot. |
| **Evidence** | Principal FREE SOURCE PRIORITY 2026-09-19 item 3; [ops/reports/source-evaluation/2026-09-18.md](reports/source-evaluation/2026-09-18.md) Treasury licence “free, without restriction… commercial or non-commercial”. `licence_verdict: ok_gov` on `treasury`. |
| **Proposed outcome** | Read-only treasury.gov / Fiscal Data adapter as a FRED cross-check. Contradiction → `contradicted`, never invent. No key. |
| **Definition of done** | Adapter + fixture; PIT; missing → unavailable; values publishable (ok_gov); does not replace FRED; no paid vendor. |
| **Non-goals** | Starting while IMP-024 occupies IN_PROGRESS; replacing FRED; CB calendars (stay with later EDGAR/macro work). |
| **Dependencies** | IMP-022 DONE (run_id `fred-fullstack-20260919-101938-aest`). Parked until IMP-024 leaves the slot. IMP-024 is EDGAR, not this item. |
| **Risk level** | Low. |
| **Status** | READY |
| **PR** | — |
| **Lesson learned** | *(fill at close)* |

### IMP-036 — Retire Yahoo when a licensed path exists

| Field | Value |
|---|---|
| **ID** | IMP-036 |
| **Priority** | P2 |
| **Type** | Data / licence (Principal FREE SOURCE PRIORITY #5) |
| **Desk** | Intel |
| **Owner** | Intel |
| **Problem** | Yahoo scrape/RSS is already rejected (IMP-004 / Pulse runbook) but the retirement rule was docs-only. A licensed replacement is not named yet. |
| **Evidence** | Principal FREE SOURCE PRIORITY 2026-09-19 item 5; `config/ingest.yaml` `adapters.yahoo.licence_verdict: prohibited`. |
| **Proposed outcome** | Keep Yahoo `prohibited` until a licensed path exists. Verdict stays next to the adapter. Do not add Yahoo HTTP. |
| **Definition of done** | `licence_verdict: prohibited` remains until a Principal-named licensed replacement is wired; Pulse still has no Yahoo fallback. |
| **Non-goals** | Adding Yahoo; scraping; starting while IMP-024 occupies IN_PROGRESS. |
| **Dependencies** | A licensed replacement (Principal). |
| **Risk level** | Low (keep-closed). |
| **Status** | BACKLOG |
| **PR** | — |
| **Lesson learned** | *(fill at close)* |

### IMP-037 — Trial Tiingo free tier (base-rate backfill only, 500 sym/mo)

| Field | Value |
|---|---|
| **ID** | IMP-037 |
| **Priority** | P2 |
| **Type** | Data / trial (Principal FREE SOURCE PRIORITY #6) |
| **Desk** | Quant + Intel |
| **Owner** | Quant / Intel |
| **Problem** | Quant base-rate history is thin. Tiingo free tier is 500 symbols/month. Evaluation 2026-09-18 preferred EODHD for delisted; Principal now allows a **base-rate backfill only** trial. |
| **Evidence** | Principal FREE SOURCE PRIORITY 2026-09-19 item 6; `adapters.tiingo.licence_verdict: restricted` (internal until display rights confirmed). |
| **Proposed outcome** | Time-boxed free-tier trial for base-rate backfill only. 500 sym/mo budget. Values stay internal (`restricted`) until display rights are confirmed. Not a second equities vendor for Pulse. |
| **Definition of done** | Env key only if trialled; rate-limit budget; no published Tiingo values while `restricted`; PIT `available_at`; no Yahoo. |
| **Non-goals** | Paid Tiingo; replacing Polygon; publishing values before terms allow; starting while IMP-024 occupies IN_PROGRESS. |
| **Dependencies** | IMP-022 DONE. Parked until IMP-024 leaves the slot. IMP-028/029 paid SKUs stay Principal-gated. |
| **Risk level** | Medium (second vendor vs Polygon lock; Telegram display). |
| **Status** | BACKLOG |
| **PR** | — |
| **Lesson learned** | *(fill at close)* |

### IMP-038 — Finnhub free: calendar/estimates only after terms allow republish

| Field | Value |
|---|---|
| **ID** | IMP-038 |
| **Priority** | P3 |
| **Type** | Data / trial (Principal FREE SOURCE PRIORITY #7) |
| **Desk** | Intel |
| **Owner** | Intel |
| **Problem** | Evaluation 2026-09-18 rejected Finnhub for Telegram (personal-use licence). Principal allows a later trial of calendar/estimates **only after** terms allow republishing derived values to a private channel. |
| **Evidence** | Principal FREE SOURCE PRIORITY 2026-09-19 item 7; `adapters.finnhub.licence_verdict: pending_terms`. |
| **Proposed outcome** | Hold. If terms later allow derived-value republish to a private channel: calendar/estimates only. Until then: no adapter, no published Finnhub numbers. |
| **Definition of done** | Written terms verdict next to the adapter. If still personal-use: stay `pending_terms` / do not wire. If allowed: calendar/estimates only; estimates are vendor IP — confirm republish of *derived* values. |
| **Non-goals** | Wiring Finnhub now; news reprint; starting while IMP-024 occupies IN_PROGRESS. |
| **Dependencies** | Terms review. EDGAR (IMP-024) remains the confirmed-earnings path. |
| **Risk level** | Medium (ToS). |
| **Status** | BACKLOG |
| **PR** | — |
| **Lesson learned** | *(fill at close)* |

### IMP-039 — Candidate strategy intake + Quant validation studies (Principal 2026-09-19)

| Field | Value |
|---|---|
| **ID** | IMP-039 |
| **Priority** | P2 |
| **Type** | Quant / research spec |
| **Desk** | Quant |
| **Owner** | QUANT |
| **Problem** | Retail video / Substack / Reddit strategy slogans have no shelf that is not a thesis, not a Quant Board, and not a watchlist scan-gate. Claims arrive without sample, window, instrument set, cost model, split, or payoff shape. |
| **Evidence** | Principal intake 2026-09-19 (C-001 supply/demand zone, C-002 triple RSI MR, C-003 second-entry pullback); [research/candidates/README.md](../research/candidates/README.md). IMP-034 (#60) is ticker/licence, not this shelf. IMP-033 DONE (#59) must not become the promotion path. |
| **Proposed outcome** | Quant-owned HYPOTHESIS cards with locked `N,X,Y,Z,M` ATR params. Slogans REJECT or restated falsifiably. Validation studies execute later from the specs. Failures archive under `research/candidates/failures/`. |
| **Definition of done** | Queue: IMP-034 DONE (#60). IMP-022 DONE (#62). IMP-024 DONE (#63). Intake landed as [#61](https://github.com/ElChopa11/market-memory/pull/61). Plan [plans/IMP-039-candidate-strategy-intake.md](plans/IMP-039-candidate-strategy-intake.md). Cards stay `INTAKE_ONLY` / HYPOTHESIS. Studies: fixture/paper only; NOTHING computed until IMP-040 Phase 1 base rates exist; `n < 20` → INSUFFICIENT SAMPLE; no live, no PLAYBOOK sizing, no universe/watchlist edits. OPEN incidents untouched. |
| **Non-goals** | Live trading; signing; `live.yaml`; Redis; sizing; scan-gate promotion; implementing C-001/C-002/C-003 as harness strategies in the intake PR or the IMP-040 PR; closing OPEN incidents; auto-merge; waiving Skeptic/Risk; universe promotion. |
| **Dependencies** | IMP-033 DONE (#59). IMP-034 DONE (#60) — id collision avoided. IMP-022 DONE (#62). IMP-024 DONE (#63). IMP-011 harness/factors exist. IMP-029 (delisted tape) BACKLOG — studies carry `survivorship_uncontrolled` until then. IMP-040 Phase 1 base rates must land before any study compute. |
| **Risk level** | Medium (operators may treat a HYPOTHESIS card as a call or promote it through the watchlist scan). |
| **Status** | READY |
| **PR** | [#61](https://github.com/ElChopa11/market-memory/pull/61) (intake specs; studies not started) |
| **Lesson learned** | *(fill when validation studies close)* |

### IMP-040 — Phase 1 unconditional event-class base rates

| Field | Value |
|---|---|
| **ID** | IMP-040 |
| **Priority** | P0 |
| **Type** | Quant / Market Memory |
| **Desk** | Quant |
| **Owner** | Quant |
| **Problem** | C-001/C-002/C-003 cannot be studied until unconditional base rates exist for the event classes they measure against. Principal order-of-work: nothing computed on candidates first. |
| **Evidence** | Principal 2026-09-19 candidate intake; [#61](https://github.com/ElChopa11/market-memory/pull/61) `research/candidates/` (rules 1–12). IMP-034 on main is ticker/licence (#60), not the candidate shelf. IMP-039 is that shelf. |
| **Proposed outcome** | Fixture-deterministic unconditional rates for dip touches, zone/range-boundary touches, and first-entry EMA pullbacks, stored in Market Memory with provenance. Paper only. |
| **Definition of done** | Plan [plans/IMP-040-phase1-unconditional-base-rates.md](plans/IMP-040-phase1-unconditional-base-rates.md). `lab base-rate compute --fixture --no-db` writes `research/quant/base-rates/` with `as_of_knowledge`, `params_hash`, instrument set, window, cost model. Table `event_base_rate`. Naming sleeve `base_rate` → quant. Citation path for C-001/002/003 documented. No sizing, no scan-gate, no candidate study results. IMP-039 stays READY / cards INTAKE_ONLY. OPEN incidents untouched. Tests + import-boundary green. |
| **Non-goals** | Implementing C-001/C-002/C-003 signals; sizing; scan-gate; live/signing; Redis; Telegram send; closing OPEN incidents; universe promotion; auto-merge; dropping EDGAR or candidate-intake files. |
| **Dependencies** | IMP-011 factor math. IMP-019 naming. IMP-039 candidate intake (#61). IMP-024 DONE (#63). |
| **Risk level** | Medium (operators may read a base rate as a call or start candidate studies early). |
| **Status** | DONE |
| **PR** | https://github.com/ElChopa11/market-memory/pull/66 |
| **Lesson learned** | Merged to `main` (#66, 2026-09-19). Fixture-deterministic unconditional rates in `research/quant/base-rates/` + table `event_base_rate`. Expand beyond fixture (live Memory rates) is Principal L2 **P1** — not this thread. IMP-039 stays READY / INTAKE_ONLY. |

### IMP-042 — Scheduler miss detector (clock control)

| Field | Value |
|---|---|
| **ID** | IMP-042 |
| **Priority** | P0 |
| **Type** | Scheduler reliability / ops control |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | SCHED-001 (Sydney 08:00) never fired while NY siblings did. There was no standing check that a closed window without a completion row is a miss. Heartbeat-on-fire alone is a log, not a control. |
| **Evidence** | [reports/scheduler/2026-09-19-sched-001-root-cause.md](reports/scheduler/2026-09-19-sched-001-root-cause.md). No GitHub cron. Lab yaml has no Sydney 08:00 job. Grok Bot `sydney-morning-digest-8am` NEVER RUN. |
| **Proposed outcome** | Miss sweep is MERGE-BLOCKING: for each configured routine, closed window + no completion → non-zero CLI + OPEN ops artifact. CI runs it on a fixture clock. Heartbeat write-on-fire is secondary. SCHED-001 stays OPEN. Canaries ignored. |
| **Definition of done** | Queue: IMP-040 DONE (#66). This item the only implementation thread. Plan [plans/IMP-042-scheduler-heartbeat.md](plans/IMP-042-scheduler-heartbeat.md). `lab schedule miss-check` (heartbeat-check alias) escalates misses. Table `schedule_heartbeat`. Backfill report. Root-cause report separates (a) 08:00 unexplained OPEN from (b) 06:30/Fri 17:00 unverified Hive timestamps. Tests + CI fixture clock. No live trading. No P1/P2/P3. |
| **Non-goals** | Closing SCHED-001; Phase-1 rate expansion; instance ledger; source-health regen; desk naming; Telegram inventory; SRC-object_store; candidate study compute; paid adapters; canaries; auto-merge; waiving gates. |
| **Dependencies** | IMP-040 DONE (#66). SCHED-001 stays OPEN. |
| **Risk level** | High if the miss detector is skipped — the clock stays untrue. |
| **Status** | DONE |
| **PR** | [#68](https://github.com/ElChopa11/market-memory/pull/68) |
| **Lesson learned** | Merged to `main` (#68, 2026-09-19). Miss sweep is the clock control. Heartbeat-on-fire is a log. SCHED-001 stays OPEN. |

### IMP-043 — Hybrid Step 2: delivery env-file + env preflight

| Field | Value |
|---|---|
| **ID** | IMP-043 |
| **Priority** | P0 |
| **Type** | Ops / delivery credentials |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | Telegram token must not live on the Grok Secrets card. Hive is a clock; `lab` is the sole publisher. Operators needed dotenv load from a delivery-only file plus a full-state preflight that names every declared var/service (found / missing / NOT CONFIGURED / DOWN SERVICE) without silent DM fallback or silent getChat id drift. |
| **Evidence** | Principal Hybrid architecture Step 2 (2026-09-19). House lessons: Secrets-card leak; getChat / supergroup `-100...` id change. Hive is a plain group; per-desk routes unset. |
| **Proposed outcome** | `lab` brief/deliver/`lab env preflight` load `/home/box/agent-data/delivery/telegram.env` or `MM_DELIVERY_ENV_FILE`. Preflight prints full state. `MISSING` required → exit non-zero. Per-desk `NOT CONFIGURED` does not fail. `getChat` verifies group id. `--no-send` only. |
| **Definition of done** | Env-file load (file wins when present; process env for CI). Preflight names Telegram (token, group, Principal DM, per-desk), FRED, Polygon, Postgres, object store. No DM fallback. getChat fail-loud. Tests: file load, missing-var names, no secrets printed. Runbook + house lessons. No real send. |
| **Non-goals** | Real Telegram send (step 5); Hive prompt rewrites; miss-detector rework; equity/Polygon feature work; forum topics; delivery binary isolation (IMP-044); committing tokens or chat ids. |
| **Dependencies** | IMP-042 DONE (#68). IMP-013/021 delivery already on main. |
| **Risk level** | Medium (shared-box file-path is a soft boundary; isolation is IMP-044). |
| **Status** | DONE |
| **PR** | [#71](https://github.com/ElChopa11/market-memory/pull/71) |
| **Lesson learned** | Merged to `main` (#71, 2026-09-19). Delivery env-file + full-state preflight. `--no-send` only. Does not occupy the implementation slot. |

### IMP-046 — Hybrid Step 4: Hive CLI completion rows

| Field | Value |
|---|---|
| **ID** | IMP-046 |
| **Priority** | P0 |
| **Type** | Ops / scheduler reliability |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | Hive is the clock; `lab` CLI is the only path that executes. Miss detector (IMP-042) could not observe Hive fires because CLI brief/deliver did not write a completion row (especially `--no-db`). Success-only heartbeat is a log. |
| **Evidence** | Principal Hybrid Step 4 (2026-09-19). IMP-042 miss sweep on main (#68). IMP-043 env preflight on main (#71). Step 3 Grok prompts CLI-clock only (outside this PR). House lesson: instrumentation that records only successes cannot detect silence. |
| **Proposed outcome** | Every Hive-driven `lab brief` / `lab deliver` / `lab schedule heartbeat` writes a completion JSON (`run_id`, trigger, fire time, offset vs anchor, exit status, payload path). Miss-check loads that directory. Failed CLI is a fire. |
| **Definition of done** | Disk rows at `ops/reports/scheduler/completions/`. CLI stamps success and failure. Fixture-clock tests: write on CLI path; miss detector sees fire vs miss. Runbook documents location + how miss-sweep reads it. `--no-send` only. SCHED-001 stays OPEN. Single IN_PROGRESS. |
| **Non-goals** | Real Telegram send (step 5a DM-only is IMP-047); Hive prompt rewrites; lifting freeze; equity/Polygon feature work; closing SCHED-001; IMP-044 isolation; IMP-045 topics; auto-merge; gate waiver. |
| **Dependencies** | IMP-042 DONE (#68). IMP-043 DONE (#71). Step 3 prompts outside this PR. |
| **Risk level** | High if skipped — miss detector still cannot see the executed path. |
| **Status** | DONE |
| **PR** | [#72](https://github.com/ElChopa11/market-memory/pull/72) |
| **Lesson learned** | Merged to `main` (#72, 2026-09-19). Hive CLI completion rows for the miss detector. `--no-send` only. Freeze held until Step 5a (DM-only). |

### IMP-047 — Hybrid Step 5a: DM-only live send (group stays frozen)

| Field | Value |
|---|---|
| **ID** | IMP-047 |
| **Priority** | P0 |
| **Type** | Ops / delivery |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | Principal denied a prior Step 5 that would unfreeze the Hive group. Operators still need a gated live path that POSTs only to the Principal DM. |
| **Evidence** | Principal Step 5a (2026-09-19). IMP-043 env preflight (#71). IMP-046 completion rows (#72). Group `TELEGRAM_CHAT_ID` stays frozen. Cloud VM has no delivery token. |
| **Proposed outcome** | `lab deliver test --to-principal-dm --i-mean-it` POSTs only to `TELEGRAM_CHAT_ID_PRINCIPAL_DM`. Missing that env → refuse. Never `TELEGRAM_CHAT_ID` (group). Preflight still runs. `--routine-id` still stamps a completion row. Envelope/source/provenance on the test payload. |
| **Definition of done** | DM-only CLI path. Group/desk `--send` remains SEND_FROZEN. `--i-mean-it` alone does **not** lift the group freeze (`GROUP_SEND_FROZEN` / `group_live and not to_dm`). Tests mock Telegram HTTP. PR documents on-box acceptance (Don). No miss-detector edits. Weekly authoring CLI not built (IMP-048 BACKLOG). Hybrid clock prompt canonical copies + server read-back not built (IMP-049 BACKLOG). Per-channel `send_enabled` config gate not built (IMP-050 BACKLOG). `--i-mean-it` is acceptable only for this one-shot DM test. Single IN_PROGRESS. |
| **Non-goals** | Lifting the Hive group freeze. Miss-detector / IMP-042 / miss-check edits. Weekly investment review authoring CLI. Hybrid clock prompt-hash / server read-back tooling (IMP-049). Replacing `--i-mean-it` with YAML `send_enabled` (IMP-050). IMP-044 isolation. IMP-045 topics. Claiming live acceptance via mocks. Treating write-API 200 as Step 3 acceptance. Auto-merge. Gate waiver. Agent merge of this PR. |
| **Dependencies** | IMP-046 DONE (#72). IMP-043 DONE (#71). IMP-042 DONE (#68) — do not modify. |
| **Risk level** | Medium (live Bot API POST to a private DM). |
| **Status** | IN_PROGRESS |
| **PR** | *(this PR)* |
| **Lesson learned** | *(fill at close)* |

### IMP-048 — Weekly investment review artifact CLI

| Field | Value |
|---|---|
| **ID** | IMP-048 |
| **Priority** | P2 |
| **Type** | Ops / Research artifact |
| **Desk** | Ops / Research |
| **Owner** | Ops |
| **Problem** | Hive clock `grok.weekly_investment_review` (Fri 17:00 Sydney) has no lab CLI that authors the weekly investment review artifact. Completion rows can stamp a fire; they do not write the review. |
| **Evidence** | Principal Step 5a (2026-09-19): queue-only. Do not allow agent authoring for weekly. |
| **Proposed outcome** | A Principal-specified weekly artifact CLI (not agent-authored prose). Hive remains the clock; `lab` publishes. |
| **Definition of done** | CLI exists that produces the weekly artifact from fixtures/memory without agent authoring. Delivery still Ops-owned. IC/Risk gates unchanged. |
| **Non-goals** | Building it in the Step 5a DM-only PR. Agent-authored weekly. Lifting group freeze. Miss-detector edits. |
| **Dependencies** | IMP-047 DM-only send (this thread). IMP-046 completion rows. |
| **Risk level** | Low (queued). High if agents author the weekly. |
| **Status** | BACKLOG |
| **PR** | — |
| **Lesson learned** | *(do not build now; agents must not author weekly)* |

### IMP-049 — Hybrid clock prompt canonical copies + server read-back

| Field | Value |
|---|---|
| **ID** | IMP-049 |
| **Priority** | P1 |
| **Type** | Ops / prompt integrity |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | Prompt bodies for Grok/Hive routines are **server-kept and not diffable from the repo**. They can be edited outside version control with no PR, no review, no history — an uncontrolled surface. Write-API success is not proof the saved text matches intent. |
| **Evidence** | House lesson 2026-09-19 (server-kept prompts). Principal Hybrid Step 3: tonight’s acceptance is Principal panel read-back of saved prompt text, not the success of the write API call. Three Hybrid clock prompts: `grok.sydney_morning`, `grok.us_pre_market`, `grok.weekly_investment_review`. IMP-031 hashes repo `config/prompts/`, not Grok server bodies. |
| **Proposed outcome** | Keep a canonical copy of each of the three Hybrid clock prompts in the repo with a content hash. Add a periodic read-back comparison against the live server prompts. Drift → fail the check and OPEN an incident (do not silently accept; do not auto-waive gates). |
| **Definition of done** | Canonical in-repo copies of the three Hybrid clock prompts + content hashes. Periodic read-back vs live server. Mismatch fails and opens an incident. Distinct from IMP-031. **Not built in the IMP-047 DM-only PR.** |
| **Non-goals** | Building this tooling in Step 5a. Rewriting Hive prompts from the agent. Lifting group freeze. Miss-detector edits. Treating write-API 200 or mocks as acceptance. Auto-disable of prompts. Auto-merge. Gate waiver. |
| **Dependencies** | IMP-047 DM-only send (this thread). Step 3 Principal panel read-back. IMP-031 is a different surface (repo prompts). |
| **Risk level** | High if skipped long-term (uncontrolled executed prompt). Low this PR (queued only). |
| **Status** | BACKLOG |
| **PR** | — |
| **Lesson learned** | *(do not build now; Step 3 acceptance is panel read-back, not write API)* |

### IMP-050 — Per-channel `send_enabled` config gate (replace `--i-mean-it`)

| Field | Value |
|---|---|
| **ID** | IMP-050 |
| **Priority** | P1 |
| **Type** | Ops / delivery gate |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | `--i-mean-it` is a caller flag, not a durable send control. Future group unfreeze must not be “pass `--i-mean-it`.” Today group freeze is a **code constant/path** (`GROUP_SEND_FROZEN` / `group_live and not to_dm` in `mm_lab_cli`), not YAML — that is why this item is queued. Module `SEND_ENABLED = False` is a different, global dry-run default. |
| **Evidence** | Principal before merge of #73 (2026-09-19). Without `--to-principal-dm`, any `--send` / `--i-mean-it` still hits SEND_FROZEN (already true in code). `--i-mean-it` is acceptable only for the one-shot DM test in Step 5a. |
| **Proposed outcome** | Config gate `send_enabled` **per channel** (DM / Hive group / desk), **read by CLI**, **changed only by PR**. Future group unfreeze flips the Hive-group bit in versioned config, not a caller flag. |
| **Definition of done** | Versioned config with per-channel `send_enabled`. CLI reads it. Flipping a channel requires a Principal-reviewed PR. `--i-mean-it` is not the permanent control. **Not built in the IMP-047 DM-only PR.** |
| **Non-goals** | Building this gate in Step 5a. Lifting the Hive group freeze now. Miss-detector edits. Treating `--i-mean-it` as enough to unfreeze the group. Auto-merge. Gate waiver. |
| **Dependencies** | IMP-047 DM-only send (this thread). Group stays frozen until this gate exists and a later PR enables the group channel. |
| **Risk level** | High if skipped at group-unfreeze time (caller flag as the only lock). Low this PR (queued only). |
| **Status** | BACKLOG |
| **PR** | — |
| **Lesson learned** | *(do not build now; `--i-mean-it` is Step 5a DM test only)* |

### IMP-051 — Publisher inventory by Telegram membership (Hybrid single-exit)

| Field | Value |
|---|---|
| **ID** | IMP-051 |
| **Priority** | P2 |
| **Type** | Ops / delivery control (docs + operator hygiene) |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | A control boundary around repo / CLI send misses every publisher that does not use that path. Desk bots that are Hive members, Chart / TradingView webhooks, and panel drift can post without `lab deliver`. |
| **Evidence** | Principal house lesson 2026-09-19 ([config/knowledge/house-lessons.md](../config/knowledge/house-lessons.md) — “Control boundary around own code misses other publishers”). Hybrid single-exit: desks → GrokBot working chat artifacts → Don compiles → lab deliver CLI → Telegram. IMP-050 (`send_enabled` per channel by PR) already BACKLOG. |
| **Proposed outcome** | Inventory publishers by who can post (membership / credential / webhook), not by what the repo invokes. Then close the extra exits. |
| **Definition of done** | Later PR, not this one: (1) Ops runbook inventories publishers by Telegram membership / credential / webhook. (2) Desk bots removed from the Hive group; they are not members and do not hold Telegram credentials or third-party webhooks to Telegram. (3) Chart / TradingView webhook ban recorded and enforced as policy. (4) Principal panel reconcile: five desks + coord + alerts. **Do not build in this PR.** |
| **Non-goals** | Feature code. Telegram send. Building IMP-050. Lifting the Hive group freeze. Giving desk bots tokens or webhook URLs. Auto-merge. Gate waiver. Occupying the IMP-047 slot. |
| **Dependencies** | IMP-050 stays BACKLOG (per-channel `send_enabled` by PR). House lesson above. IMP-045 (topics vs groups) is a separate Principal decision. |
| **Risk level** | High if skipped (uninventoried publishers). Low this PR (queued only). |
| **Status** | BACKLOG |
| **PR** | — |
| **Lesson learned** | *(do not build now; enumerate by membership / credential / webhook)* |

### IMP-044 — Delivery process isolation (separate user or container)

| Field | Value |
|---|---|
| **ID** | IMP-044 |
| **Priority** | P1 |
| **Type** | Ops / security boundary |
| **Desk** | Ops |
| **Owner** | Ops |
| **Problem** | Delivery-only `telegram.env` on a shared box is a **soft** boundary: any agent that can read the path can load the token. |
| **Evidence** | Principal Hybrid Step 2 (2026-09-19). Secrets-card leak already forced a second rotation. File mode 0600 is not isolation. |
| **Proposed outcome** | Hard fix: delivery binary under a **separate user** or **own container** so research/hive agents cannot read the delivery env file. |
| **Definition of done** | Delivery publisher isolated from multi-agent shared uid. Token not readable by default agent user. Tests/docs. No gate waiver. |
| **Non-goals** | Implementing the isolation in the Step 2 PR. Live trading. Secrets card as the store. |
| **Dependencies** | IMP-043 (env-file + preflight) first. |
| **Risk level** | High if skipped long-term (shared-box read). |
| **Status** | BACKLOG |
| **PR** | — |
| **Lesson learned** | *(do not build now)* |

### IMP-045 — Per-desk Telegram: forum topics vs separate groups

| Field | Value |
|---|---|
| **ID** | IMP-045 |
| **Priority** | P2 |
| **Type** | Ops / delivery routing |
| **Desk** | Ops |
| **Owner** | Principal / Ops |
| **Problem** | Hive is a plain group. Per-desk `TELEGRAM_CHAT_ID_<DESK>` and `message_thread_id` are NOT CONFIGURED. Enabling forum topics converts the chat to a supergroup and changes the id to `-100...`, which would break routing silently without getChat. |
| **Evidence** | Principal 2026-09-19: topics not enabled; single group route is fine until step 5. |
| **Proposed outcome** | Principal chooses per-desk via forum topics (accept id change + getChat) **or** separate groups. Not needed before step 5. |
| **Definition of done** | Principal decision recorded; yaml/env updated without silent id drift; getChat still verifies. |
| **Non-goals** | Building topics or extra groups in Step 2. Real send. Inventing per-desk ids. |
| **Dependencies** | IMP-043 getChat preflight. Step 5 DM-only send first. |
| **Risk level** | Medium (id change). |
| **Status** | BACKLOG |
| **PR** | — |
| **Lesson learned** | *(Principal decision queued — not now)* |

### IMP-041 — Principal-locked desk knowledge base

| Field | Value |
|---|---|
| **ID** | IMP-041 |
| **Priority** | P2 |
| **Type** | Docs / operating system |
| **Desk** | Ops |
| **Owner** | Ops / Principal (file lock) |
| **Problem** | Desks had no Principal-locked prefix for literature priors, measurement failure modes, or dated house lessons. A strong prior can be misread as a trigger; a no-evidence pattern can be under-tested. |
| **Evidence** | Principal 2026-09-19 knowledge-base lock (priors / failure modes / five seeded house lessons). [plans/IMP-041-desk-knowledge-base.md](plans/IMP-041-desk-knowledge-base.md). Merged #67. IMP-042 holds the implementation slot. |
| **Proposed outcome** | `config/knowledge/` with priors, failure modes, house lessons, and usage rules. Cached prompt prefix. Prior never triggers/sizes. House lesson wins over a prior only with date + `run_id`. |
| **Definition of done** | Files present; standing rule (strong prior still needs our base rates; no-evidence prior needs MORE evidence); each failure mode has look / test / example placeholder; five Principal-listed lessons seeded; README usage rules; one-line read-before-round pointer; light markdown smoke. IMP-040 is `DONE` (#66). OPEN incidents untouched. Implementation slot is IMP-042. |
| **Non-goals** | Strategy instructions; sizing; live; candidate compute; paid data; displacing the SCHED/miss-detector thread; closing OPEN incidents; auto-merge; gate waiver. |
| **Dependencies** | None (docs). Merged as #67. Does not occupy the IMP-042 slot. |
| **Risk level** | Low (docs). Process risk if a desk treats a prior as a trigger. |
| **Status** | DONE |
| **PR** | [#67](https://github.com/ElChopa11/market-memory/pull/67) |
| **Lesson learned** | Merged to `main` (#67, 2026-09-19). Docs-only knowledge base. A prior never triggers or sizes. Does not occupy the implementation slot. |

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
| IMP-017 | Research (listings sleeve) | Ops/Research | DONE | [#54](https://github.com/ElChopa11/market-memory/pull/54) Phase 6d listings/IPO Research screen |
| IMP-018 | Ops | Don/Ops | DONE | [#49](https://github.com/ElChopa11/market-memory/pull/49) Phase 6c-1 desk consolidation 11→5 |
| IMP-019 | Ops | Don/Ops | DONE | [#51](https://github.com/ElChopa11/market-memory/pull/51) Phase 6c-2 naming layer |
| IMP-020 | Research | Research | DONE | [#52](https://github.com/ElChopa11/market-memory/pull/52) Phase 6c-4 watchlist monitor |
| IMP-021 | Ops | Ops | DONE | [#53](https://github.com/ElChopa11/market-memory/pull/53) Phase 6c-5 Ops-owned delivery expansion |
| IMP-022 | Intel + Ops | Intel / Ops | DONE | FRED full-stack CLOSED — run_id `fred-fullstack-20260919-101938-aest`; ELIGIBLE path [#60](https://github.com/ElChopa11/market-memory/pull/60) |
| IMP-023 | Intel | Intel | READY | Test data.binance.vision from AU — priority #4 |
| IMP-024 | Intel + Research | Intel / Research | DONE | [#63](https://github.com/ElChopa11/market-memory/pull/63) Wire SEC EDGAR (CBRS+SPCX lockup) |
| IMP-025 | Ops | Ops | BACKLOG | Adopt Alternative.me Fear & Greed — evaluation 2026-09-18 |
| IMP-026 | Intel | Intel | BACKLOG | Trial Coinalyze (free, cite) — evaluation 2026-09-18 |
| IMP-027 | Intel | Principal / Intel | BACKLOG | Trial CoinGlass Standard **$299/mo — Principal paid** |
| IMP-028 | Intel + Quant | Intel / Quant | BACKLOG | Polygon SI / options OI audit; paid SKUs **Principal** |
| IMP-029 | Quant | Quant | BACKLOG | Trial EODHD or Polygon Starter for 5y/delisted — **Principal paid** |
| IMP-030 | Quant + Ops | Quant / Ops | DONE | [#55](https://github.com/ElChopa11/market-memory/pull/55) Phase 6e scorecards + queue automation |
| IMP-031 | Quant | Quant | DONE | [#56](https://github.com/ElChopa11/market-memory/pull/56) Phase 6f strategy decay-watch |
| IMP-032 | Ops + Quant | Don/Ops+Quant | DONE | [#57](https://github.com/ElChopa11/market-memory/pull/57) call-card language vs Quant SoT |
| IMP-033 | Intel / Ops | Intel / Ops | DONE | [#59](https://github.com/ElChopa11/market-memory/pull/59) Canonical watchlist monitor.yaml |
| IMP-034 | Intel + Ops | Intel / Ops | DONE | [#60](https://github.com/ElChopa11/market-memory/pull/60) Ticker resolutions + licence_verdict schema |
| IMP-035 | Intel | Intel | READY | treasury.gov as FRED cross-check — priority #3 |
| IMP-036 | Intel | Intel | BACKLOG | Retire Yahoo when licensed path exists — priority #5 |
| IMP-037 | Quant + Intel | Quant / Intel | BACKLOG | Trial Tiingo free tier base-rate backfill only — priority #6 |
| IMP-038 | Intel | Intel | BACKLOG | Finnhub calendar/estimates after terms allow republish — priority #7 |
| IMP-039 | Quant | QUANT | READY | [#61](https://github.com/ElChopa11/market-memory/pull/61) Candidate strategy intake C-001/C-002/C-003; studies parked (INTAKE_ONLY); IMP-040 pack exists (#66) |
| IMP-040 | Quant | Quant | DONE | [#66](https://github.com/ElChopa11/market-memory/pull/66) Phase 1 unconditional event-class base rates (fixture). Expand is P1. |
| IMP-041 | Ops | Ops / Principal | DONE | [#67](https://github.com/ElChopa11/market-memory/pull/67) Desk knowledge base `config/knowledge/` |
| IMP-042 | Ops | Ops | DONE | [#68](https://github.com/ElChopa11/market-memory/pull/68) Miss detector (clock control). SCHED-001 stays OPEN. |
| IMP-043 | Ops | Ops | DONE | [#71](https://github.com/ElChopa11/market-memory/pull/71) Hybrid Step 2: delivery env-file + full-state preflight. `--no-send` only. |
| IMP-044 | Ops | Ops | BACKLOG | Delivery binary under separate user or own container (hard isolation). Do not build now. |
| IMP-045 | Ops | Principal / Ops | BACKLOG | Per-desk via forum topics vs separate groups. Not before step 5. |
| IMP-046 | Ops | Ops | DONE | [#72](https://github.com/ElChopa11/market-memory/pull/72) Hybrid Step 4: Hive CLI completion rows. `--no-send` only. |
| IMP-047 | Ops | Ops | IN_PROGRESS | Hybrid Step 5a: DM-only live send. Hive group / desk pack `--send` stays SEND_FROZEN. |
| IMP-048 | Ops / Research | Ops | BACKLOG | Weekly investment review artifact CLI. Do not allow agent authoring for weekly. |
| IMP-049 | Ops | Ops | BACKLOG | Canonical copies of the three Hybrid clock prompts + content hash; periodic server read-back. Fail → OPEN incident on drift. Do not build now. |
| IMP-050 | Ops | Ops | BACKLOG | Per-channel `send_enabled` config gate (DM / Hive group / desk), read by CLI, PR-only. Replaces `--i-mean-it` as the permanent send control. Do not build now. |
| IMP-051 | Ops | Ops | BACKLOG | Publisher inventory by Telegram membership (ops runbook); remove desk bots from Hive group; Chart/TradingView webhook ban; panel reconcile five desks + coord + alerts. Do not build now. |

`IN_PROGRESS` count: **1** (IMP-047). IMP-046 is `DONE` (#72). IMP-043 is `DONE` (#71). IMP-042 is `DONE` (#68). IMP-041 is `DONE` (#67). IMP-040 is `DONE` (#66). IMP-039 candidate intake (#61) is `READY`; cards stay `INTAKE_ONLY`. IMP-000–IMP-022, IMP-024, IMP-030–IMP-034, and IMP-040–IMP-043 are `DONE`. IMP-044/045/048/049/050/051 stay BACKLOG. OPEN incidents: SCHED-001 (P0), BRIEF-TAG-20260918, SRC-STOOQ-404, SRC-FRED-MISSING-ENV (environment-propagation; prior CLOSED pack cited, not a key-absent close). Services/infrastructure OPEN: SRC-OBJECT-STORE (DOWN SERVICE, MinIO :9000). Delivery OPEN: TG-UNGATED-PRE-HYBRID (pre-Hybrid Telegram **ungated**). Single implementation thread. Hybrid Step 5a this PR; Hive group stays frozen. Prompt-body drift watch, per-channel `send_enabled`, and publisher inventory are queued, not built.

**OPEN incidents — sources / clock / scorecard** (not a missing-env credentials close list)

| ID | Desk | Owner | Status | Notes |
|---|---|---|---|---|
| SCHED-001 | Ops | Ops | OPEN | P0. Sydney 08:00 digest never fired. Do not close on "no window yet". |
| BRIEF-TAG-20260918 | Ops / Quant scorecard | Ops/Quant | OPEN | 18 Sep pack ~90m pre-open vs 30m anchor |
| SRC-STOOQ-404 | Intel | Intel | OPEN | stooq http_404, 2 consecutive; evaluation 2026-09-18 rejects scrape — lawful proxy is not ES/NQ futures |
| SRC-FRED-MISSING-ENV | Ops | Ops | OPEN | **environment-propagation** (config present, run env absent). 2026-09-19 Don audit: `FRED_API_KEY` on card+process env. Prior CLOSED persist pack retained: run_id `fred-fullstack-20260919-101938-aest`; `--no-db` remains ELIGIBLE only. Do not close as key-absent. |

**OPEN incidents — services / infrastructure** (not a missing-env credentials list)

| ID | Desk | Owner | Status | Notes |
|---|---|---|---|---|
| SRC-OBJECT-STORE | Ops | Ops | OPEN | **DOWN SERVICE**: MinIO `:9000` connection refused, no container. Alias `SRC-object_store` / `object_store`. `MINIO_*` defaults may still be present. Do not close by setting keys. |

**OPEN incidents — delivery / pipeline honesty** (not a working-pipeline proof)

| ID | Desk | Owner | Status | Notes |
|---|---|---|---|---|
| TG-UNGATED-PRE-HYBRID | Ops | Ops | OPEN | Pre-Hybrid Telegram is **ungated**. Known fires: 18 Sep ~22:02 pre-market; 19 Sep 00:03 cash-open; Coord lines from the publisher audit. Not an archive. |


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

Historical “active calls” language debt (membership keys) was a Gap; it is now **IMP-005 DONE** (#35). Do not reopen the key rename. Residual call-card *priority* language vs Quant SoT is **IMP-032 DONE** (#57). Canonical watchlist monitor.yaml is **IMP-033 DONE** (#59). Principal ticker resolutions + `licence_verdict` schema are **IMP-034 DONE** (#60). FRED full-stack is **IMP-022 DONE** (run_id `fred-fullstack-20260919-101938-aest`). SEC EDGAR is **IMP-024 DONE** (#63). Candidate strategy intake is **IMP-039 READY** (#61). Phase 1 unconditional base rates are **IMP-040 DONE** (#66). Desk knowledge base is **IMP-041 DONE** (#67). Scheduler miss detector is **IMP-042 DONE** (#68). Hybrid Step 2 is **IMP-043 DONE** (#71). Hybrid Step 4 is **IMP-046 DONE** (#72). Hybrid Step 5a DM-only send is **IMP-047 IN_PROGRESS**. Weekly review CLI is **IMP-048 BACKLOG**. Hybrid clock prompt canonical copies + server read-back is **IMP-049 BACKLOG**. Per-channel `send_enabled` config gate is **IMP-050 BACKLOG**. Publisher inventory / desk-bot removal / Chart–TradingView webhook ban / panel reconcile is **IMP-051 BACKLOG**.

Post-IPO reclaim screen product was a Gap; it is now **IMP-006 DONE** (#36). Do not reopen.

Dedicated crypto / equity thesis-card templates were a Gap; they are now **IMP-007 DONE** (#37). Generic `thesis.md` stays the lifecycle spine. Do not reopen.

Quant RESEARCH_PRIORITY pass on locked membership was a Gap; it is now **IMP-008 DONE** (#38). Screenshot/TV board remains IMP-001. Do not treat membership as a Quant verdict.

Phase 5 desk/delivery architecture is **IMP-009 DONE** (#40). Polygon equities + HL structure is **IMP-010 DONE** (#41). Quant factor library is **IMP-011 DONE** (#42). Desk runners are **IMP-012 DONE** (#43). Telegram delivery is **IMP-013 DONE** (#44). Phase 6a PG NOTIFY mesh is **IMP-014 DONE** (#45). Phase 6b flow+macro+regime is **IMP-015 DONE** (#46). Phase 6c PLAYBOOK + fan-out is **IMP-016 DONE** (#47). Phase 6c-1 five-desk roster is **IMP-018 DONE** (#49). Phase 6c-2 naming layer is **IMP-019 DONE** (#51). Phase 6c-4 watchlist monitor is **IMP-020 DONE** (#52). Phase 6c-5 delivery expansion is **IMP-021 DONE** (#53). Phase 6d listings/IPO is **IMP-017 DONE** (#54). Phase 6e scorecards + queue automation is **IMP-030 DONE** (#55). Phase 6f decay-watch is **IMP-031 DONE** (#56). Call-card vs Quant SoT language alignment is **IMP-032 DONE** (#57). Canonical watchlist monitor.yaml is **IMP-033 DONE** (#59). Ticker resolutions + `licence_verdict` schema are **IMP-034 DONE** (#60). FRED full-stack is **IMP-022 DONE** (run_id `fred-fullstack-20260919-101938-aest`). SEC EDGAR wire is **IMP-024 DONE** (#63). Candidate strategy intake + Quant validation studies is **IMP-039 READY** (#61). Phase 1 unconditional base rates are **IMP-040 DONE** (#66). Desk knowledge base is **IMP-041 DONE** (#67). Scheduler miss detector is **IMP-042 DONE** (#68). Hybrid Step 2 is **IMP-043 DONE** (#71). Hybrid Step 4 is **IMP-046 DONE** (#72). Hybrid Step 5a DM-only send is **IMP-047 IN_PROGRESS**. Weekly review CLI is **IMP-048 BACKLOG**. Hybrid clock prompt canonical copies + server read-back is **IMP-049 BACKLOG**. Per-channel `send_enabled` config gate is **IMP-050 BACKLOG**. Publisher inventory / desk-bot removal / Chart–TradingView webhook ban / panel reconcile is **IMP-051 BACKLOG**.

Principal FREE SOURCE PRIORITY 2026-09-19 source work: **IMP-022** FRED full-stack DONE → **IMP-024** EDGAR DONE (#63) → **IMP-035** treasury.gov READY → **IMP-023** Binance vision AU READY → **IMP-036**–**038** BACKLOG. Phase 1 base rates are **IMP-040 DONE** (#66). Candidate intake is **IMP-039 READY** (#61); cards stay INTAKE_ONLY. Desk knowledge base is **IMP-041 DONE** (#67). Scheduler miss detector is **IMP-042 DONE** (#68). Hybrid Step 2 is **IMP-043 DONE** (#71). Hybrid Step 4 is **IMP-046 DONE** (#72). Hybrid Step 5a DM-only send is **IMP-047 IN_PROGRESS**. Weekly review CLI is **IMP-048 BACKLOG**. Hybrid clock prompt canonical copies + server read-back is **IMP-049 BACKLOG**. Per-channel `send_enabled` config gate is **IMP-050 BACKLOG**. Publisher inventory / desk-bot removal / Chart–TradingView webhook ban / panel reconcile is **IMP-051 BACKLOG**. Paid items IMP-027–029 stay BACKLOG / Principal-gated. OPEN Stooq stays OPEN. SRC-FRED-MISSING-ENV is OPEN (environment-propagation; prior CLOSED pack cited). SRC-OBJECT-STORE is OPEN (DOWN SERVICE). TG-UNGATED-PRE-HYBRID is OPEN (pre-Hybrid Telegram **ungated**). SCHED-001 stays OPEN.

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
- IMP-021 merged as #53 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-017.
- IMP-017 merged as #54 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-030.
- IMP-030 merged as #55 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-031.
- IMP-031 merged as #56 while the queue still said `IN_REVIEW` — hygiene fixed on IMP-032.
- IMP-032 merged as #57. IMP-033 merged as #59. IMP-034 + IMP-022 ELIGIBLE path merged as #60 (SAMSUN→KRX:005930, KOSDA→KRX:KQ11, `licence_verdict` next to each adapter). #62 closed `SRC-FRED-MISSING-ENV` on persist run_id `fred-fullstack-20260919-101938-aest` (not `--no-db`) and marked IMP-022 DONE. Principal record correction 2026-09-19: that close pack is retained; the incident is **OPEN** again under **environment-propagation** (Don audit: key present on card+process env; earlier missing_env = runs that did not inherit box env). #63 wired SEC EDGAR and persists CBRS/SPCX lockup observations (IMP-024 DONE). #61 landed candidate strategy intake as IMP-039 READY. #66 landed IMP-040 Phase 1 fixture base rates. #67 landed IMP-041 desk knowledge base. #68 landed IMP-042 miss detector. SRC-STOOQ-404, SCHED-001, BRIEF-TAG-20260918 stay OPEN. SRC-OBJECT-STORE is OPEN as a **DOWN SERVICE** (MinIO :9000; not missing_env). TG-UNGATED-PRE-HYBRID is OPEN: pre-Hybrid Telegram (18 Sep ~22:02 pre-market, 19 Sep 00:03 cash-open, Coord publisher-audit lines) is **ungated** and is not pipeline proof. SCHED-001 is P0; do not close on “no window yet”. Locked universe unchanged. Paper only. #71 landed IMP-043 Hybrid Step 2. #72 landed IMP-046 Hybrid Step 4. Single-threaded: IMP-047 Hybrid Step 5a (DM-only send) is the only `IN_PROGRESS`. Hive group stays frozen. IMP-048 weekly authoring CLI is BACKLOG.
- Candidate strategy intake (C-001/C-002/C-003) is **IMP-039 READY** (#61). IMP-034 on main is ticker/licence (#60), not that shelf. Studies stay parked (Quant-owned; no sizing; no scan-gate). IMP-040 pack exists (#66); expansion is L2 P1. Retail provenance = `n=unknown` hypothesis weight.
- Desk knowledge base is **IMP-041 DONE** (#67). Does not take the IMP-047 slot. OPEN incidents untouched.
- Publisher inventory (membership / credential / webhook), desk-bot removal, Chart/TradingView webhook ban, and panel reconcile (five desks + coord + alerts) is **IMP-051 BACKLOG**. IMP-050 `send_enabled` per channel stays BACKLOG. Do not build. No Telegram send.
- Principal FREE SOURCE PRIORITY 2026-09-19 reorders source work (IMP-022 DONE / 024 DONE / 035 READY / 023 READY / 036 / 037 / 038). Paid items (IMP-027 CoinGlass Standard, IMP-028 paid Polygon SKUs, IMP-029 EODHD/Starter) stay Principal decision.
