# mm-briefing-worker

Phase 3 Market Pulse worker: `briefing-worker once|next|run`.

**Must not:** execute trades. Alert pushes require threshold config.

```bash
uv run briefing-worker once --kind preopen --fixture tests/fixtures/briefing/frozen_day.json --no-db
uv run briefing-worker next --from 2026-03-06T00:00:00Z --days 5
```

See [../../docs/runbooks/market-pulse.md](../../docs/runbooks/market-pulse.md).
