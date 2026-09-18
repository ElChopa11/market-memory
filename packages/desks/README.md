# mm-desks

Phase 5d **desk runners**. Crypto (Tier 3a) and Equities (Tier 3b) plus Intel assemble, Quant, Skeptic, Risk, and Coord pack.

Protocol: `run(as_of, ctx) -> DeskOutput` with `OK|DEGRADED|FAILED`, `completeness_pct`, `provenance_ids`, artifacts.

```bash
uv run lab desk run --all --fixture tests/fixtures/phase5d/frozen_day.json --no-send --no-db
```

**Must not:** depend on the `mm_execution` module or signing; fetch Polygon (Intel/`mm_ingest`); submit orders; self-approve Skeptic/Risk. Telegram send is Coordinator `lab deliver` (IMP-013), not this package.


See [../../docs/runbooks/desks.md](../../docs/runbooks/desks.md) and [../../AGENTS.md](../../AGENTS.md).
