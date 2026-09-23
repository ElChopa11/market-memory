# US Pre-Market Brief — 2026-03-10

DATE: Generated (UTC) 2026-03-10T12:00:00+00:00; America/New_York 2026-03-10T08:00:00-04:00 (EDT); Australia/Sydney 2026-03-10T23:00:00+11:00 (AEDT); Memory watermark (as_of_knowledge) 2026-03-10T12:00:00+00:00; As-of knowledge 2026-03-10T12:00:00+00:00
Generated (UTC): 2026-03-10T12:00:00+00:00
Generated (America/New_York): 2026-03-10T08:00:00-04:00 (EDT)
Generated (Australia/Sydney): 2026-03-10T23:00:00+11:00 (AEDT)
US session status: pre_market — US pre-market (04:00–09:30 before cash open) (DST=EDT, offset -04:00; cash open 09:30, cash close 16:00 America/New_York)
Memory watermark (as_of_knowledge): 2026-03-10T12:00:00+00:00
As-of knowledge: 2026-03-10T12:00:00+00:00 (ingested_at lockstep; never published_at / market_time)
Data health: 93% (6 fresh, 1 degraded, 0 stale, 0 unavailable / 7 scored; structural excluded: none)
Coverage of observed data states with versioned weights. Not a confidence score.
Icons mark data state only (fresh / degraded / stale / unavailable). Green is not a direction.
Regime: INSUFFICIENT DATA
KEY TAKEAWAY
INSUFFICIENT DATA

Macro source: fixture
HL origin: hyperliquid.info

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

## Data quality by source

| Source | Status | As-of | Evidence | Notes |
|---|---|---|---|---|
| fixture | fresh | 2026-03-10T12:00:00+00:00 | BTC, CL, DXY, ES, ETH, NQ, US10Y, VIX |  |
| hyperliquid.info | partial | 2026-03-10T12:00:00+00:00 | 01FROZENBTCFUNDING00000001, 01FROZENBTCOI0000000000001, 01FROZENBTCOIPRIOR00000001, 01FROZENBTCMID000000000001, 01FROZENBTCMARK00000000001, 01FROZENBTCORACLE000000001, 01FROZENBTCLIQ000000000001, 01FROZENETHFUNDING00000001, 01FROZENETHOI0000000000001, 01FROZENETHMID000000000001, 01FROZENETHMARK00000000001, 01FROZENETHORACLE000000001 | public /info allowlist only |
| config/briefing/calendar.yaml | fresh | 2026-03-10T12:00:00+00:00 | yaml events | fixture; no live calendar API configured |

## Cross-asset snapshot

Section as-of: 2026-03-10T12:00:00+00:00 (capture/quote time — not an exchange-event clock unless the source says so)
Required slots (always listed): crypto, equity-index proxy, rates, USD, oil, vol. Unavailable is shown, never invented.

| Slot | Symbol | Last | Prior close | Change | Name | Source | As-of | State |
|---|---|---:|---:|---:|---|---|---|---|
| equity-index proxy | ES | 5750.00 | 5720.00 | +0.52% | S&P 500 futures | fixture | 2026-03-10T12:00:00+00:00 | 🟢 fresh |
| equity-index proxy | NQ | 20500.00 | 20400.00 | +0.49% | Nasdaq 100 futures | fixture | 2026-03-10T12:00:00+00:00 | 🟢 fresh |
| rates | US10Y | 4.28 | 4.22 | +6.0bp | US 10Y yield | fixture | 2026-03-10T12:00:00+00:00 | 🟢 fresh |
| USD | DXY | 103.80 | 104.20 | -0.38% | US Dollar Index | fixture | 2026-03-10T12:00:00+00:00 | 🟢 fresh |
| oil | CL | 78.50 | 77.20 | +1.68% | WTI crude | fixture | 2026-03-10T12:00:00+00:00 | 🟢 fresh |
| vol | VIX | 16.20 | 17.80 | -8.99% | CBOE Volatility Index | fixture | 2026-03-10T12:00:00+00:00 | 🟢 fresh |
| crypto | BTC | 65500.00 | 64800.00 | +1.08% | Bitcoin | fixture | 2026-03-10T12:00:00+00:00 | 🟢 fresh |
| crypto | ETH | 3550.00 | 3480.00 | +2.01% | Ether | fixture | 2026-03-10T12:00:00+00:00 | 🟢 fresh |

## What changed since prior US close

Prior US close watermark: 2026-03-09T20:00:00+00:00
Figures below are recorded prints vs that close; missing slots stay unavailable (not invented).

- ES [equity-index proxy] (S&P 500 futures): last 5750.00 / +0.52% [state=🟢 fresh; source=fixture; as-of=2026-03-10T12:00:00+00:00; obs none]
- NQ [equity-index proxy] (Nasdaq 100 futures): last 20500.00 / +0.49% [state=🟢 fresh; source=fixture; as-of=2026-03-10T12:00:00+00:00; obs none]
- US10Y [rates] (US 10Y yield): last 4.28 / +6.0bp [state=🟢 fresh; source=fixture; as-of=2026-03-10T12:00:00+00:00; obs none]
- DXY [USD] (US Dollar Index): last 103.80 / -0.38% [state=🟢 fresh; source=fixture; as-of=2026-03-10T12:00:00+00:00; obs none]
- CL [oil] (WTI crude): last 78.50 / +1.68% [state=🟢 fresh; source=fixture; as-of=2026-03-10T12:00:00+00:00; obs none]
- VIX [vol] (CBOE Volatility Index): last 16.20 / -8.99% [state=🟢 fresh; source=fixture; as-of=2026-03-10T12:00:00+00:00; obs none]
- BTC [crypto] (Bitcoin): last 65500.00 / +1.08% [state=🟢 fresh; source=fixture; as-of=2026-03-10T12:00:00+00:00; obs none]
- ETH [crypto] (Ether): last 3550.00 / +2.01% [state=🟢 fresh; source=fixture; as-of=2026-03-10T12:00:00+00:00; obs none]
- HL vs prior US close 2026-03-09T20:00:00+00:00 (close-to-close change only when a prior observation exists; current snapshot is labeled, not invented as a move):
  - BTC: OI +20.05% vs prior print; current funding 0.000400 (snapshot, not a close-to-close delta); current mid 65500 (snapshot, not a close-to-close delta) [quality=fresh; source=hyperliquid.info]
  - ETH: OI change unavailable (no retained observation at/before prior US close); current funding -0.000100 (snapshot, not a close-to-close delta); current mid 3550 (snapshot, not a close-to-close delta) [quality=partial; source=hyperliquid.info]

## Today's market-event calendar

Source: config/briefing/calendar.yaml (approved attributable file; empty window is shown, not invented)
Section as-of: 2026-03-10T12:00:00+00:00

- 2026-03-10T12:30:00+00:00 [high] US CPI YoY (source: config/briefing/calendar.yaml) — Frozen fixture day. Consensus 2.4% (fixture).
- 2026-03-10T14:00:00+00:00 [medium] US 10Y auction (source: config/briefing/calendar.yaml) — Watch for a stop-through vs overnight yield backup.
- 2026-03-11T18:00:00+00:00 [medium] US FOMC speaker (source: config/briefing/calendar.yaml) — Into next US session / Europe overlap.

## Cross-asset divergences

- `equity_vol` **Equity / vol divergence**: ES +0.52% while VIX -8.99% since prior US close (evidence: ES, VIX)
- `yields_equity` **Yields up with equities bid**: US10Y +6.0bp with ES +0.52% since prior US close (evidence: US10Y, ES)

## Hyperliquid market structure

Section as-of / memory watermark: 2026-03-10T12:00:00+00:00
Source: hyperliquid.info — public `/info` allowlist only (no wallet, user, account, or trading endpoints).
Snapshot fields have no exchange event time; capture is ingested_at / as_of_knowledge.

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


## Audit

Data quality: 93%
Freshest feed: ES, NQ, US10Y, DXY, CL, VIX, BTC, ETH
Major missing feeds: none

---
**Informational only — no decision, no recommendation, no order intent.**
This brief does not change universe membership, size a trade, submit an order, or approve risk.
