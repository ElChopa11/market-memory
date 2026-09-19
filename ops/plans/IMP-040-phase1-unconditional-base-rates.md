# PLAN — IMP-040 Phase 1 unconditional base rates

**Report status:** DONE (#66).  
**Owner:** Quant  
**Scope:** Unconditional event-class base rates for the classes C-001/002/003 measure against. Paper / fixture only. No candidate signal studies. No sizing. No scan-gate.

## Why

Principal order-of-work: nothing is computed on C-001 / C-002 / C-003 until unconditional base rates exist in Market Memory. Candidate intake (`research/candidates/`, #61) is IMP-039 READY; cards stay INTAKE_ONLY until this pack lands. IMP-034 on main is ticker/licence (#60), not the candidate shelf.

## Outcome

- Queue: IMP-024 DONE (#63). This item is the only `IN_PROGRESS`. IMP-039 (candidate intake #61) stays READY; studies stay blocked. OPEN incidents untouched.
- `lab base-rate compute --fixture PATH --no-db` emits a deterministic Quant artifact.
- Naming via `mm_common.naming` (`base_rate` sleeve → quant). Not a sixth desk.
- Three Quant-defined event classes:
  - `dip_touch` — first low at/through rising SMA20 after a close above it (C-002 benchmark)
  - `zone_boundary_touch` — first later touch of any prior consolidation boundary; no X·ATR departure (C-001 benchmark)
  - `pullback_ema_touch` — first EMA touch after an N-bar extreme breakout (C-003 first-entry benchmark)
- Provenance on every pack: `as_of_knowledge` (= `ingested_at`), `params_hash`, instrument set, window, cost model.
- Market Memory table `event_base_rate` (Alembic `0010`). Fixture path writes `research/quant/base-rates/YYYY-MM-DD/`.
- `n < n_min` → no claim. Never invent a print.
- Zero LLM. `--no-send`. DO NOT SIZE.

## Citation contract (C-001 / C-002 / C-003)

A later study records `delta vs event_base_rate.params_hash` + `as_of_knowledge`. It does not recompute these rates and does not implement the candidate filters here.

## Tests

- `tests/unit/test_imp039_base_rates.py`
- `tests/unit/test_imp039_cli.py`
- `tests/unit/test_imp039_queue.py`
- `tests/adversarial/test_imp039_point_in_time.py`
- `tests/integration/test_imp039_event_base_rate.py`

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. No Redis. No candidate study results.

## Non-goals

Live trading. Sizing. Scan-gate / universe / watchlist promotion. Implementing C-001/C-002/C-003 as harness strategies. Telegram fan-out. Closing OPEN incidents. Auto-merge. Waiving Skeptic/Risk.

## Rollback

Revert this PR. `event_base_rate` and the Quant sleeve label go away. Five-desk roster, listings, scorecards, decay, and EDGAR PRs stay. No live path exists to unwind.
