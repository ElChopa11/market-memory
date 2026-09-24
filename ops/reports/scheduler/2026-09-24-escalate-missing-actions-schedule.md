# Escalate missing Actions schedule while the morning window is still open

Principal-ordered house lesson, 2026-09-24. Filed under `ops/reports/scheduler/` because [docs/runbooks/scheduler.md](../../../docs/runbooks/scheduler.md) has no lessons section (it only links the 2026-09-22 architecture lesson). No workflow YAML in this note.

## Log

1. **#115 was not on `main` during the 08:30 Sydney window.** Pull request #115 (08:30 duplicate cron) was never merged until after that window. The 08:30 slot was not a fire failure. There was no 08:30 cron on `main`.
2. **Morning DM run `35931476917` was a late schedule, not a skip and not a forced dispatch.** GitHub Actions run `35931476917` (`run_id` `actions-b1-35931476917`, completion `ops/reports/scheduler/completions/grok.sydney_morning__20260923T203000Z.json`) was `event=schedule` with Δ9120s (~2.5h late): anchor 06:30 Australia/Sydney (`2026-09-23T20:30:00Z`), actual `2026-09-23T23:02:00Z` (09:02 Sydney). Actions cron is unpredictable by hours. A 06:30 brief at 09:02 is useless. That is not the same claim as “the schedule may never run.”
3. **Escalate while the brief can still be used.** After the Grok clock, if there is no usable Actions deliver by ~07:00 Australia/Sydney (or ~15–30 minutes after the clock), Coord gives the Principal the one Run-workflow click. Do not invent auth gymnastics. Escalate when the brief is still missing near the useful window, not only when zero schedule runs exist.

## Lesson

| Field | Value |
|---|---|
| **Date** | 2026-09-24 |
| **run_id** | `actions-b1-35931476917` (Actions run `35931476917`) |
| **Desk** | Ops / Coord |
| **What happened** | Grok `sydney_morning` clock fired (~20:59Z, late versus 06:30 Australia/Sydney). Don treated that dry stamp as progress and spent the open window on 403 / device-code / sign-in loops. The morning DM was Actions run `35931476917`: `event=schedule`, Δ9120s (~2.5h late), actual 09:02 Sydney. #115 was never merged until after the 08:30 Sydney window, so that slot was not a fire failure — there was no 08:30 cron on `main`. |
| **Lesson** | After the Grok clock, if no usable Actions deliver has landed by ~07:00 Australia/Sydney (or ~15–30 minutes after the clock), Coord tells the Principal immediately and gives the one click: Actions → Run workflow → `hybrid-sydney-morning` (`.github/workflows/hybrid-sydney-morning.yml`) on `main` with `i_mean_it_deliver=true`. Escalate when the brief is still missing near the useful window, not only when zero schedule runs exist. Actions cron is unpredictable by hours (a 06:30 brief at 09:02 is useless). |
| **Related** | Dual cron (#115) is a backstop. It is not a substitute for this escalation. It was not on `main` for the 08:30 Sydney window on 2026-09-24. |
| **Does not** | Change workflow YAML. Treat a Grok dry stamp as Actions execution. Substitute device-code or sign-in loops for the Run-workflow click. Call the 08:30 slot a fire failure when no 08:30 cron was on `main`. Call run `35931476917` a skip or a forced dispatch. Treat “may never run” as the diagnosis. Authorise a Hive group send or lift `SEND_FROZEN`. |
| **Overrides prior** | No. Process lesson. The 2026-09-22 lock stands: Grok is a pure clock; Actions is execution. Minutes of cron drift remain drift. Hours late, such as a 06:30 brief at 09:02, is not a usable morning deliver. |

Paper only. No Telegram send. No group.
