# Eleven-capture value test

Principal ruling, 2026-09-25.

## 1. Purpose

Everything built before session eleven either serves this question or doesn't happen: can the brief tell the Principal something he doesn't already know? It re-asks P0's question after eleven captures.

## 2. Informative (the score)

A morning scores Y if the Principal can name one specific line in the brief that told him something he didn't know and wouldn't have got from glancing at a chart, and that line isn't stale or wrong. Everything else scores N, including a brief that was merely correct. "Wouldn't have got from a chart glance" is the whole bar, and the Principal judges it in the moment. For each morning he also records WHY in one sentence. The WHY doesn't affect the score. It is for the session-eleven post-mortem, to see whether the Ys clustered on one panel or were scattered.

## 3. Scoring

The Principal scores alone. No desk scores a brief. Each morning gets Y or N plus the quoted line, on the same day before 10:00 AEST, which is before that session plays out. A score recorded later doesn't count. The Principal commits the row to the scoresheet table in this file. The git commit date is untrusted: whoever makes the commit sets it, and it can be backdated, so it is not evidence. The evidence is GitHub's server-side push time for the commit that adds the row, as shown in the repository activity log or the push event. A score whose push time is later than 10:00 AEST on that day doesn't count.

## 4. Which ten count

Captures 2 through 11. Capture 1 has no prior capture and can't produce a delta. A missed morning scores N and is not skipped. A brief that doesn't arrive is N, because the system failing to deliver is a failure of the system, not an excused absence.

## 5. Acted (a separate field)

Each morning the Principal also records whether he ACTED on anything in the brief, Y or N. It has no bearing on the score. A brief can be informative and still useless. At session eleven both columns are read together. Informative without action is its own finding and does not pass on its own.

## 6. Decision at session eleven

0 to 2 Y out of 10: STOP building panels and pivot. 3 or more Y out of 10: continue. There is no middle band and no review band, because a test with a review band is a test that gets argued. The bar won't be extended or moved.

Why 2 is a stop, recorded so it isn't relitigated: the bar was set against P0's honest count of 1 in 10. Two is one morning better than changing nothing. If eleven captures and a persistence layer only move the count from 1 to 2, the next month of building doesn't pay for itself.

What STOP means: it does not mean shutting down. It means stopping work on the signal generator and redirecting to measuring the Principal's own trading, meaning expectancy by setup type, by instrument and by regime, from his actual fills. That is the shorter project, and it answers a question about his money rather than about the market. The infrastructure stays. The direction changes.

## 7. Scoresheet

| capture # | date (AEST) | brief delivered (Y/N) | informative (Y/N) | line quoted | WHY (one sentence) | acted (Y/N) | counts (Y for captures 2–11) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | | N |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| 5 | 2026-10-02 | Y | N | — (none; score MISSED) | No pre-10:00 AEST Principal score existed; missed morning counts as N per §4. | | Y |
| 6 | 2026-10-05 | Y | N | — (none; score MISSED) | No pre-10:00 AEDT Principal score existed; missed morning counts as N per §4. | | Y |
| 7 | 2026-10-06 | N | N | — (none; score MISSED) | Brief did not arrive; a brief that does not arrive is N per §4, and an outage is not an excused absence. | | Y |
| 8 | 2026-10-07 | Y | N | — (none; score MISSED) | No pre-10:00 AEDT Principal score existed; missed morning counts as N per §4. | | Y |
| 9 | 2026-10-08 | Y | Y | "NEAR fund 45.42% ann" | NEAR rallied +5.5% against a falling tape with longs paying 45% annualised — the move is crowded leverage, not visible on a price chart. | N | Y |
| 10 | 2026-10-09 | Y | N | — (none; score MISSED) | No pre-10:00 AEDT Principal score existed; missed morning counts as N per §4. | | Y |
| 11 | | | | | | | |

C5 score filed post-window as MISSED→N per Principal 2026-10-02; push after 10:00 AEST by design for a miss log.

C6 score filed post-window as MISSED→N per Principal 2026-10-05; push after 10:00 AEDT by design for a miss log.
C6 observation: GitHub-cron backup runs 37243560492 and 37249891043 wrote completion rows fbac379 and 2db4f7d with status=late for the same 19:30Z slot; no second deliver receipt, so no second send.

C7 score filed post-window as MISSED→N per Principal 2026-10-06; push after 10:00 AEDT by design for a miss log.
C7 observation: Host dispatch run 37363787185 fired at 19:30:03Z (06:30 AEDT) but stage1-stamp never got a runner (runner_id 0, no steps) and was cancelled at 19:45:07Z; render-proof, capture-proof and brief-and-deliver were skipped; no completion or deliver receipt. Cause: GitHub status incident 3q1yb5m7ltvb, Incident with Actions, roughly 19:11Z to 22:49Z on 5 Oct (06:11 to 09:49 AEDT 6 Oct), runner assignment delays escalating to major outage.
C7: equity data pre-close by design — NY market still open at 06:30 AEDT capture time.

C8 score filed post-window as MISSED→N per Principal window close 2026-10-07; push after 10:00 AEDT by design for a miss log.
C8: equity data pre-close by design — NY market still open at 06:30 AEDT capture time.

C9 scored Y by the Principal at 08:42 AEDT on 2026-10-08, before the 10:00 window close. Brief delivered 06:31:04 AEDT (run 37674941386, receipt e0fd5d7).
C9: equity data pre-close by design — NY market still open at 06:30 AEDT capture time.

C10 score filed post-window as MISSED→N per Principal window close 2026-10-09; push after 10:00 AEDT by design for a miss log.
C10 delivery: run 37832406914, receipt actions-b1-37832406914, sent 06:31 AEDT (sent=true).
C10: equity data pre-close by design — NY market still open at 06:30 AEDT capture time.

**Standing checkpoint, interim read at capture 5 or 6 (Principal ruling 2026-10-03, written before any C6 data exists):**
At capture 5 or capture 6, whichever lands next, the Principal takes a short honest interim read. It is not a formal re-score. Across the mornings so far: did anything in the brief feel like it told something real, even informally, even outside the strict Y/N scoring rule in §2? This is not a shortcut around the full ten-morning test. It does not change the 3-of-10 bar in §6. It does not let anyone relitigate a score already logged. It is a cheap five-minute gut-check, so that if the honest signal is clearly weak early, that shows up before more infrastructure is built on an unconfirmed signal, rather than only at capture 11. This checkpoint influences nothing automatically. It is informational only, for the Principal's awareness. It is not a trigger for any action.
C5 is already scored MISSED→N (informative). Equity-print PASS and set2 are separate lanes. The interim gut-check is about brief informativeness across mornings, not the equity-print gate.

**DST note, captures 7–10 (Principal ruling 2026-09-28: the brief stays at 06:30 Australia/Sydney through the DST change on Sun 4 Oct 2026):**
Captures 7 (Tue 6 Oct 2026), 8 (Wed 7 Oct 2026), 9 (Thu 8 Oct 2026) and 10 (Fri 9 Oct 2026) carry this label:
"equity data pre-close by design — NY market still open at 06:30 AEDT capture time."
This label is recorded on a separate notes line for the capture, never in the WHY cell. The WHY cell is the Principal's scoring evidence, not a system caveat.
Sydney local time is AEDT (UTC+11) from Sun 4 Oct 2026, so 06:30 local is 19:30Z, which is 15:30 EDT, 30 minutes before the 16:00 NY cash close.
This is not a defect and not a missed capture. It gets the same treatment as the `EQUITY T-1 BY DESIGN` label: the morning is still delivered, counted and scored Y/N on the normal §2 bar, and a pre-close equity row is not "stale or wrong" for scoring.
Captures 6 (Mon 5 Oct) and 11 (Mon 12 Oct) are not affected, because 06:30 local on a Monday is Sunday afternoon in New York.
