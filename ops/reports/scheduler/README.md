# Scheduler reports (IMP-042)

Miss sweep artifacts. Heartbeat-on-fire is a log; these files are the control trail.

| Path | What |
|---|---|
| [2026-09-19-sched-001-root-cause.md](2026-09-19-sched-001-root-cause.md) | Cause report. (a) 08:00 unexplained OPEN. (b) 06:30 / Fri 17:00 unverified. |
| [backfill-2026-09-19.md](backfill-2026-09-19.md) | Configured vs completions since lookback. |
| [2026-09-24-escalate-missing-actions-schedule.md](2026-09-24-escalate-missing-actions-schedule.md) | Principal house lesson 2026-09-24. Later that morning Actions did fire (`actions-b1-35931476917`, `event=schedule`, `delta_seconds=9120`, ~09:02 Sydney): hour-scale drift, not a permanent skip and not a forced `workflow_dispatch`. Escalate when a usable on-time deliver is still missing. #115 was unmerged during the 08:30 window. |
| `incidents/YYYY-MM-DD-miss.md` | OPEN escalation from `lab schedule miss-check` (generated). |
| [completions/](completions/) | Hive → lab CLI completion JSON. Miss-check reads these. |
| [completions/receipts/](completions/receipts/) | Sydney Morning deliver receipts keyed on `scheduled_anchor_ts`. Not completion rows. Miss-check does not read them. |
| `known-missed-baseline.yaml` | Generated. Pre-today (Australia/Sydney) closed windows labeled known-missed. Not deleted. |

SCHED-001 is **CLOSED** citing run_id `actions-b1-35727756341` (hybrid-sydney-morning #1 Success ~21s; stamp commit `857f55c` on `main`, completions/ only). Principal 2026-09-22: Grok is a pure clock plus agent wake (run_id `box-us-pre-20260922T133710Z`; degrade-to-dry is permanent; no standing Auto-review allow). Actions is execution (fetch, brief, deliver; the runner is ephemeral and auditable by construction; Stage 1 stamp is this close). The box is interactive desk work, not a production host. Panel SCHEDULE cron and panel WEBHOOK are dead. Close pack: [incident-closures/20260922-sched-001-actions-invoker-close.md](../incident-closures/20260922-sched-001-actions-invoker-close.md). ADR: [ADR/0019-grok-clock-actions-execution.md](../../../ADR/0019-grok-clock-actions-execution.md). Next on-anchor test: 06:30 Australia/Sydney (forced-dispatch `late` is not that test). Minutes of Actions cron drift are accepted as drift. Both AEST crons stay; every fire stamps.

A drifted cron (or second trigger) arriving after a successful deliver for that anchor is a silent no-op / already_delivered, not a failure or miss.

Operator once (Monday visible, history labeled):

```bash
uv run lab migrate   # creates schedule_heartbeat if missing
uv run lab schedule miss-check --baseline-before today --no-db
```
