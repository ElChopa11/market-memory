# Unconditional event-class base rates (IMP-039)

Quant-owned Phase 1 pack. Ops may later publish; Coord orchestrates. **Not a sixth desk. Not a call. Not a C-001/C-002/C-003 study.**

Principal order-of-work: nothing is computed on those candidates until this pack exists in Market Memory.

## Commands

```bash
uv run lab base-rate compute --fixture tests/fixtures/phase1_base_rates/panel.json --no-db --no-send
```

`--no-db` writes `research/quant/base-rates/YYYY-MM-DD/unconditional.{md,json,sha256}`. Optional `--dsn` persists the same payload into Market Memory table `event_base_rate` (as_of_knowledge lockstep ingested_at). Pytest never hits live Telegram or LLM.

## Event classes

| Class | Definition | Candidate that cites it |
|---|---|---|
| `dip_touch` | First low at/through a **rising SMA20** after a completed close above that SMA | C-002 (triple RSI adds the oscillator filter) |
| `zone_boundary_touch` | First later touch of **any prior consolidation** boundary (base height ≤ Y·ATR). No X·ATR departure | C-001 (zone study adds departure confirm + first-return fade) |
| `pullback_ema_touch` | First EMA touch after a completed N-bar extreme breakout that does not take out the breakout bar extreme | C-003 (second-entry adds the second pullback + trigger) |

Params live in [`config/quant/base_rates.yaml`](../../config/quant/base_rates.yaml). `params_hash` covers those params plus the instrument set, window, and cost model.

## Provenance

Every pack carries:

- `as_of_knowledge` (= `ingested_at`; never `published_at` / `market_time`)
- `params_hash`
- instrument set
- window
- cost model (`taker_fee*2 + slippage_bps/1e4*2 + funding_rate*(expected_hold_hours/24)`). `default_clip` is a **cost clip only** — **DO NOT SIZE**

`n < n_min` (20) → **no base-rate claim**. Horizon bars that are not yet visible are censored, not invented.

## How C-001 / C-002 / C-003 cite this pack

Path: `research/quant/base-rates/<session_date>/unconditional.json` (and the `event_base_rate` row with the same `params_hash`).

A later study must:

1. Name the event class it measures against (`CANDIDATE_BENCHMARKS` in `mm_quant.base_rates`).
2. Copy `params_hash` + `as_of_knowledge` from this pack.
3. Report study hit-rate / mean R **versus** the unconditional rate for that class.
4. Keep candidate filters out of this compute. Intake (`research/candidates/`, PR #61) stays INTAKE_ONLY until this pack exists.

## Naming + Memory

`base_rate` is a Quant sleeve (`mm_common.naming`). Unknown slug `base_rate` fails closed as a publishing desk. Alembic revision `0010_unconditional_base_rates`.

## Not this runbook

Live/signing. Sizing. Scan-gate. Implementing C-001/002/003 signals. Closing OPEN incidents. Telegram send.
