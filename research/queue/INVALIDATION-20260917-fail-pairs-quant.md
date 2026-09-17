# INVALIDATION-20260917 — QUANT fail pairs / expressions (not valid as active calls)

| Field | Value |
|---|---|
| **Date** | 2026-09-17 (Australia/Sydney, AEST) |
| **Ask** | Principal / Don: QUANT **invalidation** analysis — why listed expectations are **not** valid as active calls / pair expressions |
| **Status** | `method invalidation analysis` |
| **Privacy** | **Private repo only** (`ElChopa11/market-memory`). **No Telegram.** **No trades.** |
| **Out of scope** | Memory-semi / MU / SNDK / SK Hynix (**Principal killed** — not reopened). Allocation, sizing, `live.yaml`, thesis folders. |
| **What this is** | Methodology + QUANT read of **why** FAIL expressions fail as calls / pairs. **Not** a trade. **Not** Telegram copy. Prefer rejection honesty. |
| **What PASS/FAIL means here** | Validity of the **stated expectation / pair expression** under QUANT honesty — not realized P&L. |

**QUANT honesty rules applied (bind):** windows/as-of · HL stale = appendix only / DO NOT SIZE · rel = simple-diff **NOT α** · √365 ≠ √252 · **corr ≠ causation** · no allocation from pre-FOMC corr · post-selection YTD not lock justification · no invented numbers (gap → `unavailable`).

### Sources (real numbers only)

| Artifact | Where | Notes |
|---|---|---|
| `research/queue/QUANT-20260917-active-calls.md` + `research/queue/quant-20260917/*.csv` | **main** (PR #19 merged) | Run of record `as_of_knowledge` **2026-09-17T11:15:47.495030+10:00**. |
| `research/queue/EXPECTATIONS-20260917-methodology-scorecard.md` | **main** (PR #22 merged) | Board **3 PASS / 6 FAIL / 4 INCONCLUSIVE**. |
| `research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md` + patched `UNIVERSE-20260917-call-cards.md` | **main** (PR #23 merged) | FAIL → demote/empty map; conf haircuts. |
| Local CSVs | `research/queue/quant-20260917/` | Same pack numbers as main. |

**Corr window (QUANT):** 60 aligned-panel daily returns, **2026-05-28 → 2026-09-15**, **pre-FOMC**, `n_obs=60`, point estimate only (no CI/HAC). Source: `corr_matrix_60d.csv`.

**Conf ceiling** below = max conf one may assign to treating the **pre-patch / residual pair expression** as a research-grade active call. Post-patch demoted labels (BTC-beta watch, etc.) are acknowledged but **do not rehabilitate** the invalidated expression.

---

## 1. ETH vs BTC — outperf / residual protocol

### Stated expectation
Call-cards (pre-#23): conditional **RV vs BTC**; cycle IF = **ETH/BTC outperformance** if ETF + L2 gates clear. Scorecard #22: **FAIL**. Patch #23: demoted to **BTC-beta watch**; α banned; residual empty until protocol defined; conf **0.40 → 0.28**.

### Why invalid (quant/method)
1. **No named β window + no L2 residual.** Outperformance-vs-BTC without a registered β-adjusted residual method is raw relative return theater. QUANT rule: rel = simple-diff **NOT α**, **not β-adjusted**.
2. **BTC-beta dependence is extreme in the pack sample (description, not a pair license):**
   - Corr **ETH–BTC = 0.888… ≈ 0.89** (QUANT table rounds **0.89**; CSV `0.888417508385592`). Window **2026-05-28 → 2026-09-15**, pre-FOMC. **Corr ≠ causation**; **no hedge ratio**; **no stability claim**.
3. **Raw rel returns are labeled NOT α in QUANT (must not be read as edge):**

   | Horizon | ETH ret | BTC ret | Raw ETH−BTC (**NOT α**) | asof |
   |---|---:|---:|---:|---|
   | 30d crypto bars | +26.3% | +18.1% | **+8.2%** | 2026-09-17 |
   | 90d crypto bars | +41.3% | +21.2% | **+20.1%** | 2026-09-17 |
   | YTD | −19.5% | −14.1% | **−5.4%** | 2026-09-17 |

   Source: `metrics_active_and_watch.csv` / QUANT ETH one-pager. Bar counts, not calendar months. YTD post-selection descriptive only.
4. **Vol panels not cross-comparable:** ETH RV20/RV60 **41.7% / 58.9%** √**365**; BTC **35.6% / 39.1%** √**365**; equity peers use √**252**. Do not mix annualization when arguing “ETH vol edge.”
5. **Funding / OI gaps (block microstructure claims):**
   - Live HL refresh RQ-20260917-A = HTTP **429**; stale lab capture **2026-09-17T00:28:03Z** = appendix only / **DO NOT SIZE**.
   - ETH fundingHistory 24h: **unavailable** (429).
   - ETH OI/mark ULIDs: **missing** from known MM set (QUANT data-gaps table). Stale lab OI$ proxy ~$2.37B is **not** a live residual input.
   - Spot ETH ETF multi-day flow series: **unavailable** in pack → conditional upside unfalsifiable.

### What would rehabilitate
Falsifiable pack, all present:
1. Named residual protocol: β method + **window start/end + as-of** + pass/fail rule on β-adjusted ETH residual vs BTC.
2. Separate **L2 fee/activity residual** with primary dashboard sources + as-of (not vibes).
3. Ingested ETH **OI / mark / continuous fundingHistory** (fresh, not 429 appendix).
4. Multi-day ETH ETF aggregate net-flow series with issuer as-of.
5. Explicit ban retained: raw ETH−BTC simple-diff never re-enters as edge language.

Until then: **BTC-beta watch only** (membership ≠ RV call).

### Conf ceiling (0–1)
**0.28** (matches #23 FAIL haircut). Treating ETH/BTC outperf as an active pair/RV call above this is methodologically dishonest while β/L2/funding gates are empty.

---

## 2. JPM vs XLF — diversifier / pair double-count

### Stated expectation
**JPM** (pre-#23): further upside if NII guide **beats SEP-implied path** — residual with **no numeric gap**. Scorecard **FAIL**. Patch: **earnings-watch only**; residual empty; conf **0.48 → 0.36**.

**XLF** (pre-#23): conditional/watch **diversifier** to JPM; cycle IF breadth from non-JPM banks. Scorecard **FAIL**. Patch: **monitor-only diversifier**, size-cap ≪ JPM; conf **0.36 → 0.24**.

### Why invalid (quant/method)
1. **XLF is not an independent diversifier in this sample.** Corr **JPM–XLF = 0.728… ≈ 0.73** (QUANT rounds **0.73**; CSV `0.7282170140875045`), same 60d pre-FOMC window. That is **co-movement description**, not diversifier proof, not a pair trade, not causation.
2. **Double-count is the default:** one higher-for-longer financials theme, two tickers. Holding both as “active expressions” without an xor / size-cap≪JPM **mandate + breadth metrics** double-counts the same macro narrative QUANT already flags as crowded / **no allocation from FOMC**.
3. **JPM residual was unfalsifiable theater:** “beats what SEP already priced” with **no** SEP-implied NII figure, **no** company guide extract, **no** pass/fail rule → residual undefined (#22/#23). **Unavailable — gap** (must not invent).
4. **XLF breadth metrics empty:** aggregate bank NII / KRE vs XLF with registered window/threshold = **unavailable**. Without them, “diversifier value” is narrative.
5. **Descriptive metrics (not edge):** JPM RV20/RV60 **15.9% / 18.0%** √252; XLF **13.7% / 13.0%** √252; raw vs SPY 21d/63d/YTD JPM **−0.9% / +5.1% / −2.2%**, XLF **−0.5% / +2.5% / −8.3%** — simple-diff **NOT α** (`metrics_active_and_watch.csv`).

### What would rehabilitate
1. **JPM:** explicit gap test — company NII guide (URL, as-of, figure) vs stated SEP-implied mapping (source, as-of, method) + numeric pass/fail. No macro→NII causation without prints.
2. **XLF xor or size-cap ≪ JPM:** Principal-written mandate that XLF is monitor/diversifier at strictly lower research weight **and** operational breadth pack (FDIC/Fed aggregate NII + KRE vs XLF window/threshold).
3. Corr **0.73** may be cited only as sample description; never as pair underwriting.
4. Single-trigger discipline kept: JPM NII-miss vs guide auto-drops XLF sleeve (double-count).

### Conf ceiling (0–1)
**JPM residual / SEP-beat expression: 0.36.** **XLF as independent diversifier / pair leg: 0.24.** Joint “JPM+XLF active pair” as two independent calls: treat as **≤ 0.24** (weaker leg binds) until xor/breadth exists.

---

## 3. NVDA–AVGO–SMH — basket-outperform / triple-count

### Stated expectation
**SMH** (pre-#23): watch basket; cycle IF **basket outperforms** if AI buildout broadens beyond NVDA. Scorecard **FAIL**. Patch: **monitor-only AI-infra appendix**; **dropped from active expectations**; conf **0.35 → 0.22**.

**NVDA** remains active **PRIMARY** (PASS). **AVGO** active satellite (**INCONCLUSIVE** on residual test — not reopened here except overlap).

### Why invalid (quant/method)
1. **SMH basket-outperform is invalid while NVDA + AVGO singles are active** — same AI-infra theme expressed three ways = **triple-count / theme-dedupe fail** (cards header + #22/#23).
2. **Overlap / holdings %: unavailable — gap.** Issuer holdings file (NVDA weight, AVGO weight, combined overlap %) **not in QUANT pack or call-cards**. Prior ≥45% overlap AND-gate was **unfalsifiable** (#23 removed it). **Do not invent holdings %.**
3. **NVDA–AVGO corr = 0.462… ≈ 0.46** (QUANT **0.46**; CSV `0.46248682909061356`) — co-movement, **not** identity, **not** a two-name license, **not** a three-name SMH license.
4. **SMH YTD must not promote:** SMH YTD **+46.1%**, raw vs SPY YTD **+35.2%** (asof 2026-09-16) — QUANT labels **post-selection descriptive, not a promotion argument**. Ret 21d/63d **−8.2% / −11.4%**; RV20/RV60 **32.0% / 45.3%** √252.
5. **ADV context only (not thesis):** SMH ADV 5d **6.9M** sh (Yahoo stamp 2026-09-17T00:49:39Z); notional ≈ **$3.74B** at scan last — liquidity description, not basket-outperform evidence.

### What would rehabilitate
1. Published holdings overlap % vs NVDA/AVGO (issuer file, as-of) **before** any xor.
2. Explicit Principal xor: **SMH OR singles** (not both as active expectations), or hedge-mandate language with size rules.
3. While NVDA primary + AVGO satellite remain active: SMH stays **appendix only** — no “broadening outperform” cycle IF.
4. Never use QUANT YTD raw vs SPY to restore SMH to active expectations.

### Conf ceiling (0–1)
**0.22** for SMH as active basket-outperform / third AI expression. NVDA primary PASS is **not** a license to keep SMH active.

---

## 4. UNI — undated governance event optionality

### Stated expectation
Pre-#23: conditional / **event-gated fee-switch**; cycle IF binary re-rate if dated fee-switch lands. Scorecard **FAIL** (Skeptic #14 reject stands). Patch: **deferred governance watch** — **not an active call**; 90-day clock **removed**; conf **0.32 → 0.20**.

### Why invalid (quant/method)
1. **Undated governance optionality is not a call.** No dated primary proposal URL as of 2026-09-17 → event gate is empty → expectation is **unfalsifiable fishing**.
2. Prior **90-day** “no proposal → kill” calendar from 2026-09-17 still lacked a **dated** event — fishing presented as a live gate (#23).
3. **QUANT bounce is footnote, not thesis:** UNI ret 30d/90d **+103.8% / +117.3%** includes bounce from ~$3.20 (2026-08-14); raw vs BTC **+85.7% / +96.1% / +30.0% YTD** — **NOT α**. Kraken sample shorter (starts **2024-09-27**). RV20/RV60 **116.3% / 98.2%** √365; MDD **−75.1%**.
4. HL dayNtl ~$31.2M (stale 2026-09-17T00:28:03Z): appendix / **DO NOT SIZE**; no UNI funding obs_id in known set.

### What would rehabilitate
1. New card citing a **dated** Uniswap governance proposal URL with executable fee-switch parameters + as-of.
2. Explicit event invalidation tied to that proposal’s timeline (not a floating 90-day fish).
3. Fresh HL funding/OI if microstructure is claimed — never stale appendix.
4. QUANT bounce prints remain non-supportive of the event claim.

### Conf ceiling (0–1)
**0.20.** Event-optionality as an active/watch “call” above this without a dated URL fails falsifiability.

---

## 5. AAVE — rate→credit + missing utilization baseline

### Stated expectation
Pre-#23: conditional crypto credit under higher-for-longer; cycle IF utilization/revenue rise; micro-size. Scorecard **FAIL**. Patch: **deferred / micro watch**; credit expectation **killed**; conf **0.30 → 0.18**.

### Why invalid (quant/method)
1. **Rate → credit demand is a causation leap.** FF hike / SEP higher-for-longer (macro obs backdrop) ≠ Aave utilization ≠ protocol revenue. QUANT: **corr ≠ causation**; macro obs_ids ≠ name edge.
2. **Utilization baseline: unavailable — gap.** No obs-linked core-market utilization print + dashboard URL + as-of in pack/cards. Prior “−25% from latest dashboard print within 30d” was **unfalsifiable** (#23 removed).
3. **Liquidity / HL:** stale dayNtl ~$12.9M / OI$ ~$67.5M (2026-09-17T00:28:03Z) = appendix / **DO NOT SIZE** (429). No AAVE funding obs_id. Not a micro-size license.
4. **Descriptive returns ≠ credit thesis:** ret 30d/90d/YTD **+34.5% / +60.6% / −19.3%**; raw vs BTC **+16.3% / +39.4% / −5.2%** (**NOT α**); RV20/RV60 **57.8% / 90.4%** √365; MDD **−80.3%**.

### What would rehabilitate
1. Obs-linked utilization **baseline** (print + source URL + as-of + obs_id or file cite).
2. Mechanism test that does **not** equate policy rate path with borrow demand (utilization/revenue series independent of pure BTC beta).
3. Fresh venue liquidity if any size language returns — never 429 appendix.
4. Credit-frame revival without (1) remains methodologically invalid by construction.

### Conf ceiling (0–1)
**0.18.** Credit-call reading of AAVE above this without utilization baseline + non-causation mechanism is rejection-honest invalid.

---

## PASS contrast only (short) — why these survive methodology

Do **not** reopen memory-semi. Do **not** promote PASS names to trades.

| Name | Why methodology PASS (scorecard #22) | Contrast vs FAILs |
|---|---|---|
| **BTC** | Benchmark / range + conditional gates; funding stamp ≠ forecast; cycle IF correctly **empty/speculative** until ETF + fresh fundingHistory; no corr-as-causation; crypto RV stays √365 panel. Conf card **0.45**. | Unlike ETH: no raw-outperf-as-edge claim; unlike AAVE/UNI: does not pretend empty gates are filled. |
| **NVDA** | Crowded / unwind honesty; cycle upside gated on **documented mispricing vs consensus** (honest empty); no HL; equity √252 OK; no corr-as-causation. Conf card **unchanged** by #23. | Unlike SMH: primary single-name with explicit mispricing gate — not basket-outperform while overlapping actives. |
| **XOM** | Explicitly kills “Fed hike → XOM up”; path is **crude-gated** (strip/inventory mechanism family); negative 60d corr vs semis/crypto (**XOM–NVDA −0.25**, **XOM–BTC −0.12** in sample) **≠** energy-sleeve argument. Conf card **0.38**. | Unlike JPM/XLF/AAVE: refuses macro→name causation; gate family matches the actual driver. |

**Board reminder:** QUANT pack PASS (narrow, descriptive metrics) ≠ expectation PASS. Only BTC / NVDA / XOM clear expectation methodology. Six FAILs above remain blockers for pair/active-expression reads even after #23 demotions — demotion acknowledges invalidity; it does not restore the expression.

---

## Explicit non-actions

- No trades, no sizing, no allocation, no Telegram copy, no `live.yaml`.
- No invented β, NII-gap, holdings %, or utilization numbers — gaps labeled **unavailable**.
- No memory-semi reopen.
- No α language as edge; HL stale not primary; corr ≠ causation; √365 vs √252 labeled.

**Signed:** QUANT invalidation · Principal/Don queue · 2026-09-17 AEST · private repo only · **not a trade**
