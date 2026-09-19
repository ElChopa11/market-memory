# SCHED-001 root cause — 2026-09-19

as_of_knowledge: 2026-09-19T09:49:00Z (Sat 19:49 AEST)
control: miss sweep (closed window + no completion → escalate)
heartbeat-on-fire: log only; not this report’s check
canaries: out of scope (running outside this PR)

Two clocks. Do not collapse them.

---

## (a) Historical SCHED-001 — Sydney 08:00 — unexplained, stays OPEN

**Cause statement:** The Sydney 08:00 digest (`sydney-morning-digest-8am`) had weekday windows and never fired. Sibling NY-cron briefs completed. That miss is **unexplained**. It is not closed by “no window yet”, by a retarget to 06:30, or by shipping a detector.

### Configured vs actual (lab clock)

| Source | What it configured | First enabled | Sydney 08:00 job? | Runner in this repo? |
|---|---|---|---|---|
| `config/schedules/market-pulse.yaml` (Phase 0, 2026-09-16 13:35Z) | pre_open/close **disabled** | stub | **no** | no |
| Same file, Phase 3 (commit `48f48f8`, 2026-09-16 14:34Z) | pre_open **08:00 America/New_York**; close 16:15 NY; weekdays | 2026-09-16 | **no** (NY 08:00 ≠ Sydney 08:00) | no GitHub `schedule:` / cron; no compose worker |
| `config/delivery/telegram.yaml` `schedule` | desk_pack 07:30, watchlist 07:45, listings 07:50, scorecard 07:55, decay 08:05 **Australia/Sydney** | later 6c | 08:05 decay is not the 08:00 digest | no cron |
| `.github/workflows/*` | `pull_request` + `push` to main only | — | — | **no cron** (verified 2026-09-19) |
| `docker-compose.yml` | postgres + minio | — | — | no briefing-worker service |
| `briefing-worker run` | sleeps until next Pulse NY fire | Phase 3 | NY Pulse only | not deployed |

Git history of `config/schedules/market-pulse.yaml`: **two revisions**, neither ever lists a Sydney 08:00 digest. Lab yaml cannot have fired SCHED-001.

### Configured vs actual (Grok Bot clock)

| Routine | Anchor (operator facts 2026-09-19) | Completions in repo | Status |
|---|---|---|---|
| `sydney-morning-digest-8am` | weekdays 08:00 Australia/Sydney | none | NEVER RUN. **SCHED-001.** |
| US Pre-Market / NY siblings | see (US Pre-Market) below | observed fire Fri 18 ~22:02 AEST; committed sample `briefs/2026-09-16/us-pre-market.md` is **off** the 08:00 NY anchor (generated 2026-09-17T03:19:30Z) | siblings **did** complete |

Queue evidence (IMP-018 #49, 2026-09-18): *“Routine `sydney-morning-digest-8am` showed never-run while sibling NY-cron briefs completed.”*

There is **no** `ROUTINE_CHANGE` / `created_at` / `updated_at` for this routine in the repo. Hive timestamps are pending Don paste. Until then: **windows existed and did not fire** is the operating fact. Do not rewrite it as a creation-timing miss.

### Why NY siblings could fire while 08:00 did not (hypotheses — not a close)

1. **Split ownership (supported).** Lab Pulse is NY wall-clock in yaml with no in-repo runner. Actual fires came from Grok Bot / operator `lab brief`. The Sydney 08:00 Grok Bot routine is a different id and never completed.
2. **No in-repo cron (supported).** Nothing in GitHub Actions or compose invokes 08:00 Sydney.
3. **Timezone / cron mismatch on the Grok Bot routine (unverified).** Possible, not proven: a UTC 08:00 string would not be 08:00 Sydney.
4. **Disabled / invalid automation (unverified).** UI NEVER RUN is consistent with zero successful triggers.
5. **Not “no window yet” (rejected as a close).** Weekday 08:00 windows occurred (at least Wed 16 / Thu 17 / Fri 18 Sep 2026 while NY siblings were alive). Closing on the next window would hide a miss the detector exists to catch.

**Verdict (a):** unexplained miss. SCHED-001 stays **OPEN** until a verified on-anchor fire. The miss detector is the standing control that would have escalated each closed 08:00 window without a completion row.

---

## (b) Retargeted 06:30 / Weekly Fri 17:00 — calendar hypothesis UNVERIFIED

Operator facts (status report #65 + this turn): Grok Bot, Australia/Sydney:

| Routine | Configured | automation_status | Next window after Sat 2026-09-19 19:49 AEST |
|---|---|---|---|
| Sydney Morning | weekdays 06:30 | NEVER RUN | Mon 21 Sep 06:30 AEST |
| Weekly Investment Review | Fridays 17:00 | NEVER RUN | Fri 25 Sep 17:00 AEST |

**Calendar hypothesis:** if these routines were *created or retargeted after* Fri 18 06:30 and Fri 18 17:00, never-run as of Saturday is expected until those next windows.

**Repo evidence for that hypothesis:** **none.** Searched `config/schedules/` and git history: no `ROUTINE_CHANGE`, no `created_at`, no `updated_at` for Grok Bot automations. **UNVERIFIED pending Hive timestamps Don will paste.**

This is **not** SCHED-001. Do not fold (b) into (a). Do not close (a) because (b) might be calendar.

Miss sweep still treats a *closed* 06:30 or Friday 17:00 window without a completion row as a miss. It does not invent `created_at` to suppress that.

---

## US Pre-Market off-anchor (22:02 vs 23:00) — BRIEF-TAG family, not a miss

| Clock | Instant | UTC |
|---|---|---|
| Observed fire | 2026-09-18 22:02 AEST | 2026-09-18T12:02:00Z |
| Current Grok Bot US Pre-Market anchor | 23:00 Australia/Sydney | 2026-09-18T13:00:00Z |
| Lab yaml `pre_open` | 08:00 America/New_York (EDT) | 2026-09-18T12:00:00Z |
| Principal 30m-pre-open | 09:00 NY / 23:00 Syd | 2026-09-18T13:00:00Z |

**Delta vs 23:00 AEST:** `22:02 − 23:00` = **−3480 seconds** (58 minutes early). Off-anchor = `late` in heartbeat math (`|delta| > 300s`), not `missed` (a fire exists).

**Delta vs lab yaml 08:00 NY:** `12:02Z − 12:00Z` = **+120 seconds** (2 minutes after the NY 08:00 anchor).

**BRIEF-TAG-20260918:** Fri 18 pack is the 90m-pre-open (08:00 NY / 22:00 Syd) artifact vs the 30m-pre-open golden (09:00 NY / 23:00 Syd). The 22:02 AEST fire is that 90m pack, **related**. Incident stays OPEN (comparability). It is not SCHED-001.

---

## Reconstruction table (inception → 2026-09-19)

| Family | Routine | Anchor | Windows in evidence window | Fire | Delta vs listed anchor |
|---|---|---|---|---|---|
| lab | `lab.pulse.preopen` | 08:00 America/New_York | weekdays since 2026-09-16 14:34Z | Fri 18 ~22:02 AEST (Grok); sample 2026-09-16 brief generated 03:19Z 17 Sep (off-anchor) | Fri 18: +120s vs yaml; −3480s vs 23:00 Syd |
| lab | `lab.pulse.close` | 16:15 America/New_York | weekdays since Phase 3 | none in git | missed (no completion artifact) |
| lab | `lab.delivery.*` | 07:30–08:05 Australia/Sydney | weekdays as yaml enabled | none in git | missed (config, no runner) |
| grok_bot | `grok.sydney_morning_digest_8am` | 08:00 Australia/Sydney | weekday 08:00 windows **did occur** | none | **SCHED-001 missed** |
| grok_bot | `grok.sydney_morning` | 06:30 Australia/Sydney | Hive created_at **unverified** | NEVER RUN | (b) unverified |
| grok_bot | `grok.weekly_investment_review` | Fri 17:00 Australia/Sydney | Hive created_at **unverified** | NEVER RUN | (b) unverified |
| grok_bot | `grok.us_pre_market` | 23:00 Australia/Sydney | Fri 18 closed | 22:02 AEST | −3480s (BRIEF-TAG) |

---

## What would have caught (a)

`lab schedule miss-check` on a clock after Friday 08:00 AEST + 900s, with no completion row for `grok.sydney_morning_digest_8am` → exit 1 + `ops/reports/scheduler/incidents/YYYY-MM-DD-miss.md`.

That is the MERGE-BLOCKING control. Heartbeat-on-fire is the log that fills the completion row when something actually runs.
