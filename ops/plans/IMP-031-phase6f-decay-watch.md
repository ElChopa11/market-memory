# PLAN — IMP-031 Phase 6f strategy decay-watch

**Report status:** IN_REVIEW (this PR).  
**Owner:** Quant (hash math) / Ops (alert + delivery)  
**Scope:** Phase 6f — prompt-hash strategy decay-watch on the five-desk roster. No live trading. No execution. No `live.yaml`. No Redis. No gate waiver. No invented scorecard numbers.

## Why

6e recorded prompt SHA-256 inputs (`config/scorecards/decay.yaml`, `mm_quant.decay_stub`) with `watch_enabled: false`. Operators still lacked a standing watch that alerts when a versioned prompt or strategy/config hash drifts.

## Outcome

- Queue: IMP-030 DONE (#55). IMP-031 this thread. OPEN incidents untouched (SCHED-001, BRIEF-TAG-20260918, SRC-STOOQ-404, SRC-FRED-MISSING-ENV).
- `lab decay watch --fixture PATH --no-send` hashes versioned prompts + listed configs against pinned SHA-256.
- Naming via `mm_common.naming` (`decay` is a Quant sleeve, not a sixth desk). Unknown slug `decay` fails closed as a publishing desk.
- Mesh envelope on `desk.quant.output`. Mismatch / missing / unpinned → NOTIFY on `desk.quant.alert`.
- Queue *signal* is operator-facing only. Helper does **not** write `ops/improvement-queue.md`, auto-merge, auto-waive, auto-disable prompts, or close OPEN incidents.
- Ops `lab deliver decay` inherits `content_hash` (quant route + Ops mirror).
- Integrates with IMP-030 scorecards: attached pairs keep `NOT_COMPARABLE` tagged; no invented completeness_delta / hash_identity.
- Zero LLM on the fixture path. `--no-send`. Paper stays closed.

## Tests

- `tests/unit/test_phase6f_decay.py`
- `tests/unit/test_phase6f_cli.py`
- `tests/unit/test_phase6f_cli_deliver.py`
- `tests/unit/test_phase6f_delivery.py`
- `tests/unit/test_phase6f_queue.py`
- `tests/adversarial/test_phase6f_point_in_time.py`

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. PG NOTIFY ids only. `--no-send` in tests. Ask before network/keys/order deps.

## Non-goals

Live trading. Signing. `live.yaml`. Redis. Universe promotion. Auto-merge. Auto-waive Skeptic/Risk. Auto-disable prompts. Closing OPEN incidents. Reopening the roster. Inventing like-for-like scores for tagged incomparable packs.

## Rollback

Revert this PR. Decay CLI, Quant sleeve label, and Ops decay delivery go away. Scorecards, listings, watchlist, naming, and the five-desk roster stay on main. No live path exists to unwind.
