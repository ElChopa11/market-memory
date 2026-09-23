# US Close Brief — 2026-03-10

DATE: Generated (UTC) 2026-03-10T20:15:00+00:00; America/New_York 2026-03-10T16:15:00-04:00 (EDT); Australia/Sydney 2026-03-11T07:15:00+11:00 (AEDT); As-of knowledge 2026-03-10T20:15:00+00:00
Generated (UTC): 2026-03-10T20:15:00+00:00
Generated (America/New_York): 2026-03-10T16:15:00-04:00 (EDT)
Generated (Australia/Sydney): 2026-03-11T07:15:00+11:00 (AEDT)
US session status: after_hours — US after-hours (16:00–20:00 after cash close) (DST=EDT)
As-of knowledge: 2026-03-10T20:15:00+00:00 (ingested_at watermark; never published_at alone)
Data health: 93% (6 fresh, 1 degraded, 0 stale, 0 unavailable / 7 scored; structural excluded: none)
Coverage of observed data states with versioned weights. Not a confidence score.
Icons mark data state only (fresh / degraded / stale / unavailable). Green is not a direction.
Regime: INSUFFICIENT DATA
KEY TAKEAWAY
INSUFFICIENT DATA

## Data health

Per-domain state. Icons are data state only, never direction.

| Domain | State | Detail |
|---|---|---|
| Equities | 🟢 fresh | ES, NQ |
| Rates | 🟢 fresh | US10Y |
| USD | 🟢 fresh | DXY |
| Oil | 🟢 fresh | CL |
| Vol | 🟢 fresh | VIX |
| Crypto | 🟢 fresh | BTC, ETH |
| Hyperliquid | 🟡 degraded | BTC fresh, ETH degraded |

## What moved

| Slot | Symbol | Last | Prior close | Change | prior US close (session) | Source | As-of | State |
|---|---|---:|---:|---:|---|---|---|---|
| equity-index proxy | ES | 5780.00 | 5720.00 | +1.05% | S&P 500 futures | fixture | 2026-03-10T20:15:00+00:00 | 🟢 fresh |
| equity-index proxy | NQ | 20620.00 | 20400.00 | +1.08% | Nasdaq 100 futures | fixture | 2026-03-10T20:15:00+00:00 | 🟢 fresh |
| rates | US10Y | 4.31 | 4.22 | +9.0bp | US 10Y yield | fixture | 2026-03-10T20:15:00+00:00 | 🟢 fresh |
| USD | DXY | 103.55 | 104.20 | -0.62% | US Dollar Index | fixture | 2026-03-10T20:15:00+00:00 | 🟢 fresh |
| oil | CL | 79.10 | 77.20 | +2.46% | WTI crude | fixture | 2026-03-10T20:15:00+00:00 | 🟢 fresh |
| vol | VIX | 15.40 | 17.80 | -13.48% | CBOE Volatility Index | fixture | 2026-03-10T20:15:00+00:00 | 🟢 fresh |
| crypto | BTC | 66100.00 | 64800.00 | +2.01% | Bitcoin | fixture | 2026-03-10T20:15:00+00:00 | 🟢 fresh |
| crypto | ETH | 3520.00 | 3480.00 | +1.15% | Ether | fixture | 2026-03-10T20:15:00+00:00 | 🟢 fresh |

Overnight reference:

- ES [equity-index proxy] (S&P 500 futures): last 5750.00 / +0.52% [state=🟢 fresh; source=fixture; as-of=2026-03-10T20:15:00+00:00; obs none]
- NQ [equity-index proxy] (Nasdaq 100 futures): last 20500.00 / +0.49% [state=🟢 fresh; source=fixture; as-of=2026-03-10T20:15:00+00:00; obs none]
- US10Y [rates] (US 10Y yield): last 4.28 / +6.0bp [state=🟢 fresh; source=fixture; as-of=2026-03-10T20:15:00+00:00; obs none]
- DXY [USD] (US Dollar Index): last 103.80 / -0.38% [state=🟢 fresh; source=fixture; as-of=2026-03-10T20:15:00+00:00; obs none]
- CL [oil] (WTI crude): last 78.50 / +1.68% [state=🟢 fresh; source=fixture; as-of=2026-03-10T20:15:00+00:00; obs none]
- VIX [vol] (CBOE Volatility Index): last 16.20 / -8.99% [state=🟢 fresh; source=fixture; as-of=2026-03-10T20:15:00+00:00; obs none]
- BTC [crypto] (Bitcoin): last 65500.00 / +1.08% [state=🟢 fresh; source=fixture; as-of=2026-03-10T20:15:00+00:00; obs none]
- ETH [crypto] (Ether): last 3550.00 / +2.01% [state=🟢 fresh; source=fixture; as-of=2026-03-10T20:15:00+00:00; obs none]

## What was unexpected

- ES session +1.05% vs overnight +0.52%
- BTC session +2.01% vs overnight +1.08%
- VIX session move -13.48% is large vs a quiet overnight

## Lab right/wrong hooks

- `THESIS-0001` status=paper instrument=BTC: lab wrong (so far): expected short BTC, session +2.01%
  - Invalidation: Daily close below 64000
  - Hypothesis: Funding fade after crowding
- `THESIS-0002` status=in_research instrument=ETH: lab right (so far): expected long ETH, session +1.15%
  - Invalidation: ETH underperforms BTC by 3% on a US session close
  - Hypothesis: ETH catch-up vs BTC

## Assumption changes

- Vol crush extended: overnight bid-for-risk assumption still in force
- Higher-yield overnight backup continued into the US session

## Monitor into Asia / Europe / next US

- Asia: BTC/ETH funding, OI, and liquidation prints vs US cash close levels.
- Europe: whether the USD/yields overnight path re-asserts before next US pre-open.
- Dated catalysts still live:
  - 2026-03-11T18:00:00+00:00 [medium] FOMC speaker — Into next US session / Europe overlap.

## Hyperliquid into the next session

### BTC (🟢 fresh; source=hyperliquid.info)

- Instrument as-of knowledge: 2026-03-10T12:00:00+00:00
- Funding: 0.000400 (obs 01FROZENBTCFUNDING00000001; as-of 2026-03-10T12:00:00+00:00; market_time 2026-03-10T08:00:00+00:00)
- Open interest: 1200.5 (Δ +20.05%; obs 01FROZENBTCOI0000000000001; as-of 2026-03-10T12:00:00+00:00; market_time 2026-03-10T11:55:00+00:00)
- Mid: 65500 (obs 01FROZENBTCMID000000000001; as-of 2026-03-10T12:00:00+00:00; market_time 2026-03-10T11:55:00+00:00)
- Basis mark−oracle: 110 (mark obs 01FROZENBTCMARK00000000001; oracle obs 01FROZENBTCORACLE000000001)
- Liquidations (window sum): 2.5 (obs 01FROZENBTCLIQ000000000001)
- Levels: basis_mark_minus_oracle=110, session_high=65800, session_low=64600

### ETH (🟡 degraded; source=hyperliquid.info)

- Instrument as-of knowledge: 2026-03-10T12:00:00+00:00
- Funding: -0.000100 (obs 01FROZENETHFUNDING00000001; as-of 2026-03-10T12:00:00+00:00; market_time 2026-03-10T08:00:00+00:00)
- Open interest: missing (Δ n/a; obs 01FROZENETHOI0000000000001; as-of 2026-03-10T12:00:00+00:00; market_time 2026-03-10T11:55:00+00:00)
- Mid: 3550 (obs 01FROZENETHMID000000000001; as-of 2026-03-10T12:00:00+00:00; market_time 2026-03-10T11:55:00+00:00)
- Basis mark−oracle: 3 (mark obs 01FROZENETHMARK00000000001; oracle obs 01FROZENETHORACLE000000001)
- Liquidations (window sum): 0 (obs none)
- Levels: basis_mark_minus_oracle=3, session_high=3580, session_low=3460


## Audit

Data quality: 93%
Freshest feed: ES, NQ, US10Y, DXY, CL, VIX, BTC, ETH
Major missing feeds: none

---
**Informational only — no decision, no recommendation, no order intent.**
This brief does not change universe membership, size a trade, submit an order, or approve risk.
