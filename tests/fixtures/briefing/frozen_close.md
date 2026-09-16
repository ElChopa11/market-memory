# US Close Brief — 2026-03-10

Generated: 2026-03-10T20:15:00+00:00
As-of knowledge: 2026-03-10T20:15:00+00:00 (ingested_at watermark; never published_at alone)
Session clock: 2026-03-10T16:15:00-04:00 (America/New_York)
Lab clock: 2026-03-11T07:15:00+11:00 (Australia/Sydney)
Data quality: partial

## What moved

| Symbol | Last | Prior close | Change | prior US close (session) | Quality |
|---|---:|---:|---:|---|---|
| ES | 5780.00 | 5720.00 | +1.05% | S&P 500 futures | ok |
| NQ | 20620.00 | 20400.00 | +1.08% | Nasdaq 100 futures | ok |
| US10Y | 4.31 | 4.22 | +9.0bp | US 10Y yield | ok |
| DXY | 103.55 | 104.20 | -0.62% | US Dollar Index | ok |
| CL | 79.10 | 77.20 | +2.46% | WTI crude | ok |
| VIX | 15.40 | 17.80 | -13.48% | CBOE Volatility Index | ok |
| BTC | 66100.00 | 64800.00 | +2.01% | Bitcoin | ok |
| ETH | 3520.00 | 3480.00 | +1.15% | Ether | ok |

Overnight reference:

- ES (S&P 500 futures): last 5750.00 / +0.52% [ok]
- NQ (Nasdaq 100 futures): last 20500.00 / +0.49% [ok]
- US10Y (US 10Y yield): last 4.28 / +6.0bp [ok]
- DXY (US Dollar Index): last 103.80 / -0.38% [ok]
- CL (WTI crude): last 78.50 / +1.68% [ok]
- VIX (CBOE Volatility Index): last 16.20 / -8.99% [ok]
- BTC (Bitcoin): last 65500.00 / +1.08% [ok]
- ETH (Ether): last 3550.00 / +2.01% [ok]

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

### BTC (quality=ok)

- Funding: 0.000400 (obs 01FROZENBTCFUNDING00000001)
- Open interest: 1200.5 (Δ +20.05%; obs 01FROZENBTCOI0000000000001)
- Mid: 65500 (obs 01FROZENBTCMID000000000001)
- Basis mark−oracle: 110.0
- Liquidations (window sum): 2.5000 (obs 01FROZENBTCLIQ000000000001)
- Levels: basis_mark_minus_oracle=110, session_high=65800, session_low=64600

### ETH (quality=partial)

- Funding: -0.000100 (obs 01FROZENETHFUNDING00000001)
- Open interest: missing (Δ n/a; obs 01FROZENETHOI0000000000001)
- Mid: 3550 (obs 01FROZENETHMID000000000001)
- Basis mark−oracle: 3.0
- Liquidations (window sum): 0.0000 (obs none)
- Levels: basis_mark_minus_oracle=3, session_high=3580, session_low=3460
