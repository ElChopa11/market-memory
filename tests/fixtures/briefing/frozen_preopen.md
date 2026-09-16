# US Pre-Open Brief — 2026-03-10

Generated: 2026-03-10T12:00:00+00:00
As-of knowledge: 2026-03-10T12:00:00+00:00 (ingested_at watermark; never published_at alone)
Session clock: 2026-03-10T08:00:00-04:00 (America/New_York)
Lab clock: 2026-03-10T23:00:00+11:00 (Australia/Sydney)
Data quality: partial
Macro source: fixture

## Overnight tape

| Symbol | Last | Prior close | Change | prior US close | Quality |
|---|---:|---:|---:|---|---|
| ES | 5750.00 | 5720.00 | +0.52% | S&P 500 futures | ok |
| NQ | 20500.00 | 20400.00 | +0.49% | Nasdaq 100 futures | ok |
| US10Y | 4.28 | 4.22 | +6.0bp | US 10Y yield | ok |
| DXY | 103.80 | 104.20 | -0.38% | US Dollar Index | ok |
| CL | 78.50 | 77.20 | +1.68% | WTI crude | ok |
| VIX | 16.20 | 17.80 | -8.99% | CBOE Volatility Index | ok |
| BTC | 65500.00 | 64800.00 | +1.08% | Bitcoin | ok |
| ETH | 3550.00 | 3480.00 | +2.01% | Ether | ok |

## What changed since prior US close

Prior US close watermark: 2026-03-09T20:00:00+00:00

- ES (S&P 500 futures): last 5750.00 / +0.52% [ok]
- NQ (Nasdaq 100 futures): last 20500.00 / +0.49% [ok]
- US10Y (US 10Y yield): last 4.28 / +6.0bp [ok]
- DXY (US Dollar Index): last 103.80 / -0.38% [ok]
- CL (WTI crude): last 78.50 / +1.68% [ok]
- VIX (CBOE Volatility Index): last 16.20 / -8.99% [ok]
- BTC (Bitcoin): last 65500.00 / +1.08% [ok]
- ETH (Ether): last 3550.00 / +2.01% [ok]

## Macro / catalysts

- 2026-03-10T12:30:00+00:00 [high] US CPI YoY — Frozen fixture day. Consensus 2.4% (fixture).
- 2026-03-10T14:00:00+00:00 [medium] US 10Y auction — Watch for a stop-through vs overnight yield backup.
- 2026-03-11T18:00:00+00:00 [medium] US FOMC speaker — Into next US session / Europe overlap.

## Cross-asset divergences

- `equity_vol` **Equity / vol divergence**: ES +0.52% while VIX -8.99% since prior US close (evidence: ES, VIX)
- `yields_equity` **Yields up with equities bid**: US10Y +6.0bp with ES +0.52% since prior US close (evidence: US10Y, ES)

## Hyperliquid (Market Memory)

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


## Watchlist

### BTC

- Why now: Funding elevated while open interest expands — crowding into the US cash open (funding=0.0400%; OI +20.1% vs prior print; mark-oracle basis +110.00)
- Evidence (observation ids): 01FROZENBTCFUNDING00000001, 01FROZENBTCOI0000000000001, 01FROZENBTCOIPRIOR00000001, 01FROZENBTCMID000000000001, 01FROZENBTCMARK00000000001, 01FROZENBTCORACLE000000001, 01FROZENBTCLIQ000000000001
- Levels: resistance=66000, support=64000, basis_mark_minus_oracle=110, session_high=65800, session_low=64600
- Invalidation: Funding mean-reverts below 0.00005 without an OI drop, or daily close below support
- No-trade: OI or funding data_quality is not ok; VIX > 25 with ES gap > 1%

### ETH

- Why now: ETH/BTC catch-up risk if BTC squeeze continues into the cash session (funding=-0.0100%; mark-oracle basis +3.00)
- Evidence (observation ids): 01FROZENETHFUNDING00000001, 01FROZENETHOI0000000000001, 01FROZENETHMID000000000001, 01FROZENETHMARK00000000001, 01FROZENETHORACLE000000001
- Levels: resistance=3650, support=3400, basis_mark_minus_oracle=3, session_high=3580, session_low=3460
- Invalidation: ETH lags while BTC funding remains bid; lose support without OI confirmation
- No-trade: ETH open_interest is missing or partial; HL ETH data_quality=partial
