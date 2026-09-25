# US Close Brief — 2026-03-10

UTC 2026-03-10T20:15:00+00:00 | New York 2026-03-10T16:15:00-04:00 (EDT) | Sydney 2026-03-11T07:15:00+11:00 (AEDT)
As-of knowledge: 2026-03-10T20:15:00+00:00
Data health: 93% | Equities 🟢 fresh | Rates 🟢 fresh | USD 🟢 fresh | Oil 🟢 fresh | Vol 🟢 fresh | Crypto 🟢 fresh | Hyperliquid 🟡 degraded

| Symbol | Last | Δ | Source | Quality | Label |
|---|---:|---:|---|---|---|
| ES | 5780.00 | +1.05% | fixture | fresh | S&P 500 futures |
| NQ | 20620.00 | +1.08% | fixture | fresh | Nasdaq 100 futures |
| US10Y | 4.31 | +9.0bp | fixture | fresh | US 10Y yield |
| DXY | 103.55 | -0.62% | fixture | fresh | US Dollar Index |
| CL | 79.10 | +2.46% | fixture | fresh | WTI crude |
| VIX | 15.40 | -13.48% | fixture | fresh | CBOE Volatility Index |
| BTC | 66100.00 | +2.01% | fixture | fresh | Bitcoin |
| ETH | 3520.00 | +1.15% | fixture | fresh | Ether |

## Positioning

BTC Funding: 0.000400 obs 01FROZENBTCFUNDING00000001
BTC Open interest: 1200.5 Δ +20.05% obs 01FROZENBTCOI0000000000001
BTC Mid: 65500 obs 01FROZENBTCMID000000000001
BTC Liquidations (window sum): 2.5 obs 01FROZENBTCLIQ000000000001
BTC Levels: session_high=65800, session_low=64600
ETH degraded
ETH Funding: -0.000100 obs 01FROZENETHFUNDING00000001
ETH Mid: 3550 obs 01FROZENETHMID000000000001
ETH Levels: session_high=3580, session_low=3460
gaps: ETH Open interest, ETH Liquidations (window sum)

## Unexpected

- ES session +1.05% vs overnight +0.52%
- BTC session +2.01% vs overnight +1.08%
- VIX session move -13.48% is large vs a quiet overnight

## Lab hooks

- `THESIS-0001` status=paper instrument=BTC: lab wrong (so far): expected short BTC, session +2.01%
  - Invalidation: Daily close below 64000
  - Hypothesis: Funding fade after crowding
- `THESIS-0002` status=in_research instrument=ETH: lab right (so far): expected long ETH, session +1.15%
  - Invalidation: ETH underperforms BTC by 3% on a US session close
  - Hypothesis: ETH catch-up vs BTC

## Assumptions

- Vol crush extended: overnight bid-for-risk assumption still in force
- Higher-yield overnight backup continued into the US session

## Catalysts

- 2026-03-11T18:00:00+00:00 [medium] FOMC speaker — Into next US session / Europe overlap.
