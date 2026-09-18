# mm-desks

Phase 5d **desk runners** plus Phase 6a **PG LISTEN/NOTIFY mesh** (no Redis). Crypto (Tier 3a) and Equities (Tier 3b) plus Intel assemble, Quant, Skeptic, Risk, and Coord pack.

Protocol: `run(as_of, ctx) -> DeskOutput` with `OK|DEGRADED|FAILED`, cadence, envelope header, `content_hash`.

```bash
uv run lab desk run --all --fixture tests/fixtures/phase5d/frozen_day.json --no-send --no-db
uv run lab mesh dry --fixture tests/fixtures/phase5d/frozen_day.json --no-db
```

**Must not:** depend on the `mm_execution` module or signing; fetch Polygon (Intel/`mm_ingest`); submit orders; self-approve Skeptic/Risk; import Redis. Telegram send is Coordinator `lab deliver` (IMP-013), not this package.


See [../../docs/runbooks/desks.md](../../docs/runbooks/desks.md) and [../../AGENTS.md](../../AGENTS.md).
