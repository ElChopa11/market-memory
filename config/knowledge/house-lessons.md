# House lessons

Principal-seeded 2026-09-19. This file **compounds from post-mortems**. A new lesson is appended only when a closed post-mortem (or incident close) cites **date + `run_id`** (or artifact `content_hash`). Do not silently rewrite an old lesson.

A house lesson **wins over a prior** in [priors.md](priors.md) when the override is annotated with date + `run_id`. Process lessons are not sizes and not triggers.

Seed rows below are Principal-listed. Some still lack a persist `run_id`; they stay lessons, but they cannot override a prior until that id exists.

---

## 2026-09-12 — R divergence

| Field | Value |
|---|---|
| **Date** | 2026-09-12 |
| **run_id** | *(pending — annotate when the originating pack/run is bound)* |
| **Desk** | Quant / IC/Risk |
| **What happened** | R (and “rel”) diverged across artifacts: more than one calculator, or relative-value simple-diff read as α. |
| **Lesson** | Quant `compute_trade_math` is the **only** R calculator. Every PLAYBOOK artifact inherits `trade_math_hash`; drift → `error_class=math_mismatch`, failed run. `rel` is simple-diff, **not** α. Intake does not invent expectancy. `prior(judgement)` is excluded from expectancy and sizing. |
| **Does not** | Authorise a size, a clip, or a second R path “for narrative.” |
| **Overrides prior** | No — no `run_id` yet. |

---

## ETF flow invalidator — wrong timeframe

| Field | Value |
|---|---|
| **Date** | *(seed; bind the originating review date when cited)* |
| **run_id** | *(pending)* |
| **Desk** | Research / Skeptic |
| **What happened** | ETF flow (or another flow print) was used as an invalidator on a timeframe that could not kill the thesis — typically a single daily print against a multi-day claim. |
| **Lesson** | Invalidation lookback ≥ thesis horizon / 2. Daily-print invalidators on multi-day theses fail at Skeptic. Flow invalidators use **rolling net/z**, never a single print. The invalidator’s clock must be able to fire inside the claim’s horizon. |
| **Does not** | Turn ETF flow into a trigger or a size. Multi-day ETF flow series remain a data gap until they exist in Memory. |
| **Overrides prior** | No — no `run_id` yet. |

---

## 0W–1L stand-down

| Field | Value |
|---|---|
| **Date** | *(seed; bind when the sleeve record exists)* |
| **run_id** | *(pending)* |
| **Desk** | Ops / IC/Risk |
| **What happened** | After **0 wins and 1 loss** on a published idea class, the book kept offering the next idea as if `n=1` were noise only. |
| **Lesson** | **Stand down** new publishes on that class pending review (post-mortem gate: closed idea → `templates/post-mortem.md` before that instrument publishes again). This is a **process** halt, not a sleeve-size change. The drawdown ladder still has `n=1` as a noop for −8% / −15% (`config/risk/drawdown.yaml`). One loss does not rewrite risk YAML and does not authorise “revenge” size. |
| **Does not** | Change `size_pct`, lift a Risk BLOCK, or treat stand-down as a Quant verdict. |
| **Overrides prior** | No — no `run_id` yet. Process lesson, not a literature override. |

---

## 2026-09-18 — FRED 10Y invented

| Field | Value |
|---|---|
| **Date** | 2026-09-18 |
| **run_id** | *(pending Pulse/playbook run_id for the invented figure; source-eval pack is [ops/reports/source-evaluation/2026-09-18.md](../../ops/reports/source-evaluation/2026-09-18.md))* |
| **Desk** | Intel / Ops / writer |
| **What happened** | US10Y / rates appeared in prose while FRED was `missing_env` / unavailable — a number filled from general knowledge (NO BACKFILL breach). |
| **Lesson** | FRED unavailable → **no** rates figure in the body; name `rates` in gaps. Never invent DGS10 / US10Y. NUMERIC LOCK + NO BACKFILL (IMP-016 / 6c-0; [docs/runbooks/llm-budget.md](../../docs/runbooks/llm-budget.md)). Honest `unavailable` is success. Full-stack close of `SRC-FRED-MISSING-ENV` is a later persist (`fred-fullstack-20260919-101938-aest`) and does not erase this lesson. |
| **Does not** | Allow `--no-db` ELIGIBLE runs to be treated as CLOSED. Does not authorise committing `FRED_API_KEY`. |
| **Overrides prior** | No — no originating `run_id` bound. When bound, overrides any “we know the 10Y” narrative prior. |

---

## 2026-09-19 — routine never-fired / miss detector

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(pending — SCHED-001 stays OPEN until a verified fire or a miss explained with a fix queued)* |
| **Desk** | Ops |
| **What happened** | Sydney 08:00 digest (`sydney-morning-digest-8am`) was configured and **never fired**. Same class: Weekly Investment Review never run. Status report 2026-09-19: configured ≠ ran. |
| **Lesson** | **Configured is not executed.** Do not close on “config exists.” Need a miss detector: a routine that is scheduled must emit a heartbeat or an OPEN incident when the window passes with `never-run`. SCHED-001 remains OPEN. Do not treat a sibling NY-cron success as proof the Sydney job ran. |
| **Does not** | Close SCHED-001. Does not retune Pulse. Does not start a second `IN_PROGRESS` implementation to “just add a cron.” |
| **Overrides prior** | No — incident still OPEN. Process lesson for Ops rounds. |

---

## 2026-09-19 — Grok Secrets card / secret-request leak

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(pending — process incident; bind if a rotation run_id is recorded)* |
| **Desk** | Ops |
| **What happened** | This is the **second** Telegram token rotation caused by a **credential-handling path**, not by an external breach. Grok Bot `secret-request` / Secrets-card “secure” input wrote the bot token onto the **shared multi-agent Secrets card**. |
| **Lesson** | Any “secure” input that writes to a shared surface (Grok Bot Secrets card / `secret-request`) is **not** secure on a shared multi-agent box. Agents must not receive `TELEGRAM_BOT_TOKEN` via default env. The only safe path for a delivery secret is one where **no agent process handles it**: BotFather → Principal clipboard → `/home/box/agent-data/delivery/telegram.env` written by the Principal (mode 0600, or `MM_DELIVERY_ENV_FILE`). **No card, no widget secret field, no chat paste, no secret-request.** |
| **Does not** | Authorise putting the token in git, yaml, Hive prompts, or CI Secrets for agents. Does not make the shared-box file-path a hard isolation boundary (that fix is queued as IMP-044). Does not authorise a real send. |
| **Overrides prior** | No — process lesson. Not a literature prior. |

---

## 2026-09-19 — Telegram getChat / supergroup id drift

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(pending)* |
| **Desk** | Ops |
| **What happened** | Hive is a **plain group** (not a supergroup). Converting it to a supergroup or enabling forum topics changes the chat id to a `-100...` form. Routing that still points at the old id would break **silently**. Per-desk `TELEGRAM_CHAT_ID_<DESK>` / `message_thread_id` are not configured. |
| **Lesson** | Preflight must `getChat` the configured group id and **fail loudly** if it does not resolve or if the resolved id differs. Do not assume the id is stable across a supergroup conversion. Per-desk forum topics vs separate groups is a Principal decision — not needed before step 5; single group route is fine. `TELEGRAM_CHAT_ID` (group) must never silently fall back to `TELEGRAM_CHAT_ID_PRINCIPAL_DM`. |
| **Does not** | Authorise a real send. Does not enable forum topics. Does not invent per-desk chat ids. |
| **Overrides prior** | No — process lesson. |

---

## 2026-09-19 — Controls on a path that never executes are not controls

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(pending — SCHED-001 stays OPEN)* |
| **Desk** | Ops |
| **What happened** | Hive routines, send gates, and heartbeat-on-fire sat on a path that **never executed**. Config existed; the control never ran. Same class as a preflight nobody invokes. |
| **Lesson** | **Controls on a path that never executes are not controls.** A check, gate, or heartbeat that is not on the executed path does not protect the box. Preflight, `getChat`, and miss-sweep only count when they actually run. |
| **Does not** | Close SCHED-001. Does not authorise a real Telegram send. Does not treat a config file as a substitute for a run. |
| **Overrides prior** | No — process lesson. |

---

## 2026-09-19 — Absence of output is not evidence of absence of windows

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(pending — SCHED-001 stays OPEN)* |
| **Desk** | Ops |
| **What happened** | No Hive digest appeared. That silence was readable as “no window,” while weekday windows had already closed unfired. |
| **Lesson** | **Absence of output is not evidence of absence of windows.** No Hive print ≠ no scheduled window. Do not close SCHED-001 on “no window yet.” |
| **Does not** | Close SCHED-001. Does not treat a sibling NY-cron success as proof the Sydney job ran. |
| **Overrides prior** | No — incident still OPEN. Process lesson. |

---

## 2026-09-19 — Instrumentation that records only successes cannot detect silence

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(pending — SCHED-001 stays OPEN)* |
| **Desk** | Ops |
| **What happened** | Heartbeat-on-fire writes a row only when a job fires. Jobs that never run leave **no row**, so success-only instrumentation reports a clean log. |
| **Lesson** | **Instrumentation that records only successes cannot detect silence.** Heartbeat-on-fire is a log, not the control. Closed window + no completion row is the miss (IMP-042 `lab schedule miss-check`). |
| **Does not** | Replace the miss detector with another write-on-fire. Does not auto-close OPEN incidents. |
| **Overrides prior** | No — process lesson. |

---

## 2026-09-19 — Grok/Hive prompt bodies are server-kept (not diffable)

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(pending — Step 3 acceptance is Principal panel read-back, not a persist run)* |
| **Desk** | Ops |
| **What happened** | Prompt bodies for Grok/Hive routines live on the Grok server. They are **not** in git. A write API call can change the executed prompt with no PR, no review, and no history. |
| **Lesson** | Prompt bodies for Grok/Hive routines are **server-kept and not diffable from the repo**. They can be edited outside version control with no PR, no review, no history — an **uncontrolled surface**. Tonight’s Step 3 acceptance is **Principal panel read-back of saved prompt text**, not the success of the write API call. A 200 from the write API is not evidence the saved body matches intent. Mitigation (canonical copies + periodic read-back vs live server; fail → OPEN incident on drift) is queued as IMP-049 BACKLOG — do not build in this PR. |
| **Does not** | Treat write-API success as Step 3 done. Does not authorise building prompt-hash/read-back tooling now. Does not lift the Hive group freeze. Does not rewrite the miss detector. Does not treat mocks as acceptance. Does not auto-disable prompts. Distinct from IMP-031 (repo `config/prompts/` decay does not cover Grok server bodies). |
| **Overrides prior** | No — process lesson. |

---

## 2026-09-19 — Control boundary around own code misses other publishers

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(pending — Principal process lesson; bind if an incident/run is recorded)* |
| **Desk** | Ops |
| **What happened** | A control boundary drawn around lab CLI / repo invocation treated “what we call” as the publisher set. Publishers that do not use that path (Telegram membership, a credential, a third-party webhook) were not counted. |
| **Lesson** | A control boundary drawn around your own code misses every publisher that does not use it. Enumerate publishers by who can post to the channel (membership / credential / webhook), not by what your repo invokes. Hybrid single-exit: desks → GrokBot working chat artifacts → Don compiles → lab deliver CLI → Telegram. Desk bots must not be Telegram members and must not hold Telegram credentials or third-party webhooks to Telegram. |
| **Does not** | Authorise a Telegram send. Does not build IMP-050 (per-channel `send_enabled` by PR) or IMP-051 (membership inventory / desk-bot removal / Chart–TradingView webhook ban / panel reconcile). Does not lift the Hive group freeze. Does not make a desk bot a publisher. |
| **Overrides prior** | No — process lesson. |

This lesson **still stands**. Enumerating publishers by what the repo invokes is **structurally incomplete**. The 2026-09-19 BTCUSDC.P FALSE POSITIVE does not retire it.

---

## 2026-09-19 — BTCUSDC.P Telegram sighting was FALSE POSITIVE

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(none — Principal FALSE POSITIVE close; no persist run. Do not invent one.)* |
| **Desk** | Ops |
| **What happened** | BTCUSDC.P sighted in the GrokBot panel was **desk working-thread output, not Telegram**. Hive search: **No Results**. Membership: **Principal + one human + delivery bot only**. The freeze was **never incomplete**. Cause: monitoring GrokBot and Telegram together and reading working output as a publish. |
| **Lesson** | Working-thread output is not a publish. GrokBot panel ≠ Telegram. Hive **No Results** plus membership Principal + one human + delivery bot only means the freeze was never incomplete. Do not treat GrokBot desk output as a Telegram send. |
| **Does not** | Reopen the freeze as incomplete. Does not authorise a Telegram send. Does not build membership-list or Bot API tooling. Does not erase the prior lesson that enumerating publishers by what the repo invokes is structurally incomplete. |
| **Overrides prior** | No — process lesson. Does not override the control-boundary lesson. |

---

## 2026-09-19 — Telegram membership is the authoritative publisher inventory

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(pending — standing check; bind if an incident/run is recorded)* |
| **Desk** | Ops |
| **What happened** | Publisher inventory that starts from repo invocation or from an admin-only Bot API list can miss who can actually post. Completeness requires a Principal member-list read. |
| **Lesson** | **Telegram membership IS the authoritative publisher inventory.** Re-verify membership whenever any bot or integration is added. An **Admin-only Bot API list is insufficient** — **Principal member-list read is required for completeness**. |
| **Does not** | Authorise building Bot API member-list tooling. Does not treat `getChatAdministrators` (or any admin-only Bot API list) as complete. Does not retire the prior lesson that enumerating publishers by what the repo invokes is structurally incomplete. Does not authorise a Telegram send. |
| **Overrides prior** | No — process lesson. Complements the control-boundary lesson; does not replace it. |

---

## 2026-09-19 — Ticker resolution is not entity continuity

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(none invented — cite artifact `research/base-rates/phase1-2026-09-19.md`; Principal direction on the Phase-1 equity run)* |
| **Desk** | Intel / Quant |
| **What happened** | `NASDAQ:SPCX` resolved to SpaceX, but Polygon daily aggs by ticker string returned the prior listing (The SPAC and New Issue ETF, ~$7M AUM). 454 bars from 2024-09-19, SpaceX IPO 2026. Median 1-bar 0%, vol ~121%, max 1-bar +29.8% — an entity splice, not a price series. |
| **Lesson** | **Resolving a ticker to an identifier does not prove the returned series belongs to one entity.** Continuity check flags `suspected_ticker_reuse` and **excludes** the series from the void-excluded pool. Do not treat a qualified_id hit as a clean tape. **N-sigma VOID is retired** (see the 2026-09-19 follow-up lesson): listing-date + 20/20 sustained level-shift are the voids; a single-bar extreme flags only. |
| **Does not** | Promote or demote watchlist membership. Does not invent a spliced-clean series. Does not authorise a size. Does not close OPEN incidents. |
| **Overrides prior** | No — no persist `run_id`. Process/data lesson. |

---

## 2026-09-19 — N-sigma/MAD is the wrong ticker-reuse test

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(none invented — cite artifacts `research/base-rates/phase1-2026-09-19.md`, `config/research/ticker_continuity.yaml`; Principal rejection of PR #77 N=8 retune)* |
| **Desk** | Intel / Quant |
| **What happened** | Continuity VOID used `max \|1-bar\| > N × 1.4826×MAD` (N=8). That scale is tail-insensitive: a fat-tail equity day always prints a large multiple. The rule voided QQQ, NVDA, BB, MRNA, STRC (and BMNR) — legitimate tails and possible unadjusted corporate actions — the same way it caught SPCX ticker reuse. Retuning N is parameter fitting. |
| **Lesson** | **N-sigma / MAD void was the wrong mechanism for ticker reuse.** Correct voids: **listing-date** (first bar precedes known `listed_on`) and **sustained 20/20 median level-shift** (`median(close, 20 after) / median(close, 20 before) >= 3` or `<= 1/3`; scan every bar with a full window; skip B when either side has fewer than 20 bars — do not invent). **Single-bar extremes FLAG only, never VOID.** A flag is information; a void is a decision. **Always prefer adjusted equity bars** (`adjusted=true` on Polygon daily aggs). Voiding because a fetch was unadjusted is incorrect. Report full pool and continuity-void-excluded pool. The pooled 1R:2R figure is a **descriptive mixture** (not a strategy hurdle); continuity voids barely move it. |
| **Does not** | Authorise retuning N. Does not promote or demote watchlist membership. Does not invent a spliced-clean series. Does not authorise a size. Does not treat a FLAG as a VOID. Does not skip the listing-date check on SPCX. |
| **Overrides prior** | Yes, the N-sigma VOID *mechanism* in the 2026-09-19 “Ticker resolution is not entity continuity” lesson. Listing-date VOID and the entity-continuity lesson itself still stand. No persist `run_id`; process/data override of the test, not a literature prior. |

---

## 2026-09-19 — Sustained level-shift can be ticker reuse or a business transformation

| Field | Value |
|---|---|
| **Date** | 2026-09-19 |
| **run_id** | *(none invented — cite artifacts `research/base-rates/phase1-2026-09-19.md`, `config/research/ticker_continuity.yaml`; Intel confirm of Principal-asked BMNR 2025-06-30)* |
| **Desk** | Intel / Quant |
| **What happened** | Rule B voided BMNR on 2025-06-30 (20/20 median ratio ~7.91 on the #81 `adjusted=true` tape). The mechanical label was `suspected_ticker_reuse`. Intel: same issuer BitMine Immersion Technologies (BMNR, CIK 0001829311); that day was a ~$250M PIPE @ $4.50 for ETH treasury + Tom Lee named Chairman (8-K 0001683168-25-004802), not a ticker-string splice. Reverse split is a separate May 15–16 2025 event. Identifier continuous; character break = strategy/governance pivot. Exclusion outcome matches ticker reuse; cause does not. |
| **Lesson** | **A sustained 20/20 level-shift can flag ticker reuse OR a continuous-identifier business transformation; record which.** BMNR 2025-06-30 is the latter. Do not leave the void as only “rule B fired.” Void status unchanged (still excluded from the void-excluded pool). Contrast SPCX (true ticker reuse under rule A). |
| **Does not** | Change BMNR void status or restore it to the void-excluded pool. Does not retune rule B. Does not treat a FLAG as a VOID. Does not authorise a size. Does not promote or demote watchlist membership. |
| **Overrides prior** | No — complements the entity-continuity and N-sigma lessons. Process/data annotation of void *cause*, not a literature prior. No persist `run_id`. |

---

## 2026-09-20 — 160×90 polyline is a thumbnail, not a chart

| Field | Value |
|---|---|
| **Date** | 2026-09-20 |
| **run_id** | *(none — Principal Option 1; queue-only. Do not invent one.)* |
| **Desk** | Research (chart sleeve) / Ops |
| **What happened** | PLAYBOOK `CHART_ARTIFACT` encodes a 160×90 closes-only polyline (`render_png`) with no axes or labels. That image cannot inform a decision; every playbook run still produces one, and the desk then explains it. |
| **Lesson** | **A 160×90 closes-only polyline with no axes/labels is a thumbnail, not a chart.** Do not treat it as decision evidence. Retirement of stdlib `render_png` is IMP-058 BACKLOG (after Monday 2026-09-21 unattended fire). Later `CHART_ARTIFACT` is TradingView ref + structured levels, not pixels. |
| **Does not** | Authorise implementing the retirement now. Does not authorise Telegram from Chart. Does not make Chart a publishing desk. Does not occupy IN_PROGRESS. Does not start C-00x. Does not lift the IMP-051 Chart/TV webhook ban. |
| **Overrides prior** | No — process lesson. Not a literature prior. |

---

## 2026-09-22 — Bot box is a container; compose is not deployment

| Field | Value |
|---|---|
| **Date** | 2026-09-22 |
| **run_id** | *(none — Principal process lesson from consecutive box probes. Do not invent a persist run_id.)* |
| **Desk** | Ops |
| **What happened** | Two consecutive Grok Bot boxes were **themselves containers**: PID1=`tini` → `pod-daemon`, overlay filesystem, no systemd, no docker/podman binary, no `docker.sock`. Infrastructure that assumes a local Docker host has **not been available once** on this path. |
| **Lesson** | Treat the bot box / pod as a container without a nested Docker executor. `docker-compose.yml` is a **local-dev artifact** for a machine that can run Docker — **not** a deployment path for the bot box. Real Memory deployment direction is **managed Postgres + S3-compatible object store** (Neon + Cloudflare R2 decided). Do not treat compose as production. |
| **Does not** | Wire Neon/R2 in this lesson. Does not invent a persist `run_id`. Does not authorise editing `live.yaml` or committing secrets. Does not invent `config/reference/listings.yaml`. |
| **Overrides prior** | No — process lesson. Not a literature prior. |

---

## How this file grows

1. Close the idea or incident with [templates/post-mortem.md](../../templates/post-mortem.md) (or an incident-close pack that cites `run_id`).
2. Append a lesson block with date, `run_id`, desk, what happened, lesson, does-not, and whether it overrides a named prior.
3. Principal PR if the lesson re-ranks or deletes a prior.

Do not invent `run_id`. Do not auto-apply playbook changes from a lesson.
