# SCHED-001 CLOSED — Actions invoker (2026-09-22)

Paper only. No Telegram send. Hive group stays frozen.

| Field | Value |
|---|---|
| **Ticket** | SCHED-001 |
| **Status** | CLOSED |
| **run_id** | `actions-b1-35727756341` |
| **Job** | hybrid-sydney-morning #1 Success ~21s, `stage1-stamp` green |
| **Stamp** | commit `857f55c` on `main` by `github-actions[bot]`; path scoped to `ops/reports/scheduler/completions/` only |
| **Routine** | `grok.sydney_morning` |
| **scheduled_for** | `2026-09-21T20:30:00Z` |
| **actual** | `2026-09-22T12:32:21Z` |
| **delta_seconds** | `57741` |
| **status** | `late` (correct for forced dispatch vs yesterday's anchor) |
| **Completion row** | [ops/reports/scheduler/completions/grok.sydney_morning__20260921T203000Z.json](../scheduler/completions/grok.sydney_morning__20260921T203000Z.json) |
| **Invoker** | B1 Stage 1 PR [#90](https://github.com/ElChopa11/market-memory/pull/90) — Actions cron + durable completion commit-back |
| **House lesson** | [config/knowledge/house-lessons.md](../../../config/knowledge/house-lessons.md) — 2026-09-22 panel scheduler dead; Actions is the invoker |

## Invoker finding (cite exactly)

Panel was never a viable invoker: seven routines, two boxes, zero fires, including a webhook path (C1 silent). Fix was not configuration — move execution somewhere that provably runs. Controls belong on the path that executes.

Cron live on `main`; next on-anchor test is 06:30 Australia/Sydney without Principal action.

## Does not

- Lift `SEND_FROZEN` / authorise Hive group Telegram.
- Treat forced-dispatch `late` as the on-anchor acceptance test.
- Reopen Grok/Hive panel as the clock.
