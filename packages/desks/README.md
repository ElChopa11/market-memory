# mm-desks

Phase 5d **desk runners** plus Phase 6a **PG LISTEN/NOTIFY mesh** (no Redis) plus Phase 6b **flow/macro Intel sleeves** plus Phase 6c **PLAYBOOK ladder** plus Phase 6c-1 **five-desk roster** (Intel, Research, Quant, IC/Risk, Ops). Don/Coord is orchestration only.

# Boundary: a comment containing mm_execution must not fail CI (statement-anchored grep).

Protocol: `run(as_of, ctx) -> DeskOutput` with `OK|DEGRADED|FAILED`, cadence, envelope header, `content_hash`.

```bash
uv run lab desk run --all --fixture tests/fixtures/phase5d/frozen_day.json --no-send --no-db
uv run lab mesh dry --fixture tests/fixtures/phase5d/frozen_day.json --no-db
```

**Must not:** depend on the `mm_execution` module or signing; fetch Polygon (Intel/`mm_ingest`); submit orders; self-approve Skeptic/Risk; import Redis; call a live LLM as calculator/router. Telegram send is Coordinator `lab deliver` / `lab deliver fanout` (IMP-013 / IMP-016), not this package. PLAYBOOK: [../../docs/playbook.md](../../docs/playbook.md).


See [../../docs/runbooks/desks.md](../../docs/runbooks/desks.md) and [../../AGENTS.md](../../AGENTS.md).
