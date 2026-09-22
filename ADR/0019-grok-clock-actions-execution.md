# ADR 0019 — Grok is a pure clock; Actions is execution

- **Status:** Accepted
- **Phase:** Principal 2026-09-22. Paper only. No live trading. No signing. No Telegram send. SCHED-001 stays **CLOSED** on run_id `actions-b1-35727756341`. Stage 2 is not built.

## Context

The same-night close of SCHED-001 proved a GitHub Actions stamp (`actions-b1-35727756341`, commit `857f55c` on `main`, `ops/reports/scheduler/completions/` only) and then described Actions as the only working clock. That was too broad.

The same day, a Grok Bot app routine woke an agent and wrote a completion: run_id `box-us-pre-20260922T133710Z` (`ops/reports/scheduler/completions/grok.us_pre_market__20260922T130000Z.json`). Auto-review blocked `--live`. The fire degraded to dry `--no-db` with DQ unavailable.

Panel SCHEDULE cron is dead (7 routines, 0 fires). Panel WEBHOOK is dead (C1 silent).

## Decision

| Path | Role |
|---|---|
| Grok Bot routine | Pure clock + agent wake only. Stamps completions and wakes a desk for interactive work. No live fetch. No delivery. Degrade-to-dry (`--no-db`, DQ unavailable) is permanent correct behaviour. No standing Auto-review allow. |
| GitHub Actions | Execution. Fetch, brief, and deliver. The runner is ephemeral: it runs the CLI and commits the output. Auditable by construction. |
| Bot box | Interactive desk work only. Not a production host. |
| Panel SCHEDULE cron | Dead. |
| Panel WEBHOOK | Dead. |

B1 Stage 1 (PR #90, simplified by PR #99) is still a stamp of `grok.sydney_morning` on one AEST cron (`30 20 * * 0-4` UTC). Every fire stamps. Fetch, brief, and Principal-DM delivery are Stage 2 and are not in this ADR’s code.

## Why

1. **Disposable runner.** The Actions runner is destroyed after every job. It keeps no persistent state, cookie seeds, screenshots, or autorecovery. Credential exposures this week came from shared-box state.
2. **Different egress.** Actions leaves the box network. That may fix keyless API 429s that backoff only mitigates.
3. **Auditable by construction.** The record is the log, `run_id`, commit, and diff. An agent-chosen report is not that record.
4. **No standing Auto-review allow.** A standing allow would permanently widen the path for an occasional need. Principal rejected that trade.

## Consequences

- Degrade-to-dry on a Grok-routine fire stays the correct behaviour. There is no standing Auto-review allow for `--live`.
- Actions is the execution path. The box is not a production host. Neon/R2 credentials, when wired, go to Actions secrets, not the box. A separate Telegram bot for Actions stands (two credential stores, two blast radii). Those follow-ons are recorded and not built.
- Stage 2 (Actions delivers a real pack to the Principal DM) is the next build. This ADR does not implement it. Hive group stays `SEND_FROZEN`.
- Minutes of Actions cron drift on the 06:30 digest are accepted as drift. This ADR does not add a ±900s skip, a force flag, or a second cron to `.github/workflows/hybrid-sydney-morning.yml`. That file stays the #99 shape: one AEST cron, every fire stamps.
- House lesson: [config/knowledge/house-lessons.md](../config/knowledge/house-lessons.md) (2026-09-22 Principal decision, run_id `box-us-pre-20260922T133710Z`). Miss-detector ADR: [0018-schedule-heartbeat.md](0018-schedule-heartbeat.md).
