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
3. Report study hit-rate / mean R **versus** the unconditional rate for that class **on that instrument**.
4. Keep candidate filters out of this compute. Intake (`research/candidates/`, PR #61) stays INTAKE_ONLY until this pack exists.

## Instrument-own hurdle (IC Attack 5 / Principal FIX 1)

Phase-1 **pooled** ~33% 1R:2R is a **descriptive coin-flip mixture** under **PROVISIONAL** equity history. It is **NOT** a strategy hurdle.

Quant convention:

- Every C-001 / C-002 / C-003 study is measured against **that instrument's own** unconditional 1R:2R bracket rate.
- If the study uses a trend-up permission filter, it must also beat **that instrument's own trend-up** bracket.
- Do not quote the pooled ~33% as a candidate null, a strategy hurdle, or a PASS bar.

IC Gate 1 (`research/base-rates/phase1-2026-09-19-ic-attack.md`, 2026-09-19) remains **FAIL** as the methodology-build gate for strategies. FIX 1/2 do not soften FAIL.

Unconditional forward-return headlines lead with **median**, mean alongside (IC Attack A8). Positive means with ≤0 medians are right-tail drift, not permission to long.

## Naming + Memory

`base_rate` is a Quant sleeve (`mm_common.naming`). Unknown slug `base_rate` fails closed as a publishing desk. Alembic revision `0010_unconditional_base_rates`.

## Not this runbook

Live/signing. Sizing. Scan-gate. Implementing C-001/002/003 signals. Closing OPEN incidents. Telegram send.
