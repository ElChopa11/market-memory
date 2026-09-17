# QUANT-20260917 — Active Calls Pack (Principal / Don)

| Field | Value |
| --- | --- |
| Pack ID | `QUANT-20260917` |
| Repo | `ElChopa11/market-memory` |
| Scope | **ACTIVE CALLS only** (center): BTC, ETH, NVDA, AVGO, MSFT, META, JPM, XLF, XOM |
| Appendix | Watch-only (do not center): UNI, AAVE, SMH |
| Pack written | **2026-09-17 11:18 AEST** (box clock Australia/Sydney) |
| Price/vol run | `2026-09-17T11:15:47.495030+10:00` via `research/queue/quant-20260917/build_quant_pack.py` |
| HL capture | **2026-09-17T00:28:03Z** (= **2026-09-17 10:28 AEST**) · `Intel lab HL cache (file-only; not in-repo)` · PARTIAL top25 cites same stamp · **label: stale/partial** (live HL refresh RQ-20260917-A returned HTTP **429**) |
| Equity ADV | Yahoo chart API v8 via universe scan · fetched **2026-09-17T00:49:39Z** UTC (= **10:49 AEST**) |
| Disclaimer | **Not a trade.** Quant snapshot for Skeptic review. Prefer rejection honesty (crowded / already priced). No fabricated numbers. |

## Methodology TLDR (5 lines)

1. Daily simple returns on auto-adjusted Close (yfinance); UNI from Kraken public OHLC (yfinance UNI-USD stub broken).
2. Realized vol = sample std(ddof=1) × √252 (equities) or √365 (crypto) over last 20 / 60 return bars.
3. Max drawdown ≈1y = min peak-to-trough over last 252 equity / 365 crypto bars.
4. Relative returns = name total return − SPY (equities) or − BTC (ETH); windows ≈21/63 trading days or 30/90 crypto days; YTD from first 2026 bar.
5. Cross-corr = Pearson on last **60** overlapping business-day-aligned daily returns (**2026-05-28 → 2026-09-15**).

**Artifacts:** `research/queue/quant-20260917/build_quant_pack.py`, `research/queue/quant-20260917/metrics_active_and_watch.csv`, `research/queue/quant-20260917/corr_matrix_60d.csv`, `research/queue/quant-20260917/daily_returns_60d_corr_window.csv`, `research/queue/quant-20260917/vol_mdd_summary.csv`, `research/queue/quant-20260917/equity_adv_5d_from_universe_scan.csv`, `research/queue/quant-20260917/run_meta.json`, `research/queue/quant-20260917/daily_returns_full_panel.csv`.

---

## Macro regime note (NOT a trade)

**Hawkish Fed backdrop (already public / crowded):** FOMC (12–0) raised FF target **+25bp to 3.75–4.00%** (release ~2026-09-16 14:00 ET); IORB **3.90%**, primary credit **4.00%** effective 2026-09-17; SEP path flags further tightening / higher end-2026 rates. Senate cloture on H.R.3633 rejected **49–50** (2026-09-15).

| Claim | MM obs_id / URL | Source ts |
| --- | --- | --- |
| FOMC +25bp / FF 3.75–4.00% | `01M2PCX90PQAP96J62RR6EWQ35` | 2026-09-16 (Fed statement) |
| IORB 3.90% | `01M2PCX9005R4S8GRPQJP96CRP` | 2026-09-16 |
| Primary credit 4.00% | `01M2PCX90C2J9RPG17CSZDTV3Q` | 2026-09-16 |
| Reuters further-tightening (partial) | `01M2PCX91243QK9V8HCCWQFASY` | 2026-09-16 |
| Primary Fed statement | https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm | 2026-09-16 |
| Implementation note | https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a1.htm | 2026-09-16 |
| SEP tables | https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm | 2026-09-16 |
| Senate H.R.3633 cloture fail | https://www.senate.gov/legislative/LIS/roll_call_votes/vote1192/vote_119_2_00234.htm | 2026-09-15 |

**Regime implication for this pack (descriptive only):** Higher real-rate / duration compression + energy inflation narrative favors **cash-flow / NII / energy** research frames over pure crypto beta or multiple-expansion AI longs — but **Skeptic #11:** hike + CLARITY setback are **already priced** in headlines; obs_ids are backdrop, not name-level edge.

**docs/ops TSV via gh:** **unavailable** this pass — `docs/` has runbooks only; code search for obs_ids / observations.tsv returned **0 hits**. Values below for BTC/ETH funding·OI come from **lab HL JSON** cross-cited to shortlist obs_ids (IDs referenced; payload bytes not re-read from Postgres).

---

## Cross-asset corr matrix (9 active names)

Window: **60** overlapping daily returns, **2026-05-28 → 2026-09-15** (inner-join; crypto weekends dropped when equities absent). Source: yfinance via `research/queue/quant-20260917/build_quant_pack.py` · run `2026-09-17T11:15:47.495030+10:00`.

|      |   BTC |   ETH |   NVDA |   AVGO |   MSFT |   META |   JPM |   XLF |   XOM |
|:-----|------:|------:|-------:|-------:|-------:|-------:|------:|------:|------:|
| BTC  |  1    |  0.89 |   0.26 |   0.03 |   0.25 |   0.13 |  0.04 |  0.25 | -0.12 |
| ETH  |  0.89 |  1    |   0.22 |   0.04 |   0.22 |   0.18 | -0.03 |  0.16 | -0.09 |
| NVDA |  0.26 |  0.22 |   1    |   0.46 |   0.15 |   0.14 |  0.08 |  0.02 | -0.25 |
| AVGO |  0.03 |  0.04 |   0.46 |   1    |   0.12 |  -0.01 | -0.07 | -0.28 | -0.23 |
| MSFT |  0.25 |  0.22 |   0.15 |   0.12 |   1    |  -0.02 |  0.04 |  0.28 | -0.1  |
| META |  0.13 |  0.18 |   0.14 |  -0.01 |  -0.02 |   1    |  0.09 |  0.18 | -0.07 |
| JPM  |  0.04 | -0.03 |   0.08 |  -0.07 |   0.04 |   0.09 |  1    |  0.73 | -0.04 |
| XLF  |  0.25 |  0.16 |   0.02 |  -0.28 |   0.28 |   0.18 |  0.73 |  1    | -0.26 |
| XOM  | -0.12 | -0.09 |  -0.25 |  -0.23 |  -0.1  |  -0.07 | -0.04 | -0.26 |  1    |

**Read:** BTC–ETH **0.89** (tight crypto beta). JPM–XLF **0.73** (financials cluster). XOM **negatively** correlated to semis/crypto in this window (rates/energy idiosyncratic). NVDA–AVGO **0.46** (AI-infra co-movement, not identity).

CSV: `research/queue/quant-20260917/corr_matrix_60d.csv`, returns: `research/queue/quant-20260917/daily_returns_60d_corr_window.csv`.

---

## Active calls — one-pagers


### BTC (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| Venue | Hyperliquid perp | lab |
| dayNtlVlm | $3.05B | HL `metaAndAssetCtxs` · **2026-09-17T00:28:03Z** / 2026-09-17 10:28 AEST · **stale/partial** (live 429) |
| OI (coin) | 37,923.56 BTC | same |
| OI$ proxy | $2.90B (= OI × mark) | same |
| funding (instant) | 0.0000091766 (~0.0009% / period) | same · MM cite `01M2PCXAFASC2V0WCGWR0E8MZT` |
| OI obs cite | — | MM cite `01M2PCXAFMC3792Y1PQ3H2ACVQ` (payload via docs/ops TSV: **unavailable** via gh) |
| mark / mid / oracle | 76378.0 / 76377.5 / 76411.2 | same · cites `01M2PCXAEE4BRXTPMV56SYN56V` / `01M2PCXACWWCDJRR2GJ20RV7D4` / `01M2PCXAEY18W6290P82NECSM7` |
| fundingHistory 24h | **unavailable** | HTTP 429 · `(lab path omitted)/intel-briefs/live/fundingHistory-btc.json` is null · RQ-20260917-A |
| Last close (spot proxy) | $76,201.02 | yfinance `BTC-USD` · asof **2026-09-17** · run 2026-09-17T11:15:47.495030+10:00 |
| RV 20d / 60d ann. | 35.6% / 39.1% | √365 · same |
| Max DD ~1y | -53.1% | 365d lookback · same |
| Ret 1m / 3m / YTD | 18.1% / 21.2% / -14.1% | absolute (BTC is ETH bench) |

**Skeptic honesty:** Deepest HL book ≠ mispricing. Hawkish Fed + CLARITY fail are **public**. No thesis until ETF flow series + fundingHistory continuity exist.


### ETH (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| dayNtlVlm | $1.37B | HL · **2026-09-17T00:28:03Z** / 2026-09-17 10:28 AEST · **stale/partial** |
| OI (coin) | 979,333.98 ETH | same |
| OI$ proxy | $2.37B | same · **no ETH OI/mark ULID in known MM set** |
| funding | 0.0000125000 | same · MM cite `01M2PCPEK2ZXFDKPK0TDZZZ5M4` |
| mark / mid / oracle | 2421.88 / 2421.95 / 2422.6 | same (file-only; no MM obs_ids for mark/OI) |
| fundingHistory 24h | **unavailable** | HTTP 429 |
| Last close | $2,415.42 | yfinance `ETH-USD` · asof **2026-09-17** |
| RV 20d / 60d | 41.7% / 58.9% | √365 |
| Max DD ~1y | -66.6% | 365d |
| Ret 1m / 3m / YTD | 26.3% / 41.3% / -19.5% | absolute |
| vs BTC 1m / 3m / YTD | 8.2% / 20.1% / -5.4% | name − BTC |

**Skeptic honesty:** Only funding obs linked; OI/mark ULIDs missing. Relative outperformance vs BTC in trailing windows is **not** a trade signal without flow/L2 activity prints.


### NVDA (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 102.3M sh | Yahoo chart API v8 · fetched **2026-09-17T00:49:39Z** UTC (10:49 AEST) · brief `20260917-universe-scan-crypto-equity.json` |
| ADV 5d notional ≈ | $21.70B | same (last × ADV shares) |
| Scan last / prevClose | 212.17 / 223.67 | same snapshot (may differ from yfinance asof below) |
| Last close (series) | 213.90 | yfinance `NVDA` · asof **2026-09-16** · run 2026-09-17T11:15:47.495030+10:00 |
| RV 20d / 60d ann. | 45.5% / 40.4% | √252 |
| Max DD ~1y | -20.2% | 252 trading days |
| Ret 1m / 3m / YTD | -4.8% / 3.2% / 13.5% | ≈21/63d + YTD |
| vs SPY 1m / 3m / YTD | -2.4% / 2.5% / 2.6% | name − SPY |

**Skeptic honesty:** Extremely crowded AI long; Q3 guide public for weeks. Macro obs_ids ≠ name edge. Capex/ROI falsifiers required before thesis.


### AVGO (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 25.1M sh | Yahoo chart API v8 · fetched **2026-09-17T00:49:39Z** UTC (10:49 AEST) · brief `20260917-universe-scan-crypto-equity.json` |
| ADV 5d notional ≈ | $8.53B | same (last × ADV shares) |
| Scan last / prevClose | 339.27 / 364.38 | same snapshot (may differ from yfinance asof below) |
| Last close (series) | 339.51 | yfinance `AVGO` · asof **2026-09-16** · run 2026-09-17T11:15:47.495030+10:00 |
| RV 20d / 60d ann. | 34.5% / 40.3% | √252 |
| Max DD ~1y | -29.4% | 252 trading days |
| Ret 1m / 3m / YTD | -13.5% / -9.7% / -2.0% | ≈21/63d + YTD |
| vs SPY 1m / 3m / YTD | -11.1% / -10.5% / -12.9% | name − SPY |

**Skeptic honesty:** Satellite to NVDA (same AI-infra bet — do not double-count). Consensus ASIC/networking narrative; backlog conversion unshown.


### MSFT (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 17.6M sh | Yahoo chart API v8 · fetched **2026-09-17T00:49:39Z** UTC (10:49 AEST) · brief `20260917-universe-scan-crypto-equity.json` |
| ADV 5d notional ≈ | $8.75B | same (last × ADV shares) |
| Scan last / prevClose | 497.12 / 491.65 | same snapshot (may differ from yfinance asof below) |
| Last close (series) | 490.30 | yfinance `MSFT` · asof **2026-09-16** · run 2026-09-17T11:15:47.495030+10:00 |
| RV 20d / 60d ann. | 21.3% / 42.7% | √252 |
| Max DD ~1y | -34.5% | 252 trading days |
| Ret 1m / 3m / YTD | 2.3% / 24.7% / 4.3% | ≈21/63d + YTD |
| vs SPY 1m / 3m / YTD | 4.7% / 24.0% / -6.6% | name − SPY |

**Skeptic honesty:** Mega-cap duration + AI spend consensus. Elevated 60d vol vs 20d — regime shift in recent window; still not a mispricing claim.


### META (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 18.9M sh | Yahoo chart API v8 · fetched **2026-09-17T00:49:39Z** UTC (10:49 AEST) · brief `20260917-universe-scan-crypto-equity.json` |
| ADV 5d notional ≈ | $12.66B | same (last × ADV shares) |
| Scan last / prevClose | 670.24 / 653.69 | same snapshot (may differ from yfinance asof below) |
| Last close (series) | 670.24 | yfinance `META` · asof **2026-09-15** · run 2026-09-17T11:15:47.495030+10:00 |
| RV 20d / 60d ann. | 34.2% / 45.8% | √252 |
| Max DD ~1y | -32.5% | 252 trading days |
| Ret 1m / 3m / YTD | 13.6% / 12.9% / 3.2% | ≈21/63d + YTD |
| vs SPY 1m / 3m / YTD | 16.0% / 12.2% / -7.7% | name − SPY |

**Skeptic honesty:** Ads+AI ROI is consensus crowded long. **Note:** yfinance auto-adjusted Close for 2026-09-16 was NaN — series asof **2026-09-15** (last valid). Zero ad ARPU/DAU evidence in shortlist.


### JPM (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 8.3M sh | Yahoo chart API v8 · fetched **2026-09-17T00:49:39Z** UTC (10:49 AEST) · brief `20260917-universe-scan-crypto-equity.json` |
| ADV 5d notional ≈ | $2.92B | same (last × ADV shares) |
| Scan last / prevClose | 352.49 / 354.71 | same snapshot (may differ from yfinance asof below) |
| Last close (series) | 348.92 | yfinance `JPM` · asof **2026-09-16** · run 2026-09-17T11:15:47.495030+10:00 |
| RV 20d / 60d ann. | 15.9% / 18.0% | √252 |
| Max DD ~1y | -15.5% | 252 trading days |
| Ret 1m / 3m / YTD | -3.3% / 5.8% / 8.7% | ≈21/63d + YTD |
| vs SPY 1m / 3m / YTD | -0.9% / 5.1% / -2.2% | name − SPY |

**Skeptic honesty:** Higher-for-longer NII story is the obvious post-hike frame — **already priced** narrative risk. Need credit/NII primary prints.


### XLF (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 36.3M sh | Yahoo chart API v8 · fetched **2026-09-17T00:49:39Z** UTC (10:49 AEST) · brief `20260917-universe-scan-crypto-equity.json` |
| ADV 5d notional ≈ | $2.06B | same (last × ADV shares) |
| Scan last / prevClose | 56.85 / 57.06 | same snapshot (may differ from yfinance asof below) |
| Last close (series) | 55.93 | yfinance `XLF` · asof **2026-09-16** · run 2026-09-17T11:15:47.495030+10:00 |
| RV 20d / 60d ann. | 13.7% / 13.0% | √252 |
| Max DD ~1y | -14.8% | 252 trading days |
| Ret 1m / 3m / YTD | -2.9% / 3.3% / 2.7% | ≈21/63d + YTD |
| vs SPY 1m / 3m / YTD | -0.5% / 2.5% / -8.3% | name − SPY |

**Skeptic honesty:** Diversifier to JPM only; weak/stale secondary blogs are not evidence. Prefer JPM as primary financials name.


### XOM (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 13.5M sh | Yahoo chart API v8 · fetched **2026-09-17T00:49:39Z** UTC (10:49 AEST) · brief `20260917-universe-scan-crypto-equity.json` |
| ADV 5d notional ≈ | $2.29B | same (last × ADV shares) |
| Scan last / prevClose | 169.32 / 164.23 | same snapshot (may differ from yfinance asof below) |
| Last close (series) | 163.32 | yfinance `XOM` · asof **2026-09-16** · run 2026-09-17T11:15:47.495030+10:00 |
| RV 20d / 60d ann. | 26.2% / 25.7% | √252 |
| Max DD ~1y | -20.1% | 252 trading days |
| Ret 1m / 3m / YTD | 1.2% / 15.9% / 35.8% | ≈21/63d + YTD |
| vs SPY 1m / 3m / YTD | 3.6% / 15.1% / 24.9% | name − SPY |

**Skeptic honesty:** Fed hike because inflation sticky **≠** XOM upside (Skeptic: correlation-as-causation). Oil supply/refining dominate; pipeline-restoration mean-reversion risk.


---

## Active calls — summary table

| Name | Liquidity | RV20 | RV60 | MDD~1y | 1m | 3m | YTD | Rel (bench) 1m/3m/YTD | Bench |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTC | HL dayNtl $3.05B / OI$ $2.90B @ 2026-09-17 10:28 AEST stale | 35.6% | 39.1% | -53.1% | 18.1% | 21.2% | -14.1% | — (absolute) | — |
| ETH | HL dayNtl $1.37B / OI$ $2.37B @ 2026-09-17 10:28 AEST stale | 41.7% | 58.9% | -66.6% | 26.3% | 41.3% | -19.5% | 8.2% / 20.1% / -5.4% | BTC |
| NVDA | ADV5d 102.3M sh / $21.70B | 45.5% | 40.4% | -20.2% | -4.8% | 3.2% | 13.5% | -2.4% / 2.5% / 2.6% | SPY |
| AVGO | ADV5d 25.1M sh / $8.53B | 34.5% | 40.3% | -29.4% | -13.5% | -9.7% | -2.0% | -11.1% / -10.5% / -12.9% | SPY |
| MSFT | ADV5d 17.6M sh / $8.75B | 21.3% | 42.7% | -34.5% | 2.3% | 24.7% | 4.3% | 4.7% / 24.0% / -6.6% | SPY |
| META | ADV5d 18.9M sh / $12.66B | 34.2% | 45.8% | -32.5% | 13.6% | 12.9% | 3.2% | 16.0% / 12.2% / -7.7% | SPY |
| JPM | ADV5d 8.3M sh / $2.92B | 15.9% | 18.0% | -15.5% | -3.3% | 5.8% | 8.7% | -0.9% / 5.1% / -2.2% | SPY |
| XLF | ADV5d 36.3M sh / $2.06B | 13.7% | 13.0% | -14.8% | -2.9% | 3.3% | 2.7% | -0.5% / 2.5% / -8.3% | SPY |
| XOM | ADV5d 13.5M sh / $2.29B | 26.2% | 25.7% | -20.1% | 1.2% | 15.9% | 35.8% | 3.6% / 15.1% / 24.9% | SPY |


---

## Appendix — watch-only (do not center)

### UNI (watch)

| Metric | Value | Source |
| --- | --- | --- |
| HL dayNtl / OI$ | $31.2M / $57.8M | HL · 2026-09-17T00:28:03Z · **stale/partial** |
| funding | 0.0000125000 | same · **no UNI funding obs_id in known set** |
| Spot series | Kraken `UNIUSD` (yfinance `UNI-USD` unavailable/delisted stub) · last 6.7085 · asof 2026-09-17 |
| RV20 / RV60 / MDD | 116.3% / 98.2% / -75.1% | √365 |
| Ret 1m/3m/YTD | 103.8% / 117.3% / 15.8% | large trailing bounce from ~$3.20 (2026-08-14) — **not** an upside thesis |
| vs BTC | 85.7% / 96.1% / 30.0% | |

### AAVE (watch)

| Metric | Value | Source |
| --- | --- | --- |
| HL dayNtl / OI$ | $12.9M / $67.5M | HL · 2026-09-17T00:28:03Z · **stale/partial** |
| funding | -0.0000052051 | same · no AAVE funding obs_id in known set |
| Last / RV20/60 / MDD | 120.01 / 57.8% / 90.4% / -80.3% | yfinance `AAVE-USD` · asof 2026-09-17 |
| Ret 1m/3m/YTD | 34.5% / 60.6% / -19.3% | |
| vs BTC | 16.3% / 39.4% / -5.2% | |

### SMH (watch)

| Metric | Value | Source |
| --- | --- | --- |
| ADV 5d | 6.9M sh / $3.74B | Yahoo · 2026-09-17T00:49:39Z |
| Last / RV20/60 / MDD | 545.56 / 32.0% / 45.3% / -24.6% | yfinance · asof 2026-09-16 |
| Ret 1m/3m/YTD | -8.2% / -11.4% / 46.1% | |
| vs SPY | -5.8% / -12.2% / 35.2% | YTD outperformance ≠ edge under hawkish tape |

---

## Data gaps / what unlocks a real thesis

| Gap | Why it blocks | What unlocks |
| --- | --- | --- |
| HL live refresh HTTP **429** | fundingHistory, candleSnapshot, fresh metaAndAssetCtxs missing | Successful Intel ingest with obs_ids + continuous fundingHistory |
| docs/ops TSV / Postgres obs payloads **not readable via gh** this pass | Cannot verify obs_id numeric payloads beyond shortlist cites + lab JSON | Ops export TSV or Research DB read of `01M2PCXAFASC2V0WCGWR0E8MZT` etc. |
| ETH OI/mark ULIDs missing from known set | ETH RV vs BTC lacks MM-linked OI evidence | Ingest ETH OI/mark obs_ids |
| Spot BTC/ETH ETF **flow series** | Conditional upside claims unfalsifiable | Primary ETF flow print multi-day |
| Equity name-level fundamentals | Macro obs_ids are backdrop only (Skeptic) | 10-Q / transcript extracts + primary series |
| META 2026-09-16 Close NaN in yfinance auto-adjust | As-of lag vs peers | Vendor fix or alternate vendor Close |
| UNI yfinance broken | Watch metrics depend on Kraken public OHLC | Confirm vendor mapping or pin Kraken as source of record |
| No must-cuts / no thesis folders in this pack | Per brief rules | Separate Research PR when evidence clears Skeptic bar |

---

## Provenance index

| Artifact | Path |
| --- | --- |
| This pack | `research/queue/QUANT-20260917-active-calls.md` |
| Builder script | `research/queue/quant-20260917/build_quant_pack.py` |
| Metrics CSV | `research/queue/quant-20260917/metrics_active_and_watch.csv` |
| Corr CSV | `research/queue/quant-20260917/corr_matrix_60d.csv` |
| Returns (corr window) | `research/queue/quant-20260917/daily_returns_60d_corr_window.csv` |
| Returns (full panel) | `research/queue/quant-20260917/daily_returns_full_panel.csv` |
| Vol/MDD CSV | `research/queue/quant-20260917/vol_mdd_summary.csv` |
| Equity ADV CSV | `research/queue/quant-20260917/equity_adv_5d_from_universe_scan.csv` |
| Run meta | `research/queue/quant-20260917/run_meta.json` |
| Pack README | `research/queue/quant-20260917/README.md` |
| HL raw | `Intel lab HL cache (file-only; not in-repo)` |
| HL PARTIAL top25 | `(lab path omitted)/intel-briefs/20260917-universe-scan-PARTIAL-hl-top25.json` (`hl_capture`: 2026-09-17T00:28:03Z) |
| HL refresh 429 log | `(lab path omitted)/intel-briefs/20260917-rqa-hl-refresh.md` |
| Universe scan (ADV source JSON) | `(lab path omitted)/intel-briefs/20260917-universe-scan-crypto-equity.json` (CSV extract in-repo as Equity ADV CSV) |
| Skeptic frame | `(lab path omitted)/UNIVERSE-20260917-skeptic-review.md` |

**Hard rules followed:** no fabricated numbers; unavailable labeled with why; no universe expand; no must-cuts; no thesis folders; rejection honesty preferred.
