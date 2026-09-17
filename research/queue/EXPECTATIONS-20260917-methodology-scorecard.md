# Skeptic — watchlist / membership EXPECTATIONS methodology scorecard

| Field | Value |
|---|---|
| **Date** | 2026-09-17 (Australia/Sydney, AEST) |
| **Ask** | Principal → Don → Skeptic: PASS/FAIL methodology behind watchlist expectations (not a trade). Don pushes Telegram. |
| **Sources** | `research/queue/QUANT-20260917-active-calls.md` (**main**, PR #19 merged, Skeptic methodology PASS narrow on re-review) · `research/queue/UNIVERSE-20260917-call-cards.md` (**PR #13 open**, not on main) · `config/universe.yaml` (main) · Skeptic #14/#21 context |
| **Out of scope** | Memory-semi / MU / SNDK / SK Hynix (**Principal killed** — not reopened). No trades. No invented numbers. No allocation. |
| **What PASS/FAIL means here** | **Methodology of the stated expectation**, not realized P&L. **PASS** = honest, QUANT-rule-clean, falsifiable or correctly labeled empty/speculative. **FAIL** = violates QUANT honesty, corr-as-causation, treats raw outperformance as edge, relies on stale HL, or presents unfalsifiable theater as a recommendation. **INCONCLUSIVE** = missing artifact / gate empty so the test cannot yet be run. |

**QUANT honesty rules applied:** windows/as-of discipline · HL stale = appendix only / DO NOT SIZE · rel = simple-diff **NOT α** · √365 ≠ √252 · corr ≠ causation · no allocation from pre-FOMC corr · post-selection YTD not lock justification.

---

## Overall board scorecard

| Tier | PASS | FAIL | INCONCLUSIVE | Total |
|---|---:|---:|---:|---:|
| In-universe pack-era (9) | 3 | 3 | 3 | 9 |
| Watch-only (4) | 0 | 3 | 1 | 4 |
| **Board** | **3** | **6** | **4** | **13** |

| Name | Tier | Verdict |
|---|---|---|
| BTC | in_universe | **PASS** |
| ETH | in_universe | **FAIL** |
| NVDA | in_universe | **PASS** |
| AVGO | in_universe | **INCONCLUSIVE** |
| MSFT | in_universe | **INCONCLUSIVE** |
| META | in_universe | **INCONCLUSIVE** |
| JPM | in_universe | **FAIL** |
| XLF | in_universe | **FAIL** |
| XOM | in_universe | **PASS** |
| UNI | watch | **FAIL** |
| AAVE | watch | **FAIL** |
| SMH | watch | **FAIL** |
| IBIT | watch (Principal greenlight; no card on main) | **INCONCLUSIVE** |

**Board read:** Expectations methodology is **not board-clear**. Only BTC / NVDA / XOM clear a methodology PASS. Six FAILs are blockers for treating those names’ written expectations as research-grade. Four INCONCLUSIVE need artifacts/gates before any PASS/FAIL on path claims.

### Blockers (unfalsifiable or rule-breaking expectations)

1. **ETH** — cycle expectation framed as ETH/BTC outperformance without a β/residual protocol; conflicts with QUANT “raw ≠ α.”
2. **JPM** — “NII beats what SEP already priced” with **no numeric SEP-implied vs guide gap** → residual undefined.
3. **XLF** — diversifier/breadth claim without aggregate NII / KRE series operationalized.
4. **UNI** — event-gated with **no dated event** (90-day fishing); Skeptic #14 reject still stands methodologically.
5. **AAVE** — higher-for-longer → credit demand (causation) + utilization baseline missing.
6. **SMH** — basket-outperform / AI-broadening claim while double-counting NVDA+AVGO; holdings weights absent.
7. **IBIT** — no formal expectation write-up in queue on main (sidebar only on killed memory-semi intent).
8. **Call-cards not on main** — active expectation source is still **PR #13**; cite risk until merge.

**Explicit:** This scorecard is **not** a trade, size, or allocation recommendation.

---

## In-universe membership — per name

### BTC — **PASS**
1. **Stated expectation** — Expectation: watch-only / benchmark + conditional (funding/basis/ETF/reg); **not** hawkish-Fed-up. Expected path: **1–5 sessions** range / beta to risk tape; funding stamp = snapshot not forecast; cycle IF only if ETF multi-day inflows + basis/funding gates clear (`UNIVERSE-20260917-call-cards.md` §1, PR #13). QUANT: deepest book ≠ mispricing; no thesis until ETF + fresh fundingHistory (`QUANT-20260917-active-calls.md`, main).
2. **Methodology check** — Aligns with QUANT: no HL sizing, funding not forecast, cycle correctly gated empty/speculative, no corr-as-causation, crypto RV stays √365 panel if used.
3. **Verdict:** **PASS**
4. **Why:** Benchmark/range expectation is honest and rule-clean; cycle path does not pretend gates are filled.

### ETH — **FAIL**
1. **Stated expectation** — Expectation: conditional RV vs BTC. Expected path: 1–5s tracks BTC with possible funding skew; cycle IF = ETH/BTC outperformance if ETF + L2 gates clear (call-cards §2). QUANT: raw vs BTC **NOT α**; OI/mark ULIDs missing; HL omitted/429.
2. **Methodology check** — Cycle expectation **is** raw relative outperformance without β-residual method → violates QUANT rel≠α spirit. Gates empty. Funding skew without OI series = incomplete microstructure.
3. **Verdict:** **FAIL**
4. **Why:** Outperformance-vs-BTC expectation reads as edge without a residual protocol; QUANT forbids that read.

### NVDA — **PASS**
1. **Stated expectation** — Expectation: conditional; crowded; needs mispricing angle not “AI demand exists.” Expected path: 1–5s high-beta / crowded unwind risk; cycle IF upside only with documented mispricing vs consensus (call-cards §5). QUANT: crowded; macro ≠ name edge.
2. **Methodology check** — Near-term path is descriptive risk, not alpha claim. Cycle upside gated on missing mispricing (honest empty). No HL. Equity √252 panel OK. Does not use corr as causation.
3. **Verdict:** **PASS**
4. **Why:** Crowded/unwind honesty + explicit mispricing gate; no QUANT rule breach.

### AVGO — **INCONCLUSIVE**
1. **Stated expectation** — Expectation: conditional satellite to NVDA; independence of evidence required. Expected path: 1–5s high corr to NVDA/SMH; cycle IF satellite add only if AI line-item / customer cohort show **independent** cash-conversion (call-cards §6). QUANT: NVDA–AVGO 0.46 ≠ two-name license.
2. **Methodology check** — Independence/residual test **named but not specified** (no regression window, no metric). Corr sample is pre-FOMC point estimate only — cannot underwrite “high corr” as stable expectation.
3. **Verdict:** **INCONCLUSIVE**
4. **Why:** Satellite residual claim lacks an operational test definition.

### MSFT — **INCONCLUSIVE**
1. **Stated expectation** — Expectation: conditional / earnings-gated. Expected path: 1–5s quality drift; cycle IF multiple holds if Azure growth + capex ROI confirm (call-cards §8). QUANT: large raw vs-SPY 63d is **not** residual α; RV20≪RV60 ≠ regime ID.
2. **Methodology check** — Earnings gate is the right shape; Azure extract still empty → cycle path not yet falsifiable. Must not read QUANT raw outperformance as confirming the expectation.
3. **Verdict:** **INCONCLUSIVE**
4. **Why:** Gate design OK; evidence pack empty so path claim cannot be scored PASS/FAIL yet.

### META — **INCONCLUSIVE**
1. **Stated expectation** — Expectation: conditional / earnings-gated ads+AI ROI. Expected path: 1–5s high-beta to ad/AI headlines; cycle IF re-rate only if ad growth + infra ROI beat embedded consensus (call-cards §9). QUANT: META asof **2026-09-15** lag; raw vs SPY **not contemporaneous**.
2. **Methodology check** — Same earnings-gate honesty as MSFT. Any evaluation that uses QUANT short-window rel vs SPY **fails as-of discipline** until META lag fixed. Ad/DAU extracts missing.
3. **Verdict:** **INCONCLUSIVE**
4. **Why:** Empty fundamental gates + QUANT META lag blocks clean short-horizon checks.

### JPM — **FAIL**
1. **Stated expectation** — Expectation: conditional; higher-for-longer NII OK but **likely priced** post-FOMC/SEP. Expected path: 1–5s may already reflect SEP; cycle IF further upside only if NII guide beats SEP-implied path (call-cards §10). QUANT: no allocation from FOMC; crowded narrative.
2. **Methodology check** — “Beats what SEP already priced” is a residual claim **without a numeric SEP-implied NII / market-implied gap**. Near-term “limited edge” is honest; cycle residual is unfalsifiable theater until quantified. Risk of corr/macro → NII causation without prints.
3. **Verdict:** **FAIL**
4. **Why:** Priced-in residual expectation has no measurable gap definition.

### XLF — **FAIL**
1. **Stated expectation** — Expectation: conditional/watch diversifier to JPM. Expected path: 1–5s tracks JPM/financials; cycle IF diversifier value if non-JPM banks/capital markets add breadth (call-cards §11). QUANT: JPM–XLF 0.73 is sample description not a pair trade.
2. **Methodology check** — Breadth/diversifier value undefined without aggregate NII/credit/KRE series. Double-count vs JPM primary. Corr cluster ≠ diversifier proof (corr≠causation).
3. **Verdict:** **FAIL**
4. **Why:** Diversifier expectation is narrative without operational breadth metrics.

### XOM — **PASS**
1. **Stated expectation** — Expectation: conditional / crude-gated; kill “Fed hike → XOM up.” Expected path: 1–5s tracks crude strip/inventory; cycle IF FCF/buyback if strip holds (call-cards §12). QUANT: hike ≠ XOM upside; negative corr ≠ energy sleeve.
2. **Methodology check** — Explicitly kills corr-as-causation. Crude gate is the right mechanism family. Must still bring strip/inventory as-of (not in QUANT pack) before thesis — but expectation methodology itself is clean.
3. **Verdict:** **PASS**
4. **Why:** Crude-gated path respects QUANT anti-causation rule; hike narrative rejected.

---

## Watch-only — per name

### UNI — **FAIL**
1. **Stated expectation** — Expectation: conditional / event-gated fee-switch. Expected path: 1–5s drift no edge; cycle IF binary re-rate if dated fee-switch lands (call-cards §3). Universe: watch-only (`universe.yaml`). QUANT: extreme 30d/90d bounce footnoted not thesis; HL appendix only.
2. **Methodology check** — No dated proposal → event expectation is unfalsifiable fishing (Skeptic #14 reject). Must not read QUANT bounce prints as support.
3. **Verdict:** **FAIL**
4. **Why:** Event-gated expectation without a dated event fails falsifiability.

### AAVE — **FAIL**
1. **Stated expectation** — Expectation: conditional crypto credit under higher-for-longer; micro-size. Expected path: 1–5s illiquid drift; cycle IF utilization/revenue rise (call-cards §4). Watch-only in universe.yaml.
2. **Methodology check** — Rate → borrow-demand is causation leap; utilization invalidation baseline missing; HL dayNtl thin must not be sized from stale appendix.
3. **Verdict:** **FAIL**
4. **Why:** Causation + missing baseline make the credit expectation methodologically invalid.

### SMH — **FAIL**
1. **Stated expectation** — Expectation: conditional/watch basket; double-count disclosed. Expected path: 1–5s tracks AI-semi; cycle IF basket outperforms if buildout broadens beyond NVDA (call-cards §7). Watch-only.
2. **Methodology check** — Outperform claim without holdings/overlap % and while NVDA+AVGO active = theme-dedupe fail. YTD outperformance in QUANT must not justify promotion (pack already warns).
3. **Verdict:** **FAIL**
4. **Why:** Basket-outperform expectation double-counts AI-infra without an xor/overlap test.

### IBIT — **INCONCLUSIVE**
1. **Stated expectation** — Principal greenlit **IBIT watch-only** as BTC equity-proxy / TradFi wrapper adjacent to RQ-A / BTC (sidebar in killed `INTENT-20260917-memory-semi.md` only; **not** in `universe.yaml` in_universe/watch_only lists on main; **no** expectation-card section).
2. **Methodology check** — No formal expectation path, invalidation, or QUANT row. Cannot apply windows/as-of or rel≠α checks to a missing write-up. Must not invent an expectation.
3. **Verdict:** **INCONCLUSIVE**
4. **Why:** Greenlight without a queue expectation artifact — nothing methodologically testable yet.

---

## Cross-cutting methodology notes

1. **Call-cards still on PR #13** — Telegram readers should know expectations cited here are **not merged to main**; QUANT honesty rules **are** on main.
2. **QUANT PASS (narrow)** does **not** promote any name’s expectation to thesis — it only clears the descriptive metrics snapshot.
3. **HL 429** — any expectation that needs fundingHistory / fresh OI remains blocked; do not substitute stale appendix.
4. **Memory-semi killed** — MU/SNDK/Hynix expectations are out of board; do not reopen.

---

## Explicit non-actions

- No trades, no sizing, no allocation, no `live.yaml`.
- No invented numbers.
- No must-cut reopen; no memory-semi reopen.
- No risk approval.

**Signed:** Skeptic · 2026-09-17 · board **3 PASS / 6 FAIL / 4 INCONCLUSIVE** · not a trade
