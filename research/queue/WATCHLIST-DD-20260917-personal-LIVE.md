# WATCHLIST-DD-20260917-personal-LIVE — Principal personal TV due-diligence (LIVE scrape provenance)

> IMP-005: historical personal-TV labels MAKE / WATCH / CUT are **not** trades. Map: MAKE → `RESEARCH_PRIORITY`; WATCH → `MONITOR` / `watch_only`; CUT → `REJECT`.
| Field | Value |
|---|---|
| **Date** | 2026-09-17 (Australia/Sydney, **AEST**) |
| **Repo** | `ElChopa11/market-memory` (private research) |
| **Ask** | LIVE browser scrape → inventory provenance + MAKE / WATCH / CUT disposition vs locked lab universe + QUANT honesty |
| **Privacy** | **Private research only.** **No Telegram.** **No trades.** |
| **Inventory SoT** | **Intel LIVE scrape** (Don-confirmed) — `research/queue/watchlist-live/20260917-tv-live-symbol-list.json` (+ `.csv`) |
| **Intel scrape** | **2026-09-17 12:27:33 AEST** (`2026-09-17T02:27:33Z`) · no login wall |
| **Research scrape (secondary)** | Base 12:26:13 · Racksor 12:26:29 · Crypto 12:26:44 AEST · `research/queue/watchlist-live/20260917-live-inventory.json` — **stale for Base membership** (overcounted CASHCAT on Base) |
| **TV lists** | Base `194324969` · Racksor Capital `343370615` · Crypto HL `330128831` |
| **Counts (LIVE SoT)** | Base **UI label 63 / rendered 62** · Racksor **6** · Crypto **15** · unique raw symbols **80** · raw rows **83** |
| **Lab lock** | `config/universe.yaml` **main** · version `2026-09-17` · status `locked` |
| **QUANT** | `research/queue/quant-20260917/` (PR **#19**) · scorecard PR **#22** · FAIL patch PR **#23** |
| **Appendix** | `research/queue/INVALIDATION-20260917-fail-pairs-quant.md` (demoted FAIL pairs) |
| **Disposition board** | Skeptic-final from PR **#25** / **#26** after reclass: **MAKE 2 / WATCH 25 / CUT 36** — **must cite LIVE scrape timestamps** for inventory; board itself aligned with Skeptic-passed #25 |
| **Hard rules** | rel≠α · HL stale not primary · corr≠causation · memory-semi **killed** · must-cuts = learning · prefer rejection · **no invented 63rd Base symbol** |

**Provenance supersession:** PR **#25** `WATCHLIST-DD-20260917-personal.md` was based on a **recycled extract**. **This LIVE file supersedes #25 for inventory provenance.** Disposition board may align with Skeptic-passed #25 board AFTER reclass (MAKE 2 / WATCH 25 / CUT 36) but **must cite LIVE scrape timestamps** above.

**What RESEARCH_PRIORITY / MONITOR / REJECT means here** (historical pack labels MAKE / WATCH / CUT): research-queue disposition for the **personal TV inventory**, not orders.
- **RESEARCH_PRIORITY** (historical **MAKE**) = liquid, falsifiable **in-universe membership** candidate (keep or propose into thesis priority). Not a Quant Board verdict and not a trade.
- **MONITOR** (historical **WATCH**) = monitor / context / demoted expectation / proxy — **no** thesis-priority membership.
- **REJECT** (historical **CUT**) = reject-learn (lottery, meme, must-cut archive, killed sleeve, thin narrative, double-count).

---

## 0. TLDR (6 lines)

1. **LIVE SoT (Intel 12:27:33 AEST):** Base **UI 63 / rendered 62** (do **not** invent a 63rd) · Racksor 6 · Crypto 15 · unique **80** · no login wall. Dumps: `research/queue/watchlist-live/` (+ screenshots under Intel `tv-live/`).
2. **Delta vs Research 12:26 Base extract:** **`CASHCATUSDC.P` removed from Base** (Research listed it on Base → 63 rows; LIVE Base does **not**). CASHCAT remains on **Crypto only** → still **CUT** (meme). Distinct underlyings after normalize: still **63** (CASHCAT present via Crypto).
3. **Delta vs prior recycled extract (distinct underlyings / symbols):** **zero** at underlying level — same names as #25 board; only Base-list membership hygiene changed.
4. **MAKE 2 · WATCH 25 · CUT 36** (Skeptic #26 REVISE applied). Pairs: **1** valid monitor (**BTC/GOLD**) · **6** invalid/CUT (incl. **BTC/SLV**).
5. **Sector coverage claim FAILS** (same conclusion): crypto + AI/tech + macro dashboard; missing staples/utilities/REITs/materials depth/healthcare depth/banks/energy equities.
6. **Lock gaps still missing from TV:** AVGO, MSFT, META, JPM, XLF, XOM, AAVE, SMH. Memory-semi **killed**. No Telegram. No trades.

---

## 1. LIVE inventory provenance

### 1.1 Scrape timestamps (cite both)

| Source | Role | Timestamp (AEST) | Artifact (repo path) |
|---|---|---|---|
| **Intel LIVE** | **Source of truth (Don-confirmed)** | **2026-09-17 12:27:33 AEST** | `research/queue/watchlist-live/20260917-tv-live-symbol-list.json` · `.csv` |
| Research browser | Secondary / earlier pass | Base **12:26:13** · Racksor **12:26:29** · Crypto **12:26:44** · file `scraped_at_aest` **12:26:44+10:00** | `research/queue/watchlist-live/20260917-live-inventory.json` |
| Screenshot dumps | Visual audit | ~12:26 AEST | Intel `tv-live/` (`194324969.png`, `343370615.png`, `330128831.png` + `.txt`) |

**Login:** `login_required: false` / `login_blocked: false` on all three lists.

### 1.2 LIVE counts (Intel SoT)

| List | ID | UI label | Rendered | Note |
|---|---|---:|---:|---|
| Base List | `194324969` | **63** | **62** | UI-vs-rendered discrepancy — **no 63rd invented** |
| Racksor Capital | `343370615` | 6 | 6 | unchanged |
| Crypto | `330128831` | 15 | 15 | unchanged |
| **Unique symbols** | — | — | **80** | across all lists |
| **Raw rows** | — | — | **83** | 62+6+15 (cross-list dupes allowed in raw) |

### 1.3 Delta notes (required)

| Compare | Result |
|---|---|
| **LIVE Base vs Research 12:26 Base** | Research had **`CASHCATUSDC.P` on Base** (63 symbols). **LIVE Base does NOT** include `CASHCATUSDC.P`. Only delta on Base. |
| **CASHCAT membership (LIVE)** | **Crypto list only** (`330128831`). Disposition remains **CUT** (meme). |
| **Distinct underlyings vs #25 recycled extract** | **Zero** — same normalized underlyings (63) and pair set (7). Board dispositions unchanged by scrape reconcile. |
| **Racksor / Crypto vs Research 12:26** | Identical membership (6 / 15). |

### 1.4 Normalization rules (unchanged)

Strip `.P` / `USDT` / `USDC` / `USD`; `BTC1!`→`BTC`; `NQ1!`→`NQ`; `CL1!`→`CL`; `COPPER1!`→`COPPER`; `NG1!`→`NG`; `UXJ2026`→`UX`; `SKHYNIXUSDC.P`→`SKHYNIX`; `SAMSUNGUSDT.P`→`SAMSUNG` (crypto-listed proxy ≠ KRX Samsung Electronics); `SPXUSDT.P`→`SPX6900` (meme) **≠** cash `SPX` index; `ETHBTC`→pair `ETH/BTC`. Cross-list dupes collapsed (e.g. `NEARUSDT.P` + `NEARUSDC.P` → **NEAR**).

---

## 2. Live inventory tables (symbol · list · type · scrape timestamp)

**Type key:** `crypto_perp` · `equity` · `etf` · `futures` · `macro` · `pair` · `ratio` (structure/dominance treated as `macro`).

**Scrape timestamp column:** Intel LIVE **12:27:33 AEST** for all rows below (SoT). Research timestamps noted in §1.1 only.

### 2.1 Base List — 62 rendered (UI label 63)

| Symbol | List | Type | Notes |
|---|---|---|---|
| ASTERUSDT.P | Base | crypto_perp | lottery → CUT |
| DOGEUSDT | Base | crypto_perp | meme → CUT |
| NEARUSDT.P | Base | crypto_perp | must-cut → CUT |
| UNIUSDT.P | Base | crypto_perp | WATCH |
| XMRUSDT.P | Base | crypto_perp | idiosyncratic → CUT |
| HYPEUSDT.P | Base | crypto_perp | must-cut → CUT |
| SOLUSDT.P | Base | crypto_perp | must-cut → CUT |
| ETHUSDT.P | Base | crypto_perp | WATCH (expectation FAIL) |
| LITUSDT.P | Base | crypto_perp | thin → CUT |
| ZECUSDT.P | Base | crypto_perp | idiosyncratic → CUT |
| XRPUSD | Base | crypto_perp | must-cut → CUT |
| SPXUSDT.P | Base | crypto_perp | meme SPX6900 ≠ SPX → CUT |
| XLMUSDT | Base | crypto_perp | thin beta → CUT |
| BNBUSD | Base | crypto_perp | venue context → WATCH |
| SPX | Base | macro | cash index → WATCH |
| NQ1! | Base | futures | risk beta → WATCH |
| QQQ | Base | etf | index beta → WATCH |
| CL1! | Base | futures | energy path → WATCH |
| CRCL | Base | equity | thin until filings → **CUT** |
| TSLA | Base | equity | high-duration → CUT |
| SPCX | Base | equity | thin vehicle → CUT |
| NVDA | Base | equity | **MAKE** |
| SAMSUNGUSDT.P | Base | crypto_perp | invalid KR equity proxy → CUT |
| BB | Base | equity | thin → CUT |
| GLXY | Base | equity | proxy cluster overcount → **CUT** |
| IBIT | Base | etf | BTC wrapper → WATCH |
| BMNR | Base | equity | thin → CUT |
| PURR | Base | crypto_perp | meme → CUT |
| MRNA | Base | equity | healthcare stub → CUT |
| BTC1! | Base | futures | BTC futures → **MAKE** (underlying BTC) |
| KOSDAQ | Base | macro | KR stub → WATCH |
| GOOG | Base | equity | WATCH |
| HOOD | Base | equity | thin → CUT |
| NOW | Base | equity | WATCH |
| CBRS | Base | equity | thin → CUT |
| MSTR | Base | equity | levered BTC double-count → CUT |
| STRC | Base | equity | thin → CUT |
| AMD | Base | equity | NVDA overlap → **CUT** |
| USDT.D | Base | macro | structure → WATCH |
| BTC.D | Base | macro | structure → WATCH |
| BTC/GOLD | Base | pair | **valid relative monitor** |
| BTC/SLV | Base | pair | **CUT** (redundant vs BTC/GOLD) |
| GOLD/BTC | Base | pair | invalid inverse → CUT |
| HYPE/BNB | Base | pair | invalid (HYPE must-cut) |
| HYPE/HOOD | Base | pair | invalid |
| LIT/HYPE | Base | pair | invalid |
| ETHBTC | Base | pair | invalid as active RV (corr≈0.89) |
| GOLD | Base | macro | metal context → WATCH (≠ GLD call) |
| SILVER | Base | macro | metal context → WATCH |
| COPPER1! | Base | futures | materials stub → WATCH |
| UXJ2026 | Base | futures | thin uranium → CUT |
| NG1! | Base | futures | energy vol → WATCH |
| DXY | Base | macro | WATCH |
| TOTAL | Base | macro | crypto mkt-cap → WATCH |
| OTHERSBTC | Base | macro | alt seasonality → WATCH |
| TOTAL2 | Base | macro | WATCH |
| STABLE.C | Base | macro | WATCH |
| TOTAL3 | Base | macro | WATCH |
| NEARUSDC.P | Base | crypto_perp | must-cut NEAR (dupe venue) → CUT |
| TNX | Base | macro | rates → WATCH |
| IWM | Base | etf | small-cap defer → CUT |
| VIX | Base | macro | risk → WATCH |

**Not on LIVE Base:** `CASHCATUSDC.P` (was on Research 12:26 Base extract only).

### 2.2 Racksor Capital — 6 (12:27:33 AEST SoT; Research 12:26:29)

| Symbol | List | Type | Disposition |
|---|---|---|---|
| IBIT | Racksor | etf | WATCH (also Base) |
| PURR | Racksor | crypto_perp | CUT meme (also Base) |
| SNDK | Racksor | equity | **CUT** memory-semi killed |
| MU | Racksor | equity | **CUT** memory-semi killed |
| SKHYNIXUSDC.P | Racksor | crypto_perp | **CUT** memory-semi killed |
| RBLX | Racksor | equity | CUT thin consumer/gaming |

### 2.3 Crypto — 15 (12:27:33 AEST SoT; Research 12:26:44)

| Symbol | List | Type | Disposition |
|---|---|---|---|
| BTCUSDC.P | Crypto | crypto_perp | **MAKE** (BTC) |
| ETHUSDC.P | Crypto | crypto_perp | WATCH |
| SOLUSDC.P | Crypto | crypto_perp | CUT must-cut |
| HYPEUSDC.P | Crypto | crypto_perp | CUT must-cut |
| VVVUSDC.P | Crypto | crypto_perp | CUT lottery |
| ZECUSDC.P | Crypto | crypto_perp | CUT idiosyncratic |
| XMRUSDC.P | Crypto | crypto_perp | CUT idiosyncratic |
| NEARUSDC.P | Crypto | crypto_perp | CUT must-cut |
| LITUSDC.P | Crypto | crypto_perp | CUT thin |
| **CASHCATUSDC.P** | **Crypto only** | crypto_perp | **CUT** meme (not on LIVE Base) |
| PONSUSDC.P | Crypto | crypto_perp | CUT lottery |
| XRPUSDC.P | Crypto | crypto_perp | CUT must-cut |
| SKRUSDC.P | Crypto | crypto_perp | CUT lottery |
| CHIPUSDC.P | Crypto | crypto_perp | CUT lottery |
| DOGEUSDC.P | Crypto | crypto_perp | CUT meme |

---

## 3. Sector / theme map — falsify “covers all sectors”

**Verdict: FAIL** (same conclusion as #25 / Skeptic #26 PASS on the FAIL claim).

### Covered themes (personal TV)

| Theme | Names present | Quality |
|---|---|---|
| Crypto majors / L1 beta | BTC, ETH, SOL*, BNB, XRP*, NEAR* | Deep but **must-cuts** pollute |
| Crypto venue / HL-native | HYPE*, PURR*, LIT* | Lottery / must-cut heavy |
| Privacy / idiosyncratic crypto | XMR, ZEC | Thin falsifiers |
| Meme / lottery crypto | DOGE, CASHCAT*, SPX6900, ASTER, VVV, PONS, SKR, CHIP | Noise (*CASHCAT via Crypto only on LIVE*) |
| AI / mega-cap tech | NVDA, AMD*, GOOG, NOW, QQQ, NQ | NVDA solid; AMD **CUT** |
| Crypto equity proxies | IBIT, MSTR*, GLXY*, CRCL* | IBIT WATCH; MSTR/GLXY/CRCL **CUT** |
| Memory semis (killed sleeve) | MU*, SNDK*, SKHYNIX* | **Racksor presence = hygiene fail — stay CUT** |
| Consumer / speculative equity | TSLA*, HOOD*, RBLX*, BB*, SPCX*, BMNR*, STRC*, CBRS* | Mostly CUT |
| Healthcare (stub) | MRNA* | Thin — not healthcare coverage |
| Energy / commodities | CL, NG, COPPER, GOLD, SILVER, UX* | Dashboard; **no XOM/XLE equity** |
| Rates / FX / vol / index | DXY, TNX, VIX, SPX, QQQ, IWM*, KOSDAQ | Context OK; IWM CUT |
| Crypto market structure | BTC.D, USDT.D, TOTAL/2/3, OTHERSBTC, STABLE.C | Dashboard only |

\* = **CUT**.

### Missing / thin (falsifies “all sectors”)

| Gap | Why it matters vs lab |
|---|---|
| **Financials equities** | **JPM / XLF absent** from TV despite yaml membership |
| **Energy equities** | **XOM absent**; only CL/NG futures |
| **Healthcare depth** | Only MRNA (CUT) |
| **Consumer staples** | None |
| **Utilities** | None |
| **REITs / real estate** | None |
| **Materials ex-copper** | Copper futures only |
| **International equities** | SAMSUNG crypto proxy ≠ KRX; SKHYNIX killed; KOSDAQ stub |
| **Broad US quality ex-tech** | No MSFT / META / AVGO on TV |
| **DeFi credit / DEX depth** | UNI WATCH; **AAVE absent** |
| **Semi basket** | **SMH absent** |

Personal TV is a **crypto + AI/tech + macro dashboard** with a Racksor memory-semi stub the lab already **killed**. List length ≠ research coverage.

---

## 4. ETF / proxy pairs

| Proxy | Maps to | Verdict | Why |
|---|---|---|---|
| **IBIT** | BTC TradFi spot ETF | **Valid WATCH** | Principal greenlit wrapper; not MAKE |
| **MSTR** | Levered corporate BTC | **CUT** | Double-counts BTC MAKE |
| **GLXY** | Crypto equity proxy | **CUT** | BTC MAKE + IBIT WATCH already cover cluster |
| **QQQ / NQ / SPX** | US risk / duration | **WATCH** context | Not in-universe membership |
| **IWM** | US small-cap | **CUT** | Higher-for-longer defer |
| **GOLD / SILVER** | Real-asset dashboard | **WATCH** metals; **BTC/SLV pair CUT** | Keep **BTC/GOLD** only as relative monitor; GLD *call* stays must-cut learning |
| **CL / NG** | Energy path | **WATCH** context for XOM gate family | Not XOM equity substitute |
| **SAMSUNGUSDT.P** | “Samsung” | **CUT** | ≠ KRX Samsung Electronics |
| **MU / SNDK / SKHYNIX** | Memory-semi | **CUT (killed)** | Do not rehabilitate |

---

## 5. Per distinct underlying — MAKE / WATCH / CUT

Board = Skeptic-final (#25 after #26 REVISE). Inventory citations = **LIVE 12:27:33 AEST**.

### 5.1 MAKE (2)

#### BTC — **MAKE**
Locked yaml `in_universe.crypto_perps` = **[BTC]** only (ETH demoted to watch_only). QUANT: last close **$76,201** (yfinance BTC-USD asof **2026-09-17**); RV20/RV60 **35.6% / 39.1%** √365; MDD~1y **−53.1%**; ret 1m/3m/YTD **+18.1% / +21.2% / −14.1%**. Expectations scorecard **PASS**. HL dayNtl/OI stale capture **2026-09-17T00:28:03Z** = appendix / DO NOT SIZE. LIVE TV: `BTCUSDC.P` (Crypto) + `BTC1!` (Base).

#### NVDA — **MAKE**
Locked yaml `in_universe.equities` includes NVDA. QUANT: last **213.90** asof **2026-09-16**; RV20/RV60 **45.5% / 40.4%** √252; MDD **−20.2%**; vs SPY 1m/3m/YTD **−2.4% / +2.5% / +2.6%** (simple-diff **NOT α**); ADV 5d ≈ **102.3M** sh / **$21.70B**. Corr NVDA–AVGO **0.462… ≈ 0.46** (`corr_matrix_60d.csv`, window 2026-05-28→2026-09-15) = co-movement, **not** multi-name license. AMD is **CUT**. LIVE TV: `NVDA` on Base.

### 5.2 WATCH (25)

ETH, UNI, BNB, IBIT, GOOG, NOW, QQQ, NQ, SPX, CL, NG, COPPER, GOLD, SILVER, DXY, TNX, VIX, KOSDAQ, BTC.D, USDT.D, TOTAL, TOTAL2, TOTAL3, OTHERSBTC, STABLE.C.

| Name | Why WATCH (not MAKE) |
|---|---|
| **ETH** | Yaml `watch_only` after #23; corr ETH–BTC **0.888… ≈ 0.89**; raw rel **NOT α**; appendix §1 |
| **UNI** | Yaml watch_only; undated governance FAIL; conf ceiling **0.20**; appendix §4 |
| **IBIT** | Greenlit BTC wrapper; not yaml membership → not MAKE |
| **GOOG / NOW** | Liquid monitors; not in locked yaml; no promotion |
| **BNB** | Venue/CEX context only |
| **QQQ / NQ / SPX / DXY / TNX / VIX / KOSDAQ** | Dashboards |
| **CL / NG / COPPER / GOLD / SILVER** | Commodity path context; GLD call stays must-cut learning |
| **BTC.D … STABLE.C** | Crypto structure — never in-universe membership / never a Quant verdict |

### 5.3 CUT (36)

**Must-cuts:** HYPE, SOL, XRP, NEAR.

**Memory-semi killed:** MU, SNDK, SKHYNIX.

**Meme / lottery:** DOGE, **CASHCAT** (Crypto-only on LIVE), PURR, SPX6900, ASTER, VVV, PONS, SKR, CHIP.

**Idiosyncratic / thin crypto:** XMR, ZEC, LIT, XLM, SAMSUNG.

**Thin / speculative equities:** TSLA, HOOD, MRNA, BB, BMNR, MSTR, STRC, SPCX, CBRS, RBLX.

**Skeptic REVISE (WATCH→CUT):**
- **AMD** — NVDA AI overlap; no residual
- **CRCL** — thin until filings
- **GLXY** — BTC MAKE + IBIT WATCH already cover proxy cluster

**Deferred / thin:** IWM, UX.

---

## 6. Pair invalidations (summary → appendix)

Full QUANT method: `research/queue/INVALIDATION-20260917-fail-pairs-quant.md` (main).

| Pair / expression | Verdict | Key QUANT cite |
|---|---|---|
| **ETH/BTC** | Invalid as active RV / outperf | Corr **≈0.89**; raw rel ≠ α; conf ceiling **0.28** |
| **JPM/XLF** | Invalid diversifier / double-count | Corr **≈0.73**; names **absent from TV**; ceilings **0.36 / 0.24** |
| **NVDA–AVGO–SMH** | Triple-count / basket-outperform invalid | NVDA–AVGO corr **≈0.46**; SMH absent from TV; ceiling **0.22** |
| **UNI** | Undated governance optionality | Conf **0.20**; bounce ≠ thesis |
| **AAVE** | Rate→credit killed; util baseline unavailable | Conf **0.18**; **absent from TV** |
| **BTC/GOLD** | **Valid relative monitor** (not a trade) | Macro dashboard only |
| **BTC/SLV** | **CUT** | Redundant vs BTC/GOLD |
| **GOLD/BTC** | Invalid inverse | Drop; keep BTC/GOLD |
| **HYPE/BNB, HYPE/HOOD, LIT/HYPE** | Invalid | Must-cut / lottery cluster |

**Corr source (no invented numbers):** `research/queue/quant-20260917/corr_matrix_60d.csv` · window **2026-05-28 → 2026-09-15** · n=60 · pre-FOMC · corr ≠ causation.

| Pair | CSV value | Rounded |
|---|---:|---:|
| ETH–BTC | 0.888417508385592 | ≈0.89 |
| JPM–XLF | 0.7282170140875045 | ≈0.73 |
| NVDA–AVGO | 0.46248682909061356 | ≈0.46 |
| XOM–NVDA | −0.25210414388825503 | ≈−0.25 |
| XOM–BTC | −0.11844433326789214 | ≈−0.12 |

---

## 7. Contrast vs locked `config/universe.yaml` (main)

Fetched **main** lock version `2026-09-17`, status `locked`:

| Tier | Yaml membership | On LIVE TV? | Personal disposition |
|---|---|---|---|
| **in_universe crypto** | **BTC** | Yes | **MAKE** |
| **in_universe equity** | NVDA, AVGO, MSFT, META, JPM, XOM | **Only NVDA** | NVDA **MAKE** · others **absent** |
| **watch_only crypto** | ETH, UNI, AAVE | ETH+UNI yes · **AAVE no** | ETH/UNI **WATCH** |
| **watch_only equity** | SMH, XLF | **No** | n/a on TV |
| **deferred_must_cut crypto** | HYPE, SOL, XRP, ARB, NEAR, LINK | HYPE SOL XRP NEAR yes | present → **CUT** |
| **deferred_must_cut equity** | GLD, LLY | No (GOLD metal ≠ GLD) | GOLD WATCH context only |
| **IBIT** | Sidebar only | Yes | **WATCH** |
| **Memory-semi** | **Killed** | MU SNDK SKHYNIX on Racksor | **CUT** |

**Lock gaps still missing from TV:** **AVGO, MSFT, META, JPM, XLF, XOM, AAVE, SMH**. Personal LIVE TV cannot underwrite those sleeves; lab QUANT/cards remain source of record.

---

## 8. QUANT honesty rules (bind)

- Windows / as-of always labeled.
- HL stale = appendix only / **DO NOT SIZE**.
- Rel = simple-diff **NOT α**.
- √365 ≠ √252 (crypto vs equity panels).
- **Corr ≠ causation**; no allocation from pre-FOMC corr.
- Post-selection YTD not lock justification.
- **No invented numbers** — gaps → unavailable.
- **No Telegram.** **No trades.** **No sizing.** No `live.yaml` / `universe.yaml` edits from this pack.
- Memory-semi (**MU / SNDK / SKHYNIX**) stays **killed** — Racksor presence is hygiene fail, not revival.
- Must-cuts stay learning records.

---

## 9. Disposition tallies

| Bucket | Count | Names (short) |
|---|---:|---|
| **MAKE** | **2** | BTC, NVDA |
| **WATCH** | **25** | ETH, UNI, BNB, IBIT, GOOG, NOW, QQQ, NQ, SPX, CL, NG, COPPER, GOLD, SILVER, DXY, TNX, VIX, KOSDAQ, BTC.D, USDT.D, TOTAL, TOTAL2, TOTAL3, OTHERSBTC, STABLE.C |
| **CUT** | **36** | must-cuts HYPE SOL XRP NEAR · killed MU SNDK SKHYNIX · memes/lottery (incl. CASHCAT via Crypto) · thin crypto/equities · Skeptic AMD CRCL GLXY · IWM · UX |
| **Pairs** | 7 | 1 valid monitor (BTC/GOLD) · 6 invalid/CUT |
| **Distinct underlyings** | **63** | (normalize/dedupe; CASHCAT still counted via Crypto) |
| **LIVE unique raw symbols** | **80** | Intel SoT |
| **LIVE Base rendered** | **62** | UI label 63 — no 63rd invented |

MAKE 2 + WATCH 25 + CUT 36 = **63**.

**Sector-coverage verdict:** **FAIL**.

---

## 10. Repo staging paths (for PR)

Copy into `research/queue/watchlist-live/`:

| Local (box) | Repo target |
|---|---|
| `research/queue/watchlist-live/WATCHLIST-DD-20260917-personal-LIVE.md` | `research/queue/WATCHLIST-DD-20260917-personal-LIVE.md` |
| `research/queue/watchlist-live/watchlist-live/20260917-tv-live-symbol-list.json` | `research/queue/watchlist-live/20260917-tv-live-symbol-list.json` |
| `research/queue/watchlist-live/watchlist-live/20260917-tv-live-symbol-list.csv` | `research/queue/watchlist-live/20260917-tv-live-symbol-list.csv` |
| `research/queue/watchlist-live/watchlist-live/20260917-live-inventory.json` | `research/queue/watchlist-live/20260917-live-inventory.json` (Research secondary scrape; Base overcount noted) |

Intel dumps (optional audit): `research/queue/watchlist-live/tv-live/`.

---

## 11. Explicit non-actions

- No Telegram. No trades. No sizing. No `live.yaml` edits.
- No memory-semi reopen. No must-cut reopen.
- No invented QUANT numbers; no invented 63rd Base symbol.
- HL stale capture not primary.
- This pack does **not** modify `universe.yaml`; it grades Principal’s personal TV against it with **LIVE** inventory provenance.
- Does **not** silently replace Skeptic board — board aligns with #25/#26 after reclass; **inventory SoT is LIVE**.

**Signed:** Personal WATCHLIST-DD **LIVE** · Principal/Don queue · 2026-09-17 AEST · Intel SoT **12:27:33 AEST** · private · **not a trade**

**Appendix:** `research/queue/INVALIDATION-20260917-fail-pairs-quant.md`
