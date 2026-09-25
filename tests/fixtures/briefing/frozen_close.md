```
US Close 2026-03-10

UTC 2026-03-10 20:15Z
NY 2026-03-10 16:15 EDT
SYD 2026-03-11 07:15 AEDT
Health 93% degraded Hyperliquid

ES 5780.00 +1.05%
NQ 20620.00 +1.08%
US10Y 4.31 +9.0bp
DXY 103.55 -0.62%
CL 79.10 +2.46%
VIX 15.40 -13.48%
BTC 66100.00 +2.01%
ETH 3520.00 +1.15%

Positioning
BTC fund 350.40% ann obs
01FROZENBTCFUNDING00000001
BTC Liquidations (window sum) 2.5 obs
01FROZENBTCLIQ000000000001
BTC levels session_high=65800,
session_low=64600
ETH degraded
ETH fund -87.60% ann obs
01FROZENETHFUNDING00000001
ETH levels session_high=3580,
session_low=3460

Unexpected

- ES session +1.05% vs overnight +0.52%
- BTC session +2.01% vs overnight +1.08%
- VIX session move -13.48% is large vs a
quiet overnight

Lab hooks

- `THESIS-0001` status=paper
instrument=BTC: lab wrong (so far):
expected short BTC, session +2.01%
  - Invalidation: Daily close below 64000
  - Hypothesis: Funding fade after
  crowding
- `THESIS-0002` status=in_research
instrument=ETH: lab right (so far):
expected long ETH, session +1.15%
  - Invalidation: ETH underperforms BTC by
  3% on a US session close
  - Hypothesis: ETH catch-up vs BTC

Assumptions

- Vol crush extended: overnight
bid-for-risk assumption still in force
- Higher-yield overnight backup continued
into the US session

Catalysts

- 2026-03-11T18:00:00+00:00 [medium] FOMC
speaker — Into next US session / Europe
overlap.
```
