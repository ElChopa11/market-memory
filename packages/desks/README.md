# mm-desks

Phase 5d **desk runners** plus Phase 6a **PG LISTEN/NOTIFY mesh** (no Redis) plus Phase 6b **flow/macro Intel sleeves** plus Phase 6c **PLAYBOOK ladder** plus Phase 6c-1 **five-desk roster** plus Phase 6c-2 **naming layer** plus Phase 6c-4 **watchlist monitor** plus Phase 6c-5 **Ops-owned delivery** plus Phase 6d **listings / IPO screen** plus Phase 6e **pack scorecards + queue hygiene** (Intel, Research, Quant, IC/Risk, Ops). Don/Coord is orchestration only.

# Boundary: a comment containing mm_execution must not fail CI (statement-anchored grep).

Protocol: `run(as_of, ctx) -> DeskOutput` with `OK|DEGRADED|FAILED`, cadence, envelope header, `content_hash`.

```bash
uv run lab desk run --all --fixture tests/fixtures/phase5d/frozen_day.json --no-send --no-db
uv run lab mesh dry --fixture tests/fixtures/phase5d/frozen_day.json --no-db
uv run lab watchlist scan --fixture tests/fixtures/phase6c4/locked_scan.json --no-send --no-db
uv run lab deliver watchlist --fixture tests/fixtures/phase6c4/locked_scan.json --no-send --no-db
uv run lab listings scan --fixture tests/fixtures/phase6d/listing_day.json --no-send --no-db
uv run lab deliver listings --fixture tests/fixtures/phase6d/listing_day.json --no-send --no-db
uv run lab scorecard compare --fixture tests/fixtures/phase6e/packs.json --no-send --no-db
uv run lab deliver scorecard --fixture tests/fixtures/phase6e/packs.json --no-send --no-db
uv run lab queue check
uv run lab base-rate compute --fixture tests/fixtures/phase1_base_rates/panel.json --no-db
```

**Must not:** depend on the `mm_execution` module or signing; fetch Polygon (Intel/`mm_ingest`); submit orders; self-approve Skeptic/Risk; import Redis; call a live LLM as calculator/router. Telegram send is Ops-owned `lab deliver` / `lab deliver fanout` / `lab deliver watchlist` / `lab deliver listings` (IMP-013 / IMP-016 / IMP-021 / IMP-017), not this package. PLAYBOOK: [../../docs/playbook.md](../../docs/playbook.md).


See [../../docs/runbooks/desks.md](../../docs/runbooks/desks.md) and [../../AGENTS.md](../../AGENTS.md).
