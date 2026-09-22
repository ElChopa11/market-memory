# SCHED-001 CLOSED — Grok clock, Actions execution (2026-09-22)

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
| **Invoker** | Principal 2026-09-22. Grok = pure clock + agent wake (run_id `box-us-pre-20260922T133710Z`). Actions = execution (B1 [#90](https://github.com/ElChopa11/market-memory/pull/90); this close `actions-b1-35727756341`). Box = interactive desk work, not a production host. ADR: [ADR/0019-grok-clock-actions-execution.md](../../../ADR/0019-grok-clock-actions-execution.md). |
| **House lesson** | [config/knowledge/house-lessons.md](../../../config/knowledge/house-lessons.md) — 2026-09-22 Principal decision: Grok pure clock; Actions execution. SCHED-001 stays CLOSED on `actions-b1-35727756341` |

## Invoker record (Principal decision, same day)

The first draft of this close said the panel was never a viable invoker and that Actions was the only invoker. That was too broad. A later draft left Auto-review as an open question. Principal locked the roles the same day:

| Path | Role | Evidence |
|---|---|---|
| Panel SCHEDULE cron | Dead | 7 routines, 0 fires |
| Panel WEBHOOK | Dead | C1 silent |
| Grok Bot app routine | Pure clock + agent wake | Stamps a completion and wakes a desk for interactive work. No live fetch. No delivery. run_id `box-us-pre-20260922T133710Z` (`ops/reports/scheduler/completions/grok.us_pre_market__20260922T130000Z.json`). Auto-review blocked `--live`. Degrade-to-dry (`--no-db`, DQ unavailable) is permanent. No standing Auto-review allow. |
| GitHub Actions | Execution | Fetch, brief, deliver. The runner is ephemeral: it runs the CLI and commits the output. Auditable by construction. This close is the Stage 1 stamp: `actions-b1-35727756341`. |
| Bot box | Interactive desk work | Not a production host. |

Why:

1. The Actions runner is destroyed after every job (no persistent state, cookie seeds, screenshots, or autorecovery). Credential exposures this week came from shared-box state.
2. Actions has different egress. That may fix keyless API 429s that backoff only mitigates.
3. Actions is auditable by construction (log, `run_id`, commit, diff).
4. A standing Auto-review allow would permanently widen the path for an occasional need. Principal rejected that trade.

Follow-on decisions, not built in the record that states them: Neon/R2 credentials go to Actions secrets, not the box; a separate Telegram bot for Actions stands (two blast radii); Stage 2 is the right next build (Actions delivers a real pack to the Principal DM); minutes of Actions cron drift on the 06:30 digest are accepted as drift.

Cron live on `main` is one AEST cron (`30 20 * * 0-4`, PR #99). Every fire stamps. Next on-anchor test is 06:30 Australia/Sydney without Principal action. SCHED-001 stays CLOSED on `actions-b1-35727756341`.

## Does not

- Lift `SEND_FROZEN` / authorise Hive group Telegram.
- Treat forced-dispatch `late` as the on-anchor acceptance test.
- Reopen panel SCHEDULE cron or panel WEBHOOK as a clock.
- Treat the box as a production host, or grant a standing Auto-review allow for Grok `--live`.
- Implement Stage 2, Neon/R2 wiring, or a second Actions bot in this close pack. Those are recorded follow-ons.
- Add a ±900s skip, a force flag, or a second cron to `.github/workflows/hybrid-sydney-morning.yml`.
