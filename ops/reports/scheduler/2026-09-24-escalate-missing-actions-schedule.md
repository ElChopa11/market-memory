# Escalate missing Actions schedule while the morning window is still open

Principal-ordered house lesson, 2026-09-24. Filed under `ops/reports/scheduler/` because [docs/runbooks/scheduler.md](../../../docs/runbooks/scheduler.md) has no lessons section (it only links the 2026-09-22 architecture lesson). No workflow YAML in this note.

## Log

1. **Later that morning Actions did fire as `event=schedule`.** `run_id` `actions-b1-35931476917` / Actions run `35931476917`. `scheduled_anchor` `2026-09-23T20:30:00Z`. Fired ~`2026-09-23T23:02:00Z`. `delta_seconds=9120` (~2.5h late / ~09:02 Sydney). Completion: `ops/reports/scheduler/completions/grok.sydney_morning__20260923T203000Z.json`. This was hour-scale drift, not a permanent skip and not a forced `workflow_dispatch`.
2. **Actions cron is unpredictable by hours.** A 06:30 brief at 09:02 is useless. Escalate when a usable on-time deliver is still missing in the morning window — not only when zero schedule runs exist forever.
3. **#115 was unmerged during the 08:30 Sydney window.** That slot was not a real test: there was no 08:30 cron on `main`. After the Grok clock, if no usable on-time Actions deliver has landed by ~07:00 Australia/Sydney (or ~15–30 minutes after the clock), Coord gives the Principal the one Run-workflow click: Actions → Run workflow → `hybrid-sydney-morning` (`.github/workflows/hybrid-sydney-morning.yml`) on `main` with `i_mean_it_deliver=true`. Do not invent auth gymnastics. Dual cron (#115) is a backstop, not a substitute for this escalation.

Grok `sydney_morning` clock fired (~20:59Z, late versus 06:30 Australia/Sydney). Don treated that dry stamp as progress and spent the open window on 403 / device-code / sign-in loops.

## Lesson

| Field | Value |
|---|---|
| **Date** | 2026-09-24 |
| **run_id** | `actions-b1-35931476917` (Actions run `35931476917`) |
| **Desk** | Ops / Coord |
| **What happened** | Later that morning Actions did fire as `event=schedule`: `run_id` `actions-b1-35931476917` / Actions run `35931476917`, `scheduled_anchor` `2026-09-23T20:30:00Z`, fired ~`2026-09-23T23:02:00Z`, `delta_seconds=9120` (~2.5h late / ~09:02 Sydney). Hour-scale drift, not a permanent skip and not a forced `workflow_dispatch`. #115 was unmerged during the 08:30 Sydney window, so that slot was not a real test. Grok `sydney_morning` clock fired (~20:59Z). Don treated the dry stamp as progress and spent the open window on 403 / device-code / sign-in loops. |
| **Lesson** | Actions cron is unpredictable by hours (a 06:30 brief at 09:02 is useless). Escalate when a usable on-time deliver is still missing in the morning window — not only when zero schedule runs exist forever. After the Grok clock, if none has landed by ~07:00 Australia/Sydney (or ~15–30 minutes after the clock), Coord gives the Principal one click: Run workflow `hybrid-sydney-morning` on `main` with `i_mean_it_deliver=true`. Dual cron is a backstop, not a substitute. |
| **Related** | #115 was unmerged during the 08:30 window, so that slot was not a real test. |
| **Does not** | Change workflow YAML. Treat a Grok dry stamp as Actions execution. Substitute device-code or sign-in loops for the Run-workflow click. Call the 08:30 slot a real test while #115 was unmerged. Call run `35931476917` a permanent skip or a forced `workflow_dispatch`. Wait forever for zero schedule runs before escalating. Authorise a Hive group send or lift `SEND_FROZEN`. |
| **Overrides prior** | No. Process lesson. The 2026-09-22 lock stands: Grok is a pure clock; Actions is execution. |

Paper only. No Telegram send. No group.
