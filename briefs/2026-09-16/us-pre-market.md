# US Pre-Market Brief — 2026-09-16

Generated (UTC): 2026-09-17T03:19:30+00:00
Generated (America/New_York): 2026-09-16T23:19:30-04:00 (EDT)
Generated (Australia/Sydney): 2026-09-17T13:19:30+10:00 (AEST)
US session status: overnight_closed — Overnight — US cash session closed (DST=EDT, offset -04:00; cash open 09:30, cash close 16:00 America/New_York)
Memory watermark (as_of_knowledge): 2026-09-17T03:19:30+00:00
As-of knowledge: 2026-09-17T03:19:30+00:00 (ingested_at lockstep; never published_at / market_time)
Overall data quality: partial
Macro source: live
HL origin: hyperliquid.info /info

## Data quality by source

| Source | Status | As-of | Evidence | Notes |
|---|---|---|---|---|
| coingecko | fresh | 2026-09-17T03:19:30+00:00 | BTC, ETH |  |
| fred | unavailable | 2026-09-17T03:19:30+00:00 | US10Y | missing env FRED_API_KEY; FRED unavailable |
| stooq | unavailable | 2026-09-17T03:19:30+00:00 | CL, DXY, ES, NQ, VIX | stooq failed for 5 symbol(s): ES, NQ, DXY, CL, VIX |
| hyperliquid.info /info | fresh | 2026-09-17T03:19:30+00:00 | none (not indexed) | public /info allowlist only |
| config/briefing/calendar.yaml | fresh | 2026-09-17T03:19:30+00:00 | yaml events | fixture; no live calendar API configured |

## Cross-asset snapshot

Section as-of: 2026-09-17T03:19:30+00:00 (capture/quote time — not an exchange-event clock unless the source says so)
Required slots (always listed): crypto, equity-index proxy, rates, USD, oil, vol. Unavailable is shown, never invented.

| Slot | Symbol | Last | Prior close | Change | Name | Source | As-of | Quality |
|---|---|---:|---:|---:|---|---|---|---|
| equity-index proxy | ES | n/a | n/a | n/a | S&P 500 futures | stooq | 2026-09-17T03:19:30+00:00 | unavailable |
| equity-index proxy | NQ | n/a | n/a | n/a | Nasdaq 100 futures | stooq | 2026-09-17T03:19:30+00:00 | unavailable |
| rates | US10Y | n/a | n/a | n/a | US 10Y yield | fred | 2026-09-17T03:19:30+00:00 | unavailable |
| USD | DXY | n/a | n/a | n/a | US Dollar Index | stooq | 2026-09-17T03:19:30+00:00 | unavailable |
| oil | CL | n/a | n/a | n/a | WTI crude | stooq | 2026-09-17T03:19:30+00:00 | unavailable |
| vol | VIX | n/a | n/a | n/a | CBOE Volatility Index | stooq | 2026-09-17T03:19:30+00:00 | unavailable |
| crypto | BTC | 76382.00 | 75989.94 | +0.52% | Bitcoin | coingecko | 2026-09-17T03:19:30+00:00 | fresh |
| crypto | ETH | 2432.02 | 2407.99 | +1.00% | Ether | coingecko | 2026-09-17T03:19:30+00:00 | fresh |

Notes:
- stooq failed for 5 symbol(s): ES, NQ, DXY, CL, VIX
- missing env FRED_API_KEY; FRED unavailable

## What changed since prior US close

Prior US close watermark: 2026-09-16T20:00:00+00:00
Figures below are recorded prints vs that close; missing slots stay unavailable (not invented).

- ES [equity-index proxy] (S&P 500 futures): last n/a / n/a [quality=unavailable; source=stooq; as-of=2026-09-17T03:19:30+00:00; obs none]
- NQ [equity-index proxy] (Nasdaq 100 futures): last n/a / n/a [quality=unavailable; source=stooq; as-of=2026-09-17T03:19:30+00:00; obs none]
- US10Y [rates] (US 10Y yield): last n/a / n/a [quality=unavailable; source=fred; as-of=2026-09-17T03:19:30+00:00; obs none]
- DXY [USD] (US Dollar Index): last n/a / n/a [quality=unavailable; source=stooq; as-of=2026-09-17T03:19:30+00:00; obs none]
- CL [oil] (WTI crude): last n/a / n/a [quality=unavailable; source=stooq; as-of=2026-09-17T03:19:30+00:00; obs none]
- VIX [vol] (CBOE Volatility Index): last n/a / n/a [quality=unavailable; source=stooq; as-of=2026-09-17T03:19:30+00:00; obs none]
- BTC [crypto] (Bitcoin): last 76382.00 / +0.52% [quality=fresh; source=coingecko; as-of=2026-09-17T03:19:30+00:00; obs none]
- ETH [crypto] (Ether): last 2432.02 / +1.00% [quality=fresh; source=coingecko; as-of=2026-09-17T03:19:30+00:00; obs none]
- HL vs prior US close 2026-09-16T20:00:00+00:00 (close-to-close change only when a prior observation exists; current snapshot is labeled, not invented as a move):
  - BTC: OI change unavailable (no retained observation at/before prior US close); current funding 0.000013 (snapshot, not a close-to-close delta); current mid 76398.5 (snapshot, not a close-to-close delta) [quality=fresh; source=hyperliquid.info /info]
  - ETH: OI change unavailable (no retained observation at/before prior US close); current funding 0.000013 (snapshot, not a close-to-close delta); current mid 2432.25 (snapshot, not a close-to-close delta) [quality=fresh; source=hyperliquid.info /info]

## Today's market-event calendar

Source: config/briefing/calendar.yaml (approved attributable file; empty window is shown, not invented)
Section as-of: 2026-09-17T03:19:30+00:00

- None in the look-ahead window.

## Cross-asset divergences

- No configured rule fired.

## Hyperliquid market structure

Section as-of / memory watermark: 2026-09-17T03:19:30+00:00
Source: hyperliquid.info /info — public `/info` allowlist only (no wallet, user, account, or trading endpoints).
Snapshot fields have no exchange event time; capture is ingested_at / as_of_knowledge.

### BTC (quality=fresh; source=hyperliquid.info /info)

- Instrument as-of knowledge: 2026-09-17T03:19:30+00:00
- Funding: 0.000013 (obs none (https://api.hyperliquid.xyz/info type=metaAndAssetCtxs); as-of 2026-09-17T03:19:30+00:00; market_time null (snapshot; capture is as_of_knowledge / ingested_at))
- Open interest: 37795.01338 (Δ n/a; obs none (https://api.hyperliquid.xyz/info type=metaAndAssetCtxs); as-of 2026-09-17T03:19:30+00:00; market_time null (snapshot; capture is as_of_knowledge / ingested_at))
- Mid: 76398.5 (obs none (https://api.hyperliquid.xyz/info type=metaAndAssetCtxs); as-of 2026-09-17T03:19:30+00:00; market_time null (snapshot; capture is as_of_knowledge / ingested_at))
- Basis mark−oracle: -31.6 (mark obs none (https://api.hyperliquid.xyz/info type=metaAndAssetCtxs); oracle obs none (https://api.hyperliquid.xyz/info type=metaAndAssetCtxs))
- Liquidations (window sum): 0 (obs none)
- Levels: basis_mark_minus_oracle=-31.6

### ETH (quality=fresh; source=hyperliquid.info /info)

- Instrument as-of knowledge: 2026-09-17T03:19:30+00:00
- Funding: 0.000013 (obs none (https://api.hyperliquid.xyz/info type=metaAndAssetCtxs); as-of 2026-09-17T03:19:30+00:00; market_time null (snapshot; capture is as_of_knowledge / ingested_at))
- Open interest: 980614.7346 (Δ n/a; obs none (https://api.hyperliquid.xyz/info type=metaAndAssetCtxs); as-of 2026-09-17T03:19:30+00:00; market_time null (snapshot; capture is as_of_knowledge / ingested_at))
- Mid: 2432.25 (obs none (https://api.hyperliquid.xyz/info type=metaAndAssetCtxs); as-of 2026-09-17T03:19:30+00:00; market_time null (snapshot; capture is as_of_knowledge / ingested_at))
- Basis mark−oracle: -0.7 (mark obs none (https://api.hyperliquid.xyz/info type=metaAndAssetCtxs); oracle obs none (https://api.hyperliquid.xyz/info type=metaAndAssetCtxs))
- Liquidations (window sum): 0 (obs none)
- Levels: basis_mark_minus_oracle=-0.7


## Watchlist

### BTC

- Why now: Funding elevated while open interest expands — crowding into the US cash open (funding=0.0013%; mark-oracle basis -31.60)
- Evidence (observation ids): none
- Levels: resistance=66000, support=64000, basis_mark_minus_oracle=-31.6
- Invalidation: Funding mean-reverts below 0.00005 without an OI drop, or daily close below support
- No-trade: OI or funding data_quality is not ok; VIX > 25 with ES gap > 1%

### ETH

- Why now: ETH/BTC catch-up risk if BTC squeeze continues into the cash session (funding=0.0013%; mark-oracle basis -0.70)
- Evidence (observation ids): none
- Levels: resistance=3650, support=3400, basis_mark_minus_oracle=-0.7
- Invalidation: ETH lags while BTC funding remains bid; lose support without OI confirmation
- No-trade: ETH open_interest is missing or partial


---
**Informational only — no decision, no recommendation, no order intent.**
This brief does not create an active_call, size a trade, submit an order, or approve risk.
