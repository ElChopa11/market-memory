# Universe shortlist — 2026-09-17

| Field | Value |
|---|---|
| **Purpose** | Principal-facing **intent-level watchlist proposal** for ElChopa11/market-memory research queue |
| **Date** | 2026-09-17 (Australia/Sydney, AEST) |
| **Status** | `intent-level watchlist proposal` — **not orders, not theses, not trades** |
| **Lab venues** | Crypto: Hyperliquid perps · Equities: liquid US stocks/ETFs (NYSE/NASDAQ) |
| **HL liquidity capture** | `metaAndAssetCtxs` **2026-09-17T00:28:03Z** (= **10:28 AEST**) · file-only (no obs_ids on sheet) · `Intel lab capture file (not in-repo; ask Intel/Ops)` · PARTIAL top25: `Intel PARTIAL HL top25 JSON (lab file; not yet in-repo)` |

## Macro frame (hawkish)

FOMC **+25bp** to FF **3.75–4.00%** (12–0); IORB **3.90%**; primary credit **4.00%**; Reuters/SEP path toward **higher end-2026** rates. Senate cloture on **H.R.3633** (digital commodities) rejected **49–50**.

**Known MM observation_ids (cite only these):**
- Fed FF: `01M2PCX8ZJZCKC52NQ03PHNZWE`
- IORB: `01M2PCX9005R4S8GRPQJP96CRP`
- Primary credit: `01M2PCX90C2J9RPG17CSZDTV3Q`
- FOMC +25bp: `01M2PCX90PQAP96J62RR6EWQ35`
- Reuters (partial): `01M2PCX91243QK9V8HCCWQFASY`
- BTC funding / OI / mark / oracle / mid: `01M2PCXAFASC2V0WCGWR0E8MZT` · `01M2PCXAFMC3792Y1PQ3H2ACVQ` · `01M2PCXAEE4BRXTPMV56SYN56V` · `01M2PCXAEY18W6290P82NECSM7` · `01M2PCXACWWCDJRR2GJ20RV7D4`
- ETH funding: `01M2PCPEK2ZXFDKPK0TDZZZ5M4`
- Senate H.R.3633 (no ULID): https://www.senate.gov/legislative/LIS/roll_call_votes/vote1192/vote_119_2_00234.htm

**Honesty gate:** Under hawkish Fed + CLARITY setback, **pure beta crypto upside is weak**. Crypto entries below are **conditional** (regulatory revival, ETF flow confirmation, funding/basis dislocations, venue-native HYPE liquidity) — not vibes.

---

## Crypto (10) — Hyperliquid perps

Ranked preference: liquid majors/L2 over idiosyncratic/lottery. HL dayNtlVlm / OI$ at capture (AEST 10:28).

### 1. BTC
1) **why TRADEABLE now:** HL perp #1 by dayNtl (~$3.05B) and OI$ (~$2.90B); maxLev 40; deepest book on lab venue.  
2) **why UPSIDE THIS CYCLE (falsifiable):** Conditional — (a) spot BTC ETF **net inflow** resume multi-day; (b) funding/basis dislocation mean-reverts without OI collapse; (c) digital-commodity legislative path **revives** after H.R.3633 cloture fail. Not a “hawkish Fed = BTC up” claim.  
3) **key INVALIDATION:** Sustained ETF outflows + rising real rates + CLARITY dead-end with no substitute bill; HL funding flip extreme with OI unwind.  
4) **evidence links:** obs `01M2PCXAFASC2V0WCGWR0E8MZT` (funding), `01M2PCXAFMC3792Y1PQ3H2ACVQ` (OI), `01M2PCXAEE4BRXTPMV56SYN56V` (mark), `01M2PCXAEY18W6290P82NECSM7` (oracle), `01M2PCXACWWCDJRR2GJ20RV7D4` (mid); macro `01M2PCX90PQAP96J62RR6EWQ35`, `01M2PCX91243QK9V8HCCWQFASY`; Senate https://www.senate.gov/legislative/LIS/roll_call_votes/vote1192/vote_119_2_00234.htm (2026-09-15).  
5) **confidence:** 0.55 · **still need:** verified multi-day ETF flow series; HL fundingHistory continuity; basis vs CME.

### 2. ETH
1) **why TRADEABLE now:** HL #2 dayNtl (~$1.37B), OI$ (~$2.37B); maxLev 25; core lab pair with BTC.  
2) **why UPSIDE THIS CYCLE:** Conditional — ETH ETF flow confirmation; L2 fee/activity recovery; funding dislocation vs BTC (relative value, not beta-only). Hawkish Fed compresses duration — upside requires **flow or activity** proof.  
3) **key INVALIDATION:** ETH underperforms BTC on sticky ETF outflows; L2 activity declines QoQ; funding stays max long without OI support.  
4) **evidence links:** ETH funding obs `01M2PCPEK2ZXFDKPK0TDZZZ5M4`; HL capture sheet (no ETH OI/mark ULIDs in known set); macro same as BTC; Senate URL above.  
5) **confidence:** 0.50 · **still need:** ETH ETF flows; HL ETH OI/mark obs_ids; staking/fee revenue print.

### 3. HYPE
1) **why TRADEABLE now:** HL #4 dayNtl (~$514M), OI$ (~$1.61B) — liquid enough for primary; venue-native token, maxLev 10.  
2) **why UPSIDE THIS CYCLE:** Conditional on **HL volume/OI share** expansion and fee/token utility narrative surviving risk-off; falsify via HL aggregate dayNtl and HYPE OI$ vs majors.  
3) **key INVALIDATION:** HYPE dayNtl collapses vs BTC/ETH; OI$ bleed; venue competitive share loss.  
4) **evidence links:** HL PARTIAL top25 `Intel PARTIAL HL top25 JSON (lab file; not yet in-repo)` (capture 2026-09-17T00:28:03Z); raw ctxs file; **no** HYPE observation_id in known set — do not invent.  
5) **confidence:** 0.45 · **still need:** HYPE obs_ids; fee share / token unlock calendar; correlation to BTC beta.

### 4. SOL
1) **why TRADEABLE now:** HL #5 dayNtl (~$165M), OI$ (~$523M); maxLev 20; major L1 liquidity.  
2) **why UPSIDE THIS CYCLE:** Conditional — SOL ETF/flow or network fee growth vs BTC beta; defer pure meme-driven upside. Falsify with fee revenue + stablecoin settlement share.  
3) **key INVALIDATION:** Network outage / fee collapse; outflows / OI unwind faster than BTC; lottery narrative dominates without activity.  
4) **evidence links:** HL liquidity ranks (file-only); macro obs_ids for rate backdrop; Senate URL for crypto-policy drag.  
5) **confidence:** 0.42 · **still need:** SOL-specific ETF/flow data; HL SOL funding/OI obs_ids.

### 5. XRP
1) **why TRADEABLE now:** HL #6 dayNtl (~$109M), OI$ (~$191M); maxLev 20.  
2) **why UPSIDE THIS CYCLE:** Conditional on **regulatory clarity revival** (post–H.R.3633 cloture fail) and institutional corridor volume — not rate-cut beta.  
3) **key INVALIDATION:** Further legislative dead-ends; OI/dayNtl fall out of top liquid tier; adverse legal headlines without offsetting clarity.  
4) **evidence links:** Senate roll call https://www.senate.gov/legislative/LIS/roll_call_votes/vote1192/vote_119_2_00234.htm (2026-09-15); bill tracker https://www.congress.gov/bill/119th-congress/house-bill/3633; HL ranks.  
5) **confidence:** 0.40 · **still need:** primary legal/regulatory calendar; HL XRP funding obs_id.

### 6. ARB
1) **why TRADEABLE now:** HL #7 dayNtl (~$57M), OI$ (~$28M); liquid L2 perp vs mid-cap lottery.  
2) **why UPSIDE THIS CYCLE:** Conditional — Arbitrum fee/TVL share vs ETH L2 peers; sequencer/revenue catalysts falsifiable on Dune/DefiLlama-class metrics (to be pulled before thesis).  
3) **key INVALIDATION:** L2 share loss to Base/OP/others; dayNtl drops below researchable threshold; pure ETH-beta with no activity edge.  
4) **evidence links:** HL ranks only (no ARB obs_id in known set).  
5) **confidence:** 0.35 · **still need:** L2 market-share series; unlock/vesting; HL ARB funding/OI obs.

### 7. NEAR
1) **why TRADEABLE now:** HL #8 dayNtl (~$54M), OI$ (~$173M) — strong OI$ vs peers.  
2) **why UPSIDE THIS CYCLE:** Conditional AI/xchain narrative **only if** on-chain activity/fees confirm; else reject as mid-beta.  
3) **key INVALIDATION:** Activity/fee prints miss; OI$ bleeds while price holds (crowded); falls to mid-only mean-reversion.  
4) **evidence links:** HL ranks (file-only).  
5) **confidence:** 0.33 · **still need:** NEAR fee/DAU; funding obs_id; AI partnership revenue proof.

### 8. UNI
1) **why TRADEABLE now:** HL #12 dayNtl (~$31M), OI$ (~$58M); DeFi blue-chip liquidity on HL.  
2) **why UPSIDE THIS CYCLE:** Conditional fee-switch / governance / volume share vs CEXs — falsify with Uniswap volume and fee accrual policy outcomes.  
3) **key INVALIDATION:** Fee-switch delayed indefinitely; DEX volume share down; regulatory drag post–H.R.3633.  
4) **evidence links:** HL ranks; Senate URL (crypto policy).  
5) **confidence:** 0.38 · **still need:** fee-switch timeline primary sources; UNI HL funding obs.

### 9. AAVE
1) **why TRADEABLE now:** HL #16 dayNtl (~$13M), OI$ (~$67M); solid OI$; DeFi credit blue-chip.  
2) **why UPSIDE THIS CYCLE:** Conditional — borrow demand / revenue in higher-rate crypto credit; falsify with Aave revenue and utilization (higher-for-longer can **help** credit demand if risk-on crypto returns).  
3) **key INVALIDATION:** Bad-debt event; utilization collapse; dayNtl illiquid vs majors.  
4) **evidence links:** HL ranks; macro higher-for-longer via `01M2PCX90PQAP96J62RR6EWQ35`, `01M2PCX91243QK9V8HCCWQFASY`.  
5) **confidence:** 0.36 · **still need:** Aave revenue dashboards; HL AAVE funding obs.

### 10. LINK
1) **why TRADEABLE now:** HL #25 dayNtl (~$8.3M), OI$ (~$59M) — lowest volume in this 10 but **OI$ and major-oracle role** keep it researchable vs lottery; prefer over SUI/DOGE for thesis clarity.  
2) **why UPSIDE THIS CYCLE:** Conditional — oracle / CCIP / RWA data demand with TradFi tokenization; falsify with LINK staking/revenue and integration counts.  
3) **key INVALIDATION:** DayNtl slips further (execution risk); oracle share loss; no RWA/CCIP revenue confirmation.  
4) **evidence links:** HL ranks (file-only).  
5) **confidence:** 0.32 · **still need:** CCIP/RWA revenue; HL LINK funding obs; ADV stability check.

---

## Equities (10) — liquid US names/ETFs

Selected for **falsifiable cycle upside under hawkish Fed** (AI infra power, higher-for-longer financials, energy cash flow, sticky-inflation gold, defensive growth). Deferred index-beta (SPY/QQQ) and rate-hurt small-caps (IWM).

### 1. NVDA (NASDAQ)
1) **why TRADEABLE now:** Mega-liquid NASDAQ (~$5.3–5.6T mkt cap; ADV ~120M+ shs proxies as of Sep 2026 public comps).  
2) **why UPSIDE THIS CYCLE:** AI data-center GPU demand / supply-constrained guide — survives hawkish Fed **if** hyperscaler capex holds; falsify on next hyperscaler capex guides + NVDA data-center revenue.  
3) **key INVALIDATION:** Hyperscaler capex cuts; China/export shock; gross-margin miss on competition.  
4) **evidence links:** https://www.fool.com/investing/2026/09/13/nvidia-vs-broadcom-which-trillion-dollar-ai-chip-s/ (2026-09-13); https://www.marketbeat.com/compare-stocks/?Symbols=NASDAQ%3ASMH%2CNASDAQ%3ANVDA%2CNASDAQ%3AAVGO ; macro `01M2PCX90PQAP96J62RR6EWQ35`.  
5) **confidence:** 0.58 · **still need:** latest 10-Q/earnings transcript extract; power/grid bottleneck trackers.

### 2. AVGO (NASDAQ)
1) **why TRADEABLE now:** Mega-liquid (~$1.7T; ADV ~23–25M shs proxies).  
2) **why UPSIDE THIS CYCLE:** Custom AI ASIC + networking attach — falsify on AI semiconductor revenue guide path (mgmt AI roadmap). Rate hike less fatal if AI backlog cash-converts.  
3) **key INVALIDATION:** AI semi guide cut; customer concentration miss; VMware/software drag.  
4) **evidence links:** https://www.fool.com/investing/2026/09/13/nvidia-vs-broadcom-which-trillion-dollar-ai-chip-s/ (2026-09-13); MarketBeat compare URL above.  
5) **confidence:** 0.55 · **still need:** customer cohort disclosure; next earnings AI line-item.

### 3. SMH (NASDAQ ETF)
1) **why TRADEABLE now:** Liquid semis ETF (~$71B AUM proxy; ADV ~9–10M shs) — clearer AI-infra driver than XLK/QQQ.  
2) **why UPSIDE THIS CYCLE:** Basket on hyperscaler AI buildout (NVDA/AVGO/MU/TSM-heavy); falsify with SIA billings / TSMC monthly / hyperscaler capex.  
3) **key INVALIDATION:** Capex pause (2022-style); memory/semis inventory glut.  
4) **evidence links:** https://finance.yahoo.com/markets/stocks/articles/smh-etf-investors-watch-hyperscaler-021120280.html ; MarketBeat SMH stats; Fed hike backdrop obs_ids.  
5) **confidence:** 0.52 · **still need:** current top holdings weights; options liquidity check.

### 4. MSFT (NASDAQ)
1) **why TRADEABLE now:** Mega-cap cash-flow fortress; ultra-liquid.  
2) **why UPSIDE THIS CYCLE:** Azure AI + enterprise spend durability under higher rates — falsify on Azure growth deceleration and capex ROI commentary. Quality compounding, not rate-cut beta.  
3) **key INVALIDATION:** Azure growth break; AI capex ROI doubt; multiple compression without earnings hold.  
4) **evidence links:** Macro higher-for-longer `01M2PCX90PQAP96J62RR6EWQ35`, `01M2PCX91243QK9V8HCCWQFASY`; Fed statement https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm (2026-09-16).  
5) **confidence:** 0.54 · **still need:** latest Azure metrics from earnings; buyback/FCF print.

### 5. META (NASDAQ)
1) **why TRADEABLE now:** Mega-liquid cash-rich mega-cap.  
2) **why UPSIDE THIS CYCLE:** Ads + AI infra ROI — falsify on ad growth and Reality Labs / infra spend efficiency; can fund AI build even with higher WACC.  
3) **key INVALIDATION:** Ad recession; infra spend without ROI; regulatory ad-targeting hits.  
4) **evidence links:** Macro obs_ids; Fed https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm (SEP 2026-09-16).  
5) **confidence:** 0.50 · **still need:** latest ad ARPU / family DAU; capex guide.

### 6. JPM (NYSE)
1) **why TRADEABLE now:** Flagship US bank; deep NYSE liquidity.  
2) **why UPSIDE THIS CYCLE:** **Higher-for-longer NIM / NII** and capital-markets rebound — direct falsifiable link to FF path (SEP median ~4.1% end-2026).  
3) **key INVALIDATION:** Credit losses spike; NIM compression despite hike; severe curve inversion hurt.  
4) **evidence links:** https://am.jpmorgan.com/us/en/asset-management/liq/insights/liquidity-insights/updates/higher-for-longer-creates-opportunity/ ; SEP https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm (2026-09-16); obs `01M2PCX8ZJZCKC52NQ03PHNZWE`, `01M2PCX90PQAP96J62RR6EWQ35`.  
5) **confidence:** 0.56 · **still need:** latest NII guide; charge-off trends.

### 7. XLF (NYSE Arca ETF)
1) **why TRADEABLE now:** Primary liquid US financials sector ETF (ADV tens of millions historically; low ER).  
2) **why UPSIDE THIS CYCLE:** Sector expression of higher-for-longer + capital markets — falsify with bank NII aggregate and credit spreads. Diversifies single-name JPM.  
3) **key INVALIDATION:** Regional-bank stress reprise; credit event; curve inversion dominates NIM.  
4) **evidence links:** XLF analysis context https://gomdorieconomic.com/2026/04/22/xlf-financial-select-sector-spdr-fund-analysis/ ; Fed hike obs_ids.  
5) **confidence:** 0.53 · **still need:** live AUM/ADV confirm; KRE divergence monitor.

### 8. XOM (NYSE)
1) **why TRADEABLE now:** Mega-liquid energy major.  
2) **why UPSIDE THIS CYCLE:** Energy cash-flow / inflation-stickiness hedge while Fed hikes on elevated inflation — falsify with crude strip, refining margins, buyback capacity.  
3) **key INVALIDATION:** Oil demand shock / price collapse; windfall-tax; FCF miss.  
4) **evidence links:** FOMC “inflation remains elevated” https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm (2026-09-16); CNBC hike coverage https://www.cnbc.com/2026/09/16/fed-rate-decision-september-2026.html (2026-09-16); obs `01M2PCX90PQAP96J62RR6EWQ35`.  
5) **confidence:** 0.48 · **still need:** latest production/FCF guide; oil inventory prints.

### 9. GLD (NYSE Arca ETF)
1) **why TRADEABLE now:** Most liquid US gold bullion ETF.  
2) **why UPSIDE THIS CYCLE:** **Conditional** — sticky inflation / geopolitics / CB demand; honest caveat: hiking Fed + rising real yields are **bearish risk** for gold (JPM research). Upside only if inflation stickiness outweighs real-rate drag.  
3) **key INVALIDATION:** Real yields rise further with growth strong; Western ETF outflows persistent; CB buying fades.  
4) **evidence links:** https://www.jpmorgan.com/insights/global-research/commodities/gold-prices ; https://www.ssga.com/us/en/intermediary/etfs/spdr-gold-shares-gld ; macro `01M2PCX91243QK9V8HCCWQFASY`.  
5) **confidence:** 0.40 · **still need:** GLD flows; real-rate (TIPS) series; CB purchase data.

### 10. LLY (NYSE)
1) **why TRADEABLE now:** Mega-cap pharma; highly liquid.  
2) **why UPSIDE THIS CYCLE:** GLP-1 / obesity franchise cash-flow growth **less rate-sensitive on demand** than high-duration tech — falsify on script growth, supply, and margin. Quality defensive growth under hawkish Fed.  
3) **key INVALIDATION:** Pipeline/trial miss; compounding competition; pricing/reimbursement shock.  
4) **evidence links:** Macro frame obs_ids (rate backdrop only — drug thesis is idiosyncratic); Fed https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm (2026-09-16).  
5) **confidence:** 0.47 · **still need:** latest script/IQVIA proxies; capacity guidance; valuation vs growth.

---

## Rejected / deferred

| Bucket | Names | Why |
|---|---|---|
| **Idiosyncratic / elevated risk (defer as primary)** | **ZEC** | HL #3 by dayNtl (~$932M) but elevated idiosyncratic — not preferred major/L2; defer per lab seed. |
| **Lottery / memes (reject as primary)** | **PUMP**, FARTCOIN, TRUMP, kPEPE, WIF, CASHCAT, USELESS, etc. | Volume without falsifiable cycle driver; lottery tickets. |
| **Mid-only mean-reversion (reject)** | Thin mid-cap alts with dayNtl ≪ majors and no catalyst beyond “oversold mid” | Explicitly rejected — no mid-only MR names on this shortlist. |
| **Equities deferred** | **SPY, QQQ** (index-level beta — prefer single-name/sector drivers); **IWM** (small-caps hurt by higher-for-longer); **XLK** (prefer SMH for clearer AI-infra); **XLE** (overlap with XOM); **TSLA** (high-duration / lottery-relative under hawkish); **AAPL, AMZN, GOOGL, BRK-B** (quality but lower cycle specificity vs selected 10 this pass) |
| **Crypto near-misses deferred** | SUI, DOGE | Liquid enough on HL but meme/beta-heavier than LINK/AAVE for this cycle’s falsifiable set. |

---

**Explicit:** Intent-level watchlist only. No thesis folders. No orders. No fabricated observation_ids. Promote to thesis only after listed “data still needed” gates clear.
