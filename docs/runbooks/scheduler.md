# Scheduler miss sweep (IMP-042)

The clock is true only if a **closed window without a completion row is a miss**. Heartbeat-on-fire is a log. Canaries are out of scope.

```bash
# Control (MERGE-BLOCKING). Fixture clock in CI.
uv run lab schedule miss-check \
  --fixture tests/fixtures/scheduler/ci_clock.yaml \
  --now 2026-09-19T09:49:00Z \
  --no-db

# Same control (alias). Not a heartbeat dump.
uv run lab schedule heartbeat-check --fixture tests/fixtures/scheduler/ci_clock.yaml --now 2026-09-19T09:49:00Z --no-db

# Prove the 08:00 class escalates:
uv run lab schedule miss-check --fixture tests/fixtures/scheduler/miss_clock.yaml --now 2026-09-19T09:49:00Z --no-db --out /tmp/sched-miss

# Secondary log (does not pass the check by itself):
uv run lab schedule record-fire --routine-id lab.pulse.preopen --fired-at 2026-09-18T12:02:00Z --no-db

# Backfill markdown:
uv run lab schedule backfill --fixture tests/fixtures/scheduler/miss_clock.yaml --now 2026-09-19T09:49:00Z --no-db --out /tmp/sched
```

Catalog composition:

- Grok Bot / Hive: `config/schedules/routines.yaml` (no `created_at` in repo)
- Lab Pulse: `config/schedules/market-pulse.yaml`
- Lab Telegram wall-clock: `config/delivery/telegram.yaml` `schedule`

SCHED-001 stays OPEN. Root cause: [ops/reports/scheduler/2026-09-19-sched-001-root-cause.md](../../ops/reports/scheduler/2026-09-19-sched-001-root-cause.md).
