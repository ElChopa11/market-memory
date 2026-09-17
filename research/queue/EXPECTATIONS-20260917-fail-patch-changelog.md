# EXPECTATIONS-20260917 — FAIL patch changelog (Skeptic #22)

| Field | Value |
|---|---|
| **Date** | 2026-09-17 (Australia/Sydney, AEST) |
| **Ask** | Coordinator / Research: patch call-card **expectations** that Skeptic scored **FAIL** on methodology (not P&L). |
| **Scorecard** | `research/queue/EXPECTATIONS-20260917-methodology-scorecard.md` (PR #22) |
| **Patched artifact** | `research/queue/UNIVERSE-20260917-call-cards.md` (from PR #13 branch) |
| **QUANT honesty (binds)** | `research/queue/QUANT-20260917-active-calls.md` (main, PR #19): windows/as-of · HL stale = appendix / DO NOT SIZE · rel = simple-diff **NOT α** · corr ≠ causation · no allocation from pre-FOMC corr |
| **Principal tiers** | `config/universe.yaml` (PR #15, main): UNI / AAVE / SMH already **watch-only**. **Not edited** this patch. Memory-semi **killed** — not reopened. |
| **What this is** | Expectation-label / invalidation / honesty patch. **Not** a trade, size, allocation, thesis folder, or `universe.yaml` change. |

**Board after this patch (methodology of written expectations):** FAIL names are demoted or emptied so they no longer claim unfalsifiable residual / event / credit / basket-outperform paths. This changelog does **not** re-score PASS/FAIL; it maps each FAIL → the exact patch applied.

---

## Map: FAIL → patch

| Name | Scorecard tier | FAIL (why) | Patch applied |
|---|---|---|---|
| **ETH** | active | Cycle ETH/BTC outperformance without β/residual protocol; QUANT rel≠α; AND-invalidation | Demote to **BTC-beta watch**. Ban α. Residual empty until protocol defined. **Single-trigger** ETF-outflow invalidation. Conf 0.40 → **0.28**. |
| **JPM** | active | “NII beats SEP-implied” with no numeric gap; macro→NII causation risk | Relabel **earnings-watch only**. Residual **empty/speculative** until gap test (number/source/as-of/pass-fail) exists — **not invented**. Conf 0.48 → **0.36**. |
| **XLF** | active | Diversifier/breadth without aggregate NII/KRE; corr-as-proof; weak blog | **Monitor-only diversifier**, size-cap ≪ JPM. Double-count default. Corr 0.73 = description not proof. **Blog removed**. Conf 0.36 → **0.24**. |
| **UNI** | watch | Event-gated with no dated event; 90-day fishing | **Deferred governance watch** (watch-only membership; not a Quant verdict). 90-day clock **removed**. No dated primary proposal URL. Conf 0.32 → **0.20**. |
| **AAVE** | watch | Rate→credit leap; utilization baseline missing; stale HL sizing | **Deferred / micro watch**. Credit expectation killed. HL appendix / DO NOT SIZE. Unfalsifiable 25% trigger **removed**. Conf 0.30 → **0.18**. |
| **SMH** | watch | Basket-outperform while NVDA+AVGO active; holdings % absent | **Monitor-only AI-infra basket appendix**; **dropped from active expectations**. Overlap % required before xor. Conf 0.35 → **0.22**. |

**Not patched (by design):** BTC, NVDA, XOM (PASS keepers — substance untouched). AVGO, MSFT, META, IBIT (INCONCLUSIVE — out of scope). AVGO and NVDA received **one-line** SMH-appendix role cross-refs only, forced by the SMH FAIL patch.

---

## 1) ETH (active) — FAIL → BTC-beta watch

**Scorecard FAIL:** Cycle expectation framed as ETH/BTC outperformance without a β/residual protocol; conflicts with QUANT “raw ≠ α.” AND-invalidation. Gates empty.

**Patch (prefer demote — residual evidence empty):**

| Field | Before | After |
|---|---|---|
| Heading / expectation | conditional RV vs BTC | **BTC-beta watch** (pack-era listed with in-universe names; yaml later `watch_only`; **not** RV/α) |
| Expected path (cycle) | ETH/BTC outperformance if ETF + L2 gates clear | **No** outperformance/α claim. Residual **empty** until named-window β-adjusted residual **plus** L2 fee/activity residual are defined |
| α language | RV / outperformance as cycle IF | **Banned.** Raw ETH−BTC (QUANT simple-diff) is **not** edge |
| Invalidation | AND: ETH−BTC ≤−8% / 20d **and** ETF outflows ≥5 of last 10 | **Single-trigger:** ETH ETF aggregate net outflows ≥5 consecutive US trading days — kill promotion from beta-watch to independent/RV long. Raw ETH−BTC is not the trigger |
| HL | “supports research size” | Stale lab appendix; QUANT DO NOT SIZE |
| Conf | 0.40 (≤ 0.50) | **0.28** (Skeptic #22 FAIL haircut) |

No invented β, window, or L2 numbers.

---

## 2) JPM (active) — FAIL → earnings-watch only

**Scorecard FAIL:** “NII beats what SEP already priced” with **no** numeric SEP-implied vs guide gap → residual undefined. Macro→NII causation without prints.

**Patch (gap test not written — numbers would be invented):**

| Field | Before | After |
|---|---|---|
| Call | conditional; higher-for-longer NII likely priced | **earnings-watch only**; still financials **PRIMARY** by role |
| Cycle residual | further upside if NII guide beats SEP-implied path | **Empty/speculative.** Gap test (what number, source, as-of, pass/fail) **not defined** |
| Causation | FF → NII mechanism “cleanest on the sheet”; JPM AM insight URL | **No macro→NII causation without prints.** AM “opportunity” insight **removed** as causation crutch. Fed/SEP cites remain **backdrop** |
| Invalidation | NII miss **or** NCO +20 bps QoQ | **Single-trigger:** next-quarter NII **misses company guide**. NCO is a monitor, not a second trigger |
| Conf | 0.48 (≤ 0.56) | **0.36** (FAIL haircut) |

Did **not** invent a SEP-implied NII figure or company guide extract.

---

## 3) XLF (active) — FAIL → monitor-only diversifier

**Scorecard FAIL:** Diversifier/breadth claim without aggregate NII / KRE operationalized. Double-count vs JPM. Corr cluster ≠ diversifier proof.

**Patch (breadth metrics empty — do not fake them):**

| Field | Before | After |
|---|---|---|
| Call | conditional / watch diversifier satellite | **monitor-only diversifier**; size-cap **≪ JPM primary** |
| Cycle IF | diversifier value if non-JPM banks add breadth | **No** diversifier-value claim until aggregate bank NII / KRE are operationalized |
| Double-count / corr | noted unless mandate | **Double-count is the default.** QUANT JPM–XLF 0.73 (window 2026-05-28 → 2026-09-15, pre-FOMC) = **description, not proof** |
| Evidence | gomdorieconomic.com blog (2026-04-22) cited then hedged | **Removed** (weak/stale blog-grade) |
| Invalidation | JPM invalidation **or** (KRE ≤−10% / 20d with stress headlines) | **Single-trigger:** JPM NII-miss invalidation auto-drops XLF (double-count). KRE AND-gate removed |
| Conf | 0.36 (≤ 0.53) | **0.24** (FAIL haircut) |

`universe.yaml` listed XLF under the former **`active_calls`** key (Principal; quoted as the pack-era key). This patch demotes the **expectation**, not membership. IMP-005: that key is now **`in_universe`**; XLF is **`watch_only`** after yaml PR #24.

---

## 4) UNI (watch) — FAIL → deferred governance watch

**Scorecard FAIL:** Event-gated with **no dated event**; 90-day fishing; Skeptic #14 reject still stands.

**Patch (no dated primary proposal URL exists):**

| Field | Before | After |
|---|---|---|
| Expectation | conditional / event-gated (fee-switch) | **deferred governance watch** — **watch-only membership, not a Quant verdict**; matches watch-only |
| Cycle IF | binary re-rate if dated fee-switch lands | **No** event/re-rate expectation this cycle |
| 90-day clock | no proposal reaching on-chain vote within 90 days of 2026-09-17 | **Removed** (undated fishing presented as a live gate) |
| Invalidation | 90-day fishing clock | **Single-trigger:** event-gated frame **already killed** by missing dated proposal URL as of 2026-09-17. No countdown. Revival = new card citing URL |
| HL | dayNtl ~$31M “borderline” | Stale lab appendix; DO NOT SIZE |
| Conf | 0.32 (≤ 0.38) | **0.20** (FAIL haircut) |

---

## 5) AAVE (watch) — FAIL → deferred / micro watch

**Scorecard FAIL:** Rate → credit-demand causation; utilization baseline missing; HL thin must not be sized from stale appendix.

**Patch:**

| Field | Before | After |
|---|---|---|
| Call | conditional crypto credit; micro-size until liquidity improves | **deferred / micro watch** until utilization **baseline** exists. **Not** a credit call. Matches watch-only |
| Cycle IF | revenue/utilization rise under sticky rates | **No** credit/utilization-rise expectation |
| Rate→credit | two-conditional leap flagged but still the call | **Killed.** Rate path ≠ utilization ≠ revenue |
| HL | dayNtl / OI$ as liquidity/exit-trap sizing color | **Appendix only / DO NOT SIZE** (QUANT 429). Not a micro-size license |
| Invalidation | utilization −25% from “latest dashboard print” within 30d **or** bad-debt rescue | **Removed** (−25% from unknown baseline was unfalsifiable). Credit frame **already dropped**; revival without obs-linked baseline is invalid |
| Conf | 0.30 (≤ 0.36) | **0.18** (FAIL haircut) |

No invented utilization %.

---

## 6) SMH (watch) — FAIL → monitor-only AI-infra basket appendix

**Scorecard FAIL:** Basket-outperform / AI-broadening while double-counting NVDA+AVGO; holdings weights absent.

**Patch:**

| Field | Before | After |
|---|---|---|
| Call | conditional / watch basket / overlap hedge | **monitor-only AI-infra basket appendix**. **Dropped from active expectations.** Matches watch-only |
| Cycle IF | basket outperforms if buildout broadens beyond NVDA | **Removed** while NVDA+AVGO remain active |
| Xor | “what would change our mind” included xor | Xor **blocked** until holdings overlap % vs NVDA/AVGO exists (not invented) |
| Evidence | Yahoo + MarketBeat as weak secondaries on the card | **Removed** as underwriters of a basket-outperform call |
| Invalidation | overlap ≥45% **and** NVDA primary invalidation | **Single-trigger:** NVDA primary invalidation auto-drops SMH appendix. ≥45% AND-gate removed (overlap unpublished → unfalsifiable) |
| Conf | 0.35 (≤ 0.52) | **0.22** (FAIL haircut) |

No invented holdings %. No memory-semi revival via TSM/MU weight talk (weights remain unverified).

---

## Cross-refs forced by FAIL patches (not substance rewrites)

| Name | Scorecard | Change |
|---|---|---|
| **NVDA** (PASS) | PASS | One-liner in reasoning: SMH role is **monitor-only appendix** after #22 (was “SMH basket”). Invalidation / path / conf **unchanged**. |
| **AVGO** (INCONCLUSIVE) | INCONCLUSIVE | One-liner: SMH is appendix, not a third active AI expression. Residual-test gap **not** filled (out of scope). |
| **BTC / XOM** | PASS | **Untouched.** |
| **MSFT / META** | INCONCLUSIVE | **Untouched.** |
| **IBIT** | INCONCLUSIVE | **No card added** (still no queue write-up on main; do not invent an expectation). |

---

## Explicit non-actions

- No trades, no sizing, no allocation, no `live.yaml`, no `universe.yaml` edit.
- No invented NII-gap, β, overlap %, or utilization numbers.
- No thesis folders.
- No must-cut reopen; no memory-semi reopen.
- No risk approval.

**Signed:** Research / Coordinator patch · 2026-09-17 · maps Skeptic #22 six FAILs · not a trade
