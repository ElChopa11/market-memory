# PLAN — IMP-030 Phase 6e scorecards + queue automation

**Report status:** IN_REVIEW (this PR).  
**Owner:** Quant (score math) / Ops (queue hygiene + delivery)  
**Scope:** Phase 6e — like-for-like pack scorecards with provenance + improvement-queue hygiene helpers. No live trading. No execution. No `live.yaml`. No Redis. No 6f decay-watch.

## Why

6d listings/IPO is on main (#54). Operators still lacked a standing product that scores desk packs **like-for-like** with provenance, and a helper that enforces the single-threaded READY→IN_PROGRESS slot. BRIEF-TAG-20260918 (90m vs 30m pre-open) must stay honest: it is not a 30m-pre-open golden.

## Outcome

- Queue: IMP-017 DONE (#54). IMP-030 this thread. IMP-031 / 6f PARKED. OPEN incidents untouched.
- `lab scorecard compare --fixture PATH --no-send` emits a deterministic Quant artifact.
- Naming via `mm_common.naming` (`scorecard` is a Quant sleeve, not a sixth desk).
- Mesh envelope on `desk.quant.output`. Ops `lab deliver scorecard` inherits `content_hash`.
- Like-for-like only when `product`, `schedule_anchor`, and `universe` match and no incomparable tag applies.
- BRIEF-TAG-20260918 tagged in `config/scorecards/tags.yaml`; 90m vs 30m is `NOT_COMPARABLE`. Incident stays OPEN.
- Queue helper `lab queue check` / `scripts/check_queue.py`: at most one IMP-* `IN_PROGRESS`; OPEN incidents do not occupy the slot. `lab queue can-start` is a dry READY→IN_PROGRESS aid. **No auto-merge. No gate waiver.**
- Decay *inputs* (prompt hashes) are stubbed; `watch_enabled: false`. Full prompt-hash decay watch is IMP-031.
- Zero LLM on the fixture path. `--no-send`. Paper stays closed.

## Tests

- `tests/unit/test_phase6e_scorecard.py`
- `tests/unit/test_phase6e_cli.py`
- `tests/unit/test_phase6e_cli_deliver.py`
- `tests/unit/test_phase6e_delivery.py`
- `tests/unit/test_phase6e_queue.py`
- `tests/unit/test_phase6e_queue_hygiene.py`
- `tests/adversarial/test_phase6e_point_in_time.py`

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. PG NOTIFY ids only. `--no-send` in tests. Ask before network/keys/order deps.

## Non-goals

Live trading. Signing. `live.yaml`. Redis. Full 6f decay-watch. Universe promotion. Auto-merge. Auto-waive Skeptic/Risk. Closing OPEN incidents. Reopening the roster.

## Rollback

Revert this PR. Scorecard CLI, Quant sleeve label, and queue helper go away. Five-desk roster, naming, watchlist, listings, and Ops delivery stay on main. No live path exists to unwind.
