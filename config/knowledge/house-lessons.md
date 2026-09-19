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

## How this file grows

1. Close the idea or incident with [templates/post-mortem.md](../../templates/post-mortem.md) (or an incident-close pack that cites `run_id`).
2. Append a lesson block with date, `run_id`, desk, what happened, lesson, does-not, and whether it overrides a named prior.
3. Principal PR if the lesson re-ranks or deletes a prior.

Do not invent `run_id`. Do not auto-apply playbook changes from a lesson.
