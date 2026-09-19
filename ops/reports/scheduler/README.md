# Scheduler reports (IMP-042)

Miss sweep artifacts. Heartbeat-on-fire is a log; these files are the control trail.

| Path | What |
|---|---|
| [2026-09-19-sched-001-root-cause.md](2026-09-19-sched-001-root-cause.md) | Cause report. (a) 08:00 unexplained OPEN. (b) 06:30 / Fri 17:00 unverified. |
| [backfill-2026-09-19.md](backfill-2026-09-19.md) | Configured vs completions since lookback. |
| `incidents/YYYY-MM-DD-miss.md` | OPEN escalation from `lab schedule miss-check` (generated). |

SCHED-001 stays OPEN until a verified on-anchor fire. Do not close on “no window yet”.
