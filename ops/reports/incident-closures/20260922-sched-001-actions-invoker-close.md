# SCHED-001 CLOSED — two clocks on record (2026-09-22)

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
| **Invoker** | Two clocks. Actions B1 ([#90](https://github.com/ElChopa11/market-memory/pull/90)) is the durable commit-back path for Sydney Morning Stage 1. Grok Bot app routines are the agent-shaped clock (run_id `box-us-pre-20260922T133710Z`). |
| **House lesson** | [config/knowledge/house-lessons.md](../../../config/knowledge/house-lessons.md) — 2026-09-22 two clocks; panel SCHEDULE and WEBHOOK dead; SCHED-001 stays CLOSED on `actions-b1-35727756341` |

## Invoker record (corrected the same day)

The first draft of this close said the panel was never a viable invoker and that Actions was the invoker. That was too broad. Precise record:

| Path | State | Evidence |
|---|---|---|
| Panel SCHEDULE cron | Dead | 7 routines, 0 fires |
| Panel WEBHOOK | Dead | C1 silent |
| Grok Bot app routine | Works | Wakes an agent; the agent runs the CLI; the stamp lands. run_id `box-us-pre-20260922T133710Z` (`ops/reports/scheduler/completions/grok.us_pre_market__20260922T130000Z.json`) |
| GitHub Actions B1 | Works | Durable commit-back for Sydney Morning Stage 1. run_id `actions-b1-*` (this close: `actions-b1-35727756341`) |

1. Actions = durable stamp commit-back to `main` (`completions/` only).
2. Grok Bot app routines = agent-shaped clock that can drive the box CLI and a local stamp.

Grok-path limitation: depends on an agent being awake and on Auto-review allowing the Shell call. On 2026-09-22 US Pre-Market, Auto-review blocked `--live`, so the fire correctly degraded to dry `--no-db` with DQ unavailable. Open question for the Principal: is Auto-review configurable for this path, or is the path permanently dry-only? If permanently dry-only, the Grok path is a clock and nothing more.

Cron live on `main`; next on-anchor test is 06:30 Australia/Sydney without Principal action. SCHED-001 stays CLOSED on `actions-b1-35727756341`.

## Does not

- Lift `SEND_FROZEN` / authorise Hive group Telegram.
- Treat forced-dispatch `late` as the on-anchor acceptance test.
- Reopen panel SCHEDULE cron or panel WEBHOOK as a clock.
