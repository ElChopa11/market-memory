# Scheduler reports (IMP-042)

Miss sweep artifacts. Heartbeat-on-fire is a log; these files are the control trail.

| Path | What |
|---|---|
| [2026-09-19-sched-001-root-cause.md](2026-09-19-sched-001-root-cause.md) | Cause report. (a) 08:00 unexplained OPEN. (b) 06:30 / Fri 17:00 unverified. |
| [backfill-2026-09-19.md](backfill-2026-09-19.md) | Configured vs completions since lookback. |
| `incidents/YYYY-MM-DD-miss.md` | OPEN escalation from `lab schedule miss-check` (generated). |
| [completions/](completions/) | Hive → lab CLI completion JSON. Miss-check reads these. |
| `known-missed-baseline.yaml` | Generated. Pre-today (Australia/Sydney) closed windows labeled known-missed. Not deleted. |

SCHED-001 is **CLOSED** citing run_id `actions-b1-35727756341` (hybrid-sydney-morning #1 Success ~21s; stamp commit `857f55c` on `main`, completions/ only). Two clocks: Actions durable commit-back (PR #90) and Grok Bot app routines (run_id `box-us-pre-20260922T133710Z`). Panel SCHEDULE cron and panel WEBHOOK are dead. Close pack: [incident-closures/20260922-sched-001-actions-invoker-close.md](../incident-closures/20260922-sched-001-actions-invoker-close.md). Next on-anchor test: 06:30 Australia/Sydney (forced-dispatch `late` is not that test). Auto-review on the Grok path is an open Principal question (observed degrade to dry `--no-db`, DQ unavailable).

Operator once (Monday visible, history labeled):

```bash
uv run lab migrate   # creates schedule_heartbeat if missing
uv run lab schedule miss-check --baseline-before today --no-db
```
