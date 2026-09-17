# WATCHLIST-DD-20260917 — Principal personal TV due-diligence pack

| Field | Value |
|---|---|
| **Date** | 2026-09-17 (Australia/Sydney, **AEST**) |
| **Repo** | `ElChopa11/market-memory` (private research) |
| **Ask** | Principal personal TradingView inventory → MAKE / WATCH / CUT due-diligence vs locked lab universe + QUANT honesty |
| **Privacy** | **Private research only.** **No Telegram.** **No trades.** |
| **TV lists** | Base `194324969` · Racksor Capital `343370615` · Crypto HL `330128831` |
| **Lab lock** | `config/universe.yaml` **main** · version `2026-09-17` · status `locked` |
| **QUANT** | `research/queue/quant-20260917/` (PR **#19**) · scorecard PR **#22** · FAIL patch PR **#23** |
| **Appendix** | `research/queue/INVALIDATION-20260917-fail-pairs-quant.md` (demoted FAIL pairs) |
| **Skeptic** | Cut-review **REVISE** (PR **#26**, `research/queue/WATCHLIST-DD-20260917-personal-skeptic.md`): AMD, CRCL, GLXY WATCH→CUT; BTC/SLV pair **CUT**. Board **MAKE 2 / WATCH 25 / CUT 36**. MAKE BTC/NVDA **unchanged**. Memory-semi stays killed. |
| **Hard rules** | rel≠α · HL stale not primary · corr≠causation · memory-semi **killed** · must-cuts = learning · prefer rejection |

**What MAKE/WATCH/CUT means here:** research-queue disposition for the **personal TV inventory**, not orders.
- **MAKE** = liquid, falsifiable **lab `active_call` candidate** (keep or propose into thesis priority).
- **WATCH** = monitor / context / demoted expectation / proxy — **no** active-call priority.
- **CUT** = reject-learn (lottery, meme, must-cut archive, killed sleeve, thin narrative, double-count).

---

## 0. TLDR (5 lines)

1. **Distinct underlyings: 63** after normalize/dedupe (84 raw TV rows → 63 names + **7 pairs** treated separately).
2. **MAKE 2 · WATCH 25 · CUT 36** (underlyings only; Skeptic cut-review REVISE). Pair verdicts: **1 valid monitor / 6 invalid or double-count** (BTC/SLV **CUT** as redundant vs BTC/GOLD).
3. **Sector coverage claim FAILS:** personal TV is crypto-beta + AI/tech + macro dashboard heavy; **missing** staples, utilities, REITs, materials (ex-copper), healthcare depth (ex-MRNA thin), international breadth (ex-Samsung/Hynix crypto-proxy / KOSDAQ stub), banks/energy majors (JPM/XOM absent from TV).
4. **Lab contrast:** yaml still lists **active_calls** BTC ETH + NVDA AVGO MSFT META JPM XLF XOM; personal TV only overlaps **BTC ETH NVDA UNI** (+ IBIT sidebar). AVGO/MSFT/META/JPM/XLF/XOM/AAVE/SMH **absent** from TV.
5. **Rejection bias holds:** must-cuts (HYPE SOL XRP NEAR) + memory-semi (MU SNDK SKHYNIX) + memes (DOGE PURR CASHCAT SPX6900 …) + Skeptic cuts (AMD CRCL GLXY) = **CUT**; ETH/JPM/XLF-style FAIL expressions → see appendix (not MAKE). MAKE BTC/NVDA **unchanged**.

---

## 1. Inventory — distinct underlyings (normalized)

**Normalization rules:** strip `.P` / `USDT` / `USDC` / `USD`; `BTC1!`→`BTC`; `NQ1!`→`NQ`; `CL1!`→`CL`; `COPPER1!`→`COPPER`; `NG1!`→`NG`; `UXJ2026`→`UX`; `SKHYNIXUSDC.P`→`SKHYNIX`; `SAMSUNGUSDT.P`→`SAMSUNG` (crypto-listed proxy, not KRX Samsung Electronics); `SPXUSDT.P`→`SPX6900` (meme) **≠** cash `SPX` index; `ETHBTC`→pair `ETH/BTC`. Cross-list dupes collapsed (e.g. `NEARUSDT.P` + `NEARUSDC.P` + Base `NEARUSDC.P` → **NEAR**).

### 1.1 Crypto (22)

| Underlying | TV sources | Raw examples | Disposition |
|---|---|---|---|
| BTC | CryptoHL (+ Base `BTC1!`) | BTCUSDC.P, BTC1! | **MAKE** |
| ETH | Base, CryptoHL | ETHUSDT.P, ETHUSDC.P | **WATCH** |
| SOL | Base, CryptoHL | SOLUSDT.P, SOLUSDC.P | **CUT** (must-cut) |
| HYPE | Base, CryptoHL | HYPEUSDT.P, HYPEUSDC.P | **CUT** (must-cut) |
| XRP | Base, CryptoHL | XRPUSD, XRPUSDC.P | **CUT** (must-cut) |
| NEAR | Base, CryptoHL | NEARUSDT.P, NEARUSDC.P | **CUT** (must-cut) |
| UNI | Base | UNIUSDT.P | **WATCH** |
| DOGE | Base, CryptoHL | DOGEUSDT, DOGEUSDC.P | **CUT** (meme/lottery) |
| XMR | Base, CryptoHL | XMRUSDT.P, XMRUSDC.P | **CUT** (idiosyncratic) |
| ZEC | Base, CryptoHL | ZECUSDT.P, ZECUSDC.P | **CUT** (idiosyncratic) |
| LIT | Base, CryptoHL | LITUSDT.P, LITUSDC.P | **CUT** (thin) |
| XLM | Base | XLMUSDT | **CUT** (thin beta) |
| BNB | Base | BNBUSD | **WATCH** (venue/context only) |
| ASTER | Base | ASTERUSDT.P | **CUT** (lottery) |
| VVV | CryptoHL | VVVUSDC.P | **CUT** (lottery) |
| PONS | CryptoHL | PONSUSDC.P | **CUT** (lottery) |
| SKR | CryptoHL | SKRUSDC.P | **CUT** (lottery) |
| CHIP | CryptoHL | CHIPUSDC.P | **CUT** (lottery) |
| CASHCAT | Base, CryptoHL | CASHCATUSDC.P | **CUT** (meme) |
| PURR | Base, Racksor | PURR | **CUT** (meme) |
| SAMSUNG | Base | SAMSUNGUSDT.P | **CUT** (thin crypto proxy ≠ KR equity) |
| SPX6900 | Base | SPXUSDT.P | **CUT** (meme; ≠ SPX index) |

### 1.2 Equities / equity ETFs (22)

| Underlying | TV sources | Disposition |
|---|---|---|
| NVDA | Base | **MAKE** |
| GOOG | Base | **WATCH** |
| AMD | Base | **CUT** (NVDA AI overlap; no residual) |
| TSLA | Base | **CUT** (high-duration / lottery-relative under hawkish) |
| HOOD | Base | **CUT** (thin narrative) |
| NOW | Base | **WATCH** (software quality; thin vs MSFT gate) |
| MRNA | Base | **CUT** (single-name healthcare stub) |
| BB | Base | **CUT** (thin) |
| GLXY | Base | **CUT** (BTC MAKE + IBIT WATCH already cover proxy cluster) |
| IBIT | Base, Racksor | **WATCH** (Principal greenlit BTC wrapper) |
| BMNR | Base | **CUT** (thin / unclear thesis) |
| MSTR | Base | **CUT** (levered BTC double-count) |
| STRC | Base | **CUT** (thin) |
| CRCL | Base | **CUT** (thin until filings) |
| SPCX | Base | **CUT** (thin / speculative vehicle) |
| CBRS | Base | **CUT** (thin / ambiguous) |
| MU | Racksor | **CUT** (memory-semi **killed**) |
| SNDK | Racksor | **CUT** (memory-semi **killed**) |
| SKHYNIX | Racksor | **CUT** (memory-semi **killed**) |
| RBLX | Racksor | **CUT** (thin consumer/gaming) |
| QQQ | Base | **WATCH** (index beta context; not active call) |
| IWM | Base | **CUT** (small-cap hurt by higher-for-longer; deferred in shortlist) |

### 1.3 Futures / rates / vol / metals / crypto-macro (19)

| Underlying | Raw | Disposition |
|---|---|---|
| NQ | NQ1! | **WATCH** (risk beta dashboard) |
| CL | CL1! | **WATCH** (energy path context for XOM gate family) |
| COPPER | COPPER1! | **WATCH** (materials stub — only materials print on TV) |
| NG | NG1! | **WATCH** (energy vol context) |
| UX | UXJ2026 | **CUT** (thin uranium narrative) |
| SPX | SPX (cash) | **WATCH** (benchmark context) |
| DXY | DXY | **WATCH** (macro) |
| TNX | TNX | **WATCH** (rates / higher-for-longer context) |
| VIX | VIX | **WATCH** (risk dashboard) |
| KOSDAQ | KOSDAQ | **WATCH** (KR risk stub; not a name call) |
| GOLD | GOLD | **WATCH** (must-cut **GLD** learning applies to gold-ETF *call*; raw metal = context only) |
| SILVER | SILVER | **WATCH** (metals context) |
| BTC.D | BTC.D | **WATCH** (crypto structure) |
| USDT.D | USDT.D | **WATCH** (stablecoin share / risk-off proxy) |
| TOTAL | TOTAL | **WATCH** (crypto mkt-cap context) |
| TOTAL2 | TOTAL2 | **WATCH** |
| TOTAL3 | TOTAL3 | **WATCH** |
| OTHERSBTC | OTHERSBTC | **WATCH** (alt seasonality context — not a call) |
| STABLE.C | STABLE.C | **WATCH** |

**Count check:** 22 + 22 + 19 = **63** distinct underlyings.

### 1.4 Pairs (7) — not underlyings

See §5.

---

## 2. Sector / theme map — falsify “covers all sectors”

### Covered themes (personal TV)

| Theme | Names present | Quality |
|---|---|---|
| Crypto majors / L1 beta | BTC, ETH, SOL*, BNB, XRP*, NEAR* | Deep but **must-cuts** pollute |
| Crypto venue / HL-native | HYPE*, PURR*, LIT* | Lottery / must-cut heavy |
| Privacy / idiosyncratic crypto | XMR, ZEC | Thin falsifiers |
| Meme / lottery crypto | DOGE, CASHCAT, SPX6900, ASTER, VVV, PONS, SKR, CHIP | Noise |
| AI / mega-cap tech | NVDA, AMD*, GOOG, NOW, QQQ, NQ | NVDA solid; AMD **CUT** (no residual vs NVDA); others overlap or thin |
| Crypto equity proxies | IBIT, MSTR*, GLXY*, CRCL* | IBIT = valid watch wrapper; MSTR/GLXY/CRCL **CUT** (double-count / thin / cluster already covered) |
| Memory semis (killed sleeve) | MU*, SNDK*, SKHYNIX* | **Present on Racksor — must stay CUT** |
| Consumer / speculative equity | TSLA*, HOOD*, RBLX*, BB*, SPCX*, BMNR*, STRC*, CBRS* | Mostly CUT |
| Healthcare (stub) | MRNA* | **Thin — does not constitute healthcare coverage** |
| Energy / commodities | CL, NG, COPPER, GOLD, SILVER, UX* | Dashboard-grade; **no XOM/XLE equity** |
| Rates / FX / vol / index | DXY, TNX, VIX, SPX, QQQ, IWM*, KOSDAQ | Context OK; IWM CUT |
| Crypto market structure | BTC.D, USDT.D, TOTAL/2/3, OTHERSBTC, STABLE.C | Dashboard only |

\* = **CUT** disposition in this pack.

### Missing / thin (falsifies “all sectors”)

| Gap | Why it matters vs lab |
|---|---|
| **Financials equities** | **JPM / XLF absent** from personal TV despite yaml active_calls |
| **Energy equities** | **XOM absent**; only CL/NG futures |
| **Healthcare depth** | Only **MRNA** (CUT) — no LLY (must-cut learning) / no diversified health ETF |
| **Consumer staples** | None |
| **Utilities** | None |
| **REITs / real estate** | None |
| **Materials ex-copper** | No miners / no XLB; copper futures only |
| **International equities** | No ADRs of substance; **SAMSUNG** is crypto proxy ≠ Samsung Electronics; **SKHYNIX** killed; KOSDAQ index stub ≠ name research |
| **Broad US quality ex-tech** | No MSFT / META / AVGO on TV (all yaml active) |
| **DeFi credit / DEX depth** | UNI present (WATCH); **AAVE absent** |
| **Semi basket** | **SMH absent** (watch-only in yaml) |

**Verdict:** Personal TV does **not** cover all sectors. It is a **crypto + AI/tech + macro dashboard** with a Racksor memory-semi stub that lab already **killed**. Do not treat list breadth as research coverage.

---

## 3. ETF / proxy pairs (explicit)

| Proxy | Maps to | Verdict | Why |
|---|---|---|---|
| **IBIT** | BTC (TradFi spot ETF wrapper) | **Valid WATCH proxy** | Principal greenlit watch-only; not a perp substitute; membership ≠ active call. Config historically “greenlit then ignored” — keep **WATCH**, not MAKE. |
| **MSTR** | Levered corporate BTC beta | **Invalid as separate sleeve** | Double-counts BTC active thesis; CUT. |
| **GLXY** | Crypto equity / trading proxy | **CUT** | BTC **MAKE** + IBIT **WATCH** already cover the proxy cluster; not a separate sleeve. |
| **QQQ / NQ / SPX** | US risk / duration beta | **Valid macro context** | Shortlist deferred index-beta as *calls*; keep WATCH dashboards only. |
| **IWM** | US small-cap | **CUT** | Higher-for-longer hurt; deferred in UNIVERSE shortlist. |
| **GOLD / SILVER (+ BTC/GOLD, BTC/SLV)** | Real-asset / crypto-relative | Metals **WATCH**; **BTC/SLV pair CUT** (redundant vs BTC/GOLD); gold *call* learning = must-cut **GLD** | Metals OK as dashboard; do not revive GLD active expectation. BTC/SLV does not add a second relative sleeve. |
| **CL / NG** | Energy path | **Valid context for XOM gate family** | QUANT XOM PASS is crude-gated — futures help falsify; **not** a substitute for XOM equity membership. |
| **SAMSUNGUSDT.P** | “Samsung” | **Invalid equity proxy** | Crypto-listed symbol ≠ KRX Samsung Electronics research. CUT. |
| **SKHYNIXUSDC.P** | SK hynix | **CUT (killed sleeve)** | Memory-semi intent killed; do not rehabilitate via HL-USDC listing. |
| **MU / SNDK** | Memory-semi | **CUT (killed)** | Same. |

---

## 4. Per-name DD (MAKE / WATCH / CUT)

### 4.1 MAKE (2) — lab active_call candidates

#### BTC — **MAKE**
Locked yaml `active_calls.crypto_perps` includes BTC. QUANT pack: last close **$76,201** (yfinance BTC-USD asof **2026-09-17**); RV20/RV60 **35.6% / 39.1%** √365; MDD~1y **−53.1%**; ret 1m/3m/YTD **+18.1% / +21.2% / −14.1%**. Expectations scorecard **PASS** (benchmark/range + empty cycle gates until ETF + fresh fundingHistory). HL dayNtl/OI from lab capture **2026-09-17T00:28:03Z** are **stale/partial** (live 429) — appendix only / DO NOT SIZE. Personal TV correctly carries BTC via HL USDC perp + `BTC1!`. **MAKE** = keep as sole crypto active-call priority on this inventory.

#### NVDA — **MAKE**
Locked yaml `active_calls.equities` includes NVDA. QUANT: last **213.90** asof **2026-09-16**; RV20/RV60 **45.5% / 40.4%** √252; MDD **−20.2%**; vs SPY 1m/3m/YTD **−2.4% / +2.5% / +2.6%** (simple-diff **NOT α**); ADV 5d ≈ **102.3M** sh / **$21.70B**. Scorecard **PASS** (crowded honesty + mispricing gate empty). Corr NVDA–AVGO **0.46** (60d, 2026-05-28→2026-09-15) = co-movement description, not a multi-name license. **MAKE** as AI-infra primary; do not auto-MAKE AMD/SMH/memory from this. AMD is **CUT** (no independent residual vs NVDA).

### 4.2 WATCH (25) — monitors / demotions / context

#### ETH — **WATCH** (yaml still `active_calls`; expectation **FAIL** → personal disposition WATCH)
Yaml membership kept active; PR **#23** demotes *expectation* to BTC-beta watch (conf ceiling **0.28**). QUANT: corr ETH–BTC **0.888… ≈ 0.89**; raw ETH−BTC 30d/90d/YTD **+8.2% / +20.1% / −5.4%** = **NOT α**; RV20/60 **41.7% / 58.9%** √365. Without named β residual + L2/ETF gates, personal pack treats ETH as **WATCH**, not MAKE. Detail: appendix §1.

#### UNI — **WATCH**
Yaml `watch_only`. Scorecard **FAIL** (undated governance). QUANT: RV20/60 **116.3% / 98.2%**; bounce 30d/90d **+103.8% / +117.3%** from ~$3.20 (2026-08-14) — footnote not thesis. Conf ceiling **0.20**. Appendix §4.

#### IBIT — **WATCH**
Principal greenlit BTC equity-wrapper; not in `universe.yaml` membership lists as of main lock (sidebar only). Valid TradFi proxy to watch flows beside BTC — **not** MAKE until yaml + expectation card exist.

#### GOOG — **WATCH**
Liquid mega-cap quality; **not** in locked yaml. Lower cycle specificity than MSFT/META (also absent from TV). Monitor only; no promotion without earnings-gate pack.

#### NOW — **WATCH**
Software quality name; thin vs locked MSFT Azure gate. No QUANT row. Monitor.

#### BNB — **WATCH**
Venue/CEX context vs HL-native research; not a lab active. Useful for HYPE/BNB pair context only.

#### QQQ, NQ, SPX — **WATCH**
Index/risk dashboards. Shortlist explicitly deferred SPY/QQQ as calls.

#### CL, NG, COPPER, GOLD, SILVER — **WATCH**
Commodity path context (esp. CL for XOM crude gate family). Not equity substitutes. GLD *call* remains must-cut learning — do not revive via GOLD metal. **BTC/SLV pair is CUT** (redundant vs BTC/GOLD); SILVER metal stays dashboard WATCH only.

#### DXY, TNX, VIX, KOSDAQ — **WATCH**
Macro / regional risk dashboards only.

#### BTC.D, USDT.D, TOTAL, TOTAL2, TOTAL3, OTHERSBTC, STABLE.C — **WATCH**
Crypto market-structure dashboards; never active calls.

### 4.3 CUT (36) — reject-learn

**Must-cuts (learning; do not reopen as MAKE):** HYPE, SOL, XRP, NEAR. (ARB, LINK, GLD, LLY are lab must-cuts **not** on this TV — noted for contrast only.)

**Memory-semi killed:** MU, SNDK, SKHYNIX. Intent may have been greenlit then **killed** — Racksor presence is a hygiene fail; disposition **CUT**.

**Meme / lottery crypto:** DOGE, CASHCAT, PURR, SPX6900, ASTER, VVV, PONS, SKR, CHIP.

**Idiosyncratic / thin crypto:** XMR, ZEC, LIT, XLM, SAMSUNG (invalid KR equity proxy).

**Thin / speculative equities:** TSLA, HOOD, MRNA, BB, BMNR, MSTR, STRC, SPCX, CBRS, RBLX.

**Skeptic cut-review REVISE (WATCH → CUT):**
- **AMD** — NVDA AI overlap; no independent residual vs NVDA primary. Not a second AI-infra call.
- **CRCL** — thin until primary filings and flow prints; issuer narrative is not a watch sleeve.
- **GLXY** — BTC **MAKE** + IBIT **WATCH** already cover the crypto-equity proxy cluster; extra name is double-count.

**Deferred / regime-hurt:** IWM.

**Thin commodity narrative:** UX (UXJ2026).

---

## 5. Pair-level verdicts

| Pair | Verdict | Why |
|---|---|---|
| **ETH/BTC** | **Invalid as active RV / outperf expression** | Corr ≈ **0.89**; raw rel ≠ α; no β residual protocol. Appendix §1. May exist as **chart hygiene** only → research label **WATCH structure**, not a call. |
| **BTC/GOLD** | **Valid relative monitor** (not a trade pair) | Macro regime dashboard (crypto vs real asset). Not α. |
| **GOLD/BTC** | **Invalid double-count** | Exact inverse of BTC/GOLD — drop one. Keep BTC/GOLD only. |
| **BTC/SLV** | **CUT** (redundant vs BTC/GOLD) | Silver vs BTC adds no independent relative sleeve; metals already WATCH as dashboard. |
| **HYPE/BNB** | **Invalid** | HYPE is must-cut; pair cannot rehabilitate. |
| **HYPE/HOOD** | **Invalid** | Cross-asset vibe pair; HYPE must-cut + HOOD thin. |
| **LIT/HYPE** | **Invalid** | Both thin/must-cut cluster; double lottery. |

**Pair score:** valid monitor **1** (BTC/GOLD) · invalid/double-count/redundant **6** (includes BTC/SLV **CUT**).

---

## 6. Contrast vs locked `config/universe.yaml` (main)

Fetched **main** `config/universe.yaml` (version `2026-09-17`, status `locked`):

| Tier | Yaml membership | On personal TV? | Personal disposition |
|---|---|---|---|
| **active_calls crypto** | BTC, ETH | Yes | BTC **MAKE** · ETH **WATCH** (expectation FAIL / #23 demotion) |
| **active_calls equity** | NVDA, AVGO, MSFT, META, JPM, XLF, XOM | **Only NVDA** | NVDA **MAKE** · others **absent from TV** (lab still active — do not invent TV rows) |
| **watch_only crypto** | UNI, AAVE | UNI yes · **AAVE no** | UNI **WATCH** |
| **watch_only equity** | SMH | **No** | n/a on TV |
| **deferred_must_cut crypto** | HYPE, SOL, XRP, ARB, NEAR, LINK | HYPE SOL XRP NEAR yes · ARB/LINK no | present ones **CUT** |
| **deferred_must_cut equity** | GLD, LLY | **No** (GOLD metal ≠ GLD ETF call) | GOLD stays WATCH context only |
| **IBIT** | Not in yaml lists (sidebar greenlight) | Yes | **WATCH** |
| **Memory-semi** | **Killed** (not in yaml) | MU SNDK SKHYNIX on Racksor | **CUT** |

**PR #15-era note:** Active-call set matches current yaml intent (BTC ETH + NVDA AVGO MSFT META JPM XLF XOM). ETH/XLF demotion is **expectation-level** (scorecard #22 / patch #23), **not** a yaml membership delete as of this fetch — personal pack respects yaml membership but **does not MAKE** FAIL expressions.

**Absent-from-TV lab actives (gap list):** AVGO, MSFT, META, JPM, XLF, XOM, AAVE, SMH. Personal TV cannot underwrite those sleeves; lab QUANT/cards remain source of record.

### QUANT cites used (no invented numbers)

| Item | Value | Source |
|---|---|---|
| ETH–BTC corr | **0.888… ≈ 0.89** | `corr_matrix_60d.csv` · window 2026-05-28→2026-09-15 · n=60 |
| JPM–XLF corr | **0.728… ≈ 0.73** | same (appendix; names not on TV) |
| NVDA–AVGO corr | **0.462… ≈ 0.46** | same |
| XOM–NVDA / XOM–BTC | **−0.25** / **−0.12** | same (PASS contrast) |
| Run as-of | **2026-09-17T11:15:47.495030+10:00** | `run_meta.json` |

---

## 7. Disposition tallies

| Bucket | Count | Names (short) |
|---|---:|---|
| **MAKE** | **2** | BTC, NVDA |
| **WATCH** | **25** | ETH, UNI, BNB, IBIT, GOOG, NOW, QQQ, NQ, SPX, CL, NG, COPPER, GOLD, SILVER, DXY, TNX, VIX, KOSDAQ, BTC.D, USDT.D, TOTAL, TOTAL2, TOTAL3, OTHERSBTC, STABLE.C |
| **CUT** | **36** | must-cuts HYPE SOL XRP NEAR · killed MU SNDK SKHYNIX · memes/lottery · thin crypto/equities · Skeptic REVISE AMD CRCL GLXY · IWM · UX |
| **Pairs** | 7 | 1 valid monitor · 6 invalid/double-count (BTC/SLV **CUT**) |
| **Distinct underlyings** | **63** | |

Exact lists in §1 disposition columns (MAKE 2 + WATCH 25 + CUT 36 = 63).

**Sector-coverage verdict:** **FAIL** — not all-sector; crypto/AI/macro-heavy with critical lab equities missing and killed sleeves still polluting Racksor.

---

## 8. Explicit non-actions

- No Telegram. No trades. No sizing. No `live.yaml` edits.
- No memory-semi reopen. No must-cut reopen.
- No invented QUANT numbers; gaps labeled unavailable elsewhere.
- HL stale capture not primary.
- This pack does **not** modify `universe.yaml`; it grades Principal’s personal TV against it.

**Signed:** Personal WATCHLIST-DD · Principal/Don queue · 2026-09-17 AEST · private · **not a trade**

**Appendix:** `research/queue/INVALIDATION-20260917-fail-pairs-quant.md`
