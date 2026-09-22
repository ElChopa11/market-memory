# PLAN — IMP-059 C-00x instance auto-track + detectors

**Report status:** PARKED (Principal 2026-09-22: stays PARKED; do not build detectors).  
**Owner:** Quant  
**Scope:** Instance auto-track + C-001/002/003 detectors. Fixture / `--no-db`. Per-instrument nulls. `n < n_min` → INSUFFICIENT SAMPLE. IC Gate 1 FAIL stands. No sizing. Paper only.

## Why

Phase 6e pack-compare (#55) is not instance auto-track. Candidate cards C-001 / C-002 / C-003 stay `INTAKE_ONLY` until detectors exist and scorecards auto-track instances ([research/candidates/README.md](../../research/candidates/README.md) rule 9). Principal L2 sprint P2 named the instance ledger. IMP-040 Phase 1 unconditional base rates are DONE (#66); that is necessary but not sufficient to unpark compute.

## Outcome (when Principal unparks — not this PR)

- Instance auto-track for C-001 / C-002 / C-003 detector fires into the scorecard / ledger path
- Fixture and `--no-db` paths only until a later persist gate
- Per-instrument nulls (instrument-own hurdles; pooled Phase-1 mixture is not a strategy hurdle)
- `n < n_min` → closed study verdict `INSUFFICIENT SAMPLE` (no keep-tuning)
- IC Gate 1 FAIL stands
- No sizing; no scan-gate; cards stay `INTAKE_ONLY` until a later Principal unlock
- Paper only

## Tests (when unparked — not built now)

- Fixture detector counts reconcile to study `n`
- Adversarial: no future bars; pivots confirmed only after confirmation lag
- Queue hygiene: single `IN_PROGRESS` if this item is claimed; cards remain `INTAKE_ONLY` until Principal says otherwise

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. No Telegram. IC Gate 1 FAIL intact. Candidate cards stay `INTAKE_ONLY`.

## Non-goals (this hygiene PR and while PARKED)

Neon/R2 wiring. Telegram send. Detector implementation. Study compute. Inventing `config/reference/listings.yaml`. Reopening C-001/002/003 as live studies. Clearing IC Gate 1 FAIL. Flipping cards off `INTAKE_ONLY`. Occupying `IN_PROGRESS`. Auto-merge. Gate waiver.

## Rollback

Docs/queue only. Revert this PR to remove the plan file and the PARKED queue row. No runtime path to unwind.
