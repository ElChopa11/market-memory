# Escalate missing Actions schedule while the morning window is still open

Principal-ordered house lesson, 2026-09-24. Filed under `ops/reports/scheduler/` because [docs/runbooks/scheduler.md](../../../docs/runbooks/scheduler.md) has no lessons section (it only links the 2026-09-22 architecture lesson). No workflow YAML in this note. No `run_id` invented.

| Field | Value |
|---|---|
| **Date** | 2026-09-24 |
| **run_id** | *(none — Principal process lesson. Do not invent one.)* |
| **Desk** | Ops / Coord |
| **What happened** | Grok `sydney_morning` clock fired (~20:59Z, late versus 06:30 Australia/Sydney). The Actions schedule did not fire at 06:30 Sydney. During that morning window, #115 (08:30 duplicate cron) was still an open PR and not on `main`, so 08:30 that morning could not have been a real test. Don under-escalated: treated the Grok dry stamp as progress and spent the open window on 403 / device-code / sign-in loops instead of a clear Principal Run click. |
| **Lesson** | When the Actions schedule is absent after the Grok clock plus about 15–30 minutes, or by 07:00 Australia/Sydney on a Sydney-morning day, Coord tells the Principal immediately. The one path is Actions → Run workflow → `hybrid-sydney-morning` (`.github/workflows/hybrid-sydney-morning.yml`) on `main` with `i_mean_it_deliver=true`. Do not invent auth gymnastics. |
| **Related** | GitHub Actions cron is best-effort and can skip. Dual cron (#115) is a backstop, not a substitute for this escalation. |
| **Does not** | Change workflow YAML. Treat a Grok dry stamp as Actions execution. Substitute device-code or sign-in loops for the Run-workflow click. Treat an unmerged duplicate cron as a test that already ran. Authorise a Hive group send or lift `SEND_FROZEN`. |
| **Overrides prior** | No. Process lesson with no persist `run_id`. The 2026-09-22 lock stands: Grok is a pure clock; Actions is execution. |

Paper only. No Telegram send. No group.
