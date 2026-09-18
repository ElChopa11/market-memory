# UNIVERSE-20260917 — Intent-level membership cards (Principal / Don)

| Field | Value |
|---|---|
| **Purpose** | Principal ask — reasoning + expectation behind **LOCKED** universe **membership** (not new Quant verdicts; not trades) |
| **Date** | 2026-09-17 (Australia/Sydney, AEST); **language aligned 2026-09-18 (IMP-032)** |
| **Status** | Intent-level membership cards only. **Quant SoT** is the locked-membership board `research/quant/2026-09-18/quant-review-board.md` (**IMP-008 / #38**). Closed verdicts only: `RESEARCH_PRIORITY \| MONITOR \| DEFER \| REJECT \| INSUFFICIENT_DATA`. **Not** theses, not orders, not risk approvals. **Paper only.** **DO NOT SIZE.** |
| **Principal membership** | Encoded in `config/universe.yaml`. IMP-005 keys: **in_universe** BTC, NVDA, AVGO, MSFT, META, JPM, XOM · **watch_only** ETH, UNI, AAVE, SMH, XLF (membership kept; no thesis-priority). Pack-era PR #15 listed ETH/XLF under the former `active_calls` key; yaml PR #24 demoted them. This file does **not** edit `universe.yaml`. Memory-semi **killed** (not reopened). Locked ticker set **unchanged**. |
| **Skeptic cite (historical)** | Overall **REVISE** — **0 pass / 12 revise / 8 reject** (artifact: `research/queue/UNIVERSE-20260917-skeptic-review.md` (PR #11)). Must-cuts **HYPE, SOL, XRP, ARB, NEAR, LINK, GLD, LLY** excluded here; retained only as learning records outside this file. **Do not** treat post-#11 revise language as current priority. |
| **Skeptic #22 FAIL patch (historical)** | **2026-09-17** — ETH / JPM / XLF / UNI / AAVE / SMH expectations patched for methodology FAILs (`research/queue/EXPECTATIONS-20260917-methodology-scorecard.md`, PR #22). Changelog: `research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md`. PASS keepers BTC / NVDA / XOM **untouched** (substance). INCONCLUSIVE AVGO / MSFT / META / IBIT out of scope except one-line role notes where a FAIL patch forced a cross-ref. QUANT honesty binds (`QUANT-20260917-active-calls.md`, historical filename): rel ≠ α · HL stale = appendix / DO NOT SIZE · corr ≠ causation. |
| **Quant SoT (current)** | Board 2026-09-18 (#38): **RESEARCH_PRIORITY = none**. **MONITOR:** ETH, UNI. **DEFER:** BTC, NVDA, JPM, AAVE, SMH, XLF. **INSUFFICIENT_DATA:** AVGO, MSFT, META, XOM. Membership ≠ Quant verdict. This file’s field-1 **Expectation** uses that closed set. Prior “conditional / watch-only / deferred / monitor” prose is **retired** as priority language. |
| **Locked universe (12)** | Crypto HL: BTC, ETH, UNI, AAVE · Equities: NVDA, AVGO, SMH, MSFT, META, JPM, XLF, XOM |
| **Theme-dedupe honesty** | **NVDA / AVGO / SMH** = one AI-infra theme (primary / satellite / appendix). **JPM / XLF** = one financials theme (earnings-watch primary / appendix diversifier role). Theme role ≠ Quant verdict. |
| **Separate intent** | **RQ-20260917-A** BTC funding/basis remains a **separate** workstream — link `research/2026/THESIS-0001-post-fomc-btc-funding/intent.md` (PR #9). The BTC card below is the **universe membership** card, not that thesis. |
| **Honesty bar** | No name is thesis-ready (Skeptic). Priority language is Quant closed-set only. No fabricated obs_ids. No invented gap/overlap/utilization numbers. No new names. Confidence figures below are **historical Skeptic haircuts** (process), not a trade conf and **not** “high confidence.” Stale HL dayNtl / OI live in the **appendix only** — **DO NOT SIZE**. |

**Macro backdrop (shared, not name edge):** FOMC +25bp → FF 3.75–4.00% (`01M2PCX90PQAP96J62RR6EWQ35`); FF (`01M2PCX8ZJZCKC52NQ03PHNZWE`); IORB 3.90% (`01M2PCX9005R4S8GRPQJP96CRP`); primary credit 4.00% (`01M2PCX90C2J9RPG17CSZDTV3Q`); Reuters/SEP partial (`01M2PCX91243QK9V8HCCWQFASY`); Fed statement https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm (2026-09-16). Senate H.R.3633 cloture fail 49–50 (2026-09-15): https://www.senate.gov/legislative/LIS/roll_call_votes/vote1192/vote_119_2_00234.htm.

---

## 1. BTC (Hyperliquid perp) — liquidity benchmark · Quant **DEFER**

1) **Expectation** — Quant SoT **DEFER** (`research/quant/2026-09-18/quant-review-board.md`, #38). Membership: **in_universe** liquidity/funding **benchmark**. **Not** hawkish-Fed-up. Universe **membership** card only; funding/basis research lives under **RQ-20260917-A** (`research/2026/THESIS-0001-post-fomc-btc-funding/intent.md`, PR #9). Paper only. **DO NOT SIZE.**
2) **Reasoning** — Deepest HL book (stale lab appendix — **DO NOT SIZE**; see [appendix](#appendix--stale-hl-lab-snapshot--do-not-size)) is the lab liquidity/funding **reference**, not an upside seed. Falsifiable drivers if/when data exists: (a) multi-day spot ETF net inflow resume; (b) funding/basis dislocation mean-reverts without OI collapse; (c) legislative path after H.R.3633 cloture fail. Cite MM: funding `01M2PCXAFASC2V0WCGWR0E8MZT`, OI `01M2PCXAFMC3792Y1PQ3H2ACVQ`, mark `01M2PCXAEE4BRXTPMV56SYN56V`, oracle `01M2PCXAEY18W6290P82NECSM7`, mid `01M2PCXACWWCDJRR2GJ20RV7D4`; macro `01M2PCX90PQAP96J62RR6EWQ35`, `01M2PCX91243QK9V8HCCWQFASY`; Senate URL above. Hawkish tape + CLARITY setback are **already public** — do not treat as mispricing.
3) **Expected path** — **1–5 sessions:** range / beta to risk tape; funding stamp is a snapshot, not a forecast (**speculative** without fundingHistory continuity). **This cycle:** gates empty — stay **DEFER** (benchmark membership, not a cycle-upside pack).
4) **Catalysts / checkpoints** — Daily ETF net flow prints; HL fundingHistory series vs single stamp; CME basis vs HL; any dated substitute bill calendar post–H.R.3633.
5) **Invalidation** — **Primary (single-trigger):** ≥5 consecutive US trading days of spot BTC ETF **net outflows** (aggregate issuer prints) while HL funding stays ≥ +0.01%/8h with OI$ declining ≥15% from capture baseline — kill universe promotion and RQ-A upside frames.
6) **What would change our mind** — Verified multi-day ETF inflow streak + CME/HL basis dislocation with intact OI; or dated legislative revival with corridor volume (not hope after known fail).
7) **Data still needed before thesis.md** — Verified multi-day ETF flow series; HL `fundingHistory` continuity; basis vs CME (Skeptic hard-gate + shortlist still-need). Reclassify away from cycle-upside until gates clear. Stays **DEFER** until then.
8) **Confidence** — **0.45** (historical Skeptic haircut ≤ shortlist 0.55; process only — not a trade conf).

---

## 2. ETH (Hyperliquid perp) — BTC-beta · Quant **MONITOR**

1) **Expectation** — Quant SoT **MONITOR** (#38). Membership: **watch_only** BTC-beta watch after yaml PR #24 (**not** a residual/RV vs BTC; **not** standalone beta). **Ban α language.** QUANT: raw ETH−BTC is **not** edge (`rel ≠ α`; not β-adjusted). Paper only. **DO NOT SIZE.**
2) **Reasoning** — HL #2 book (stale lab appendix — **DO NOT SIZE**; see [appendix](#appendix--stale-hl-lab-snapshot--do-not-size); live refresh 429) explains *why ETH sits next to BTC on the board*, not an upside seed. Only **ETH funding** is MM-linked (`01M2PCPEK2ZXFDKPK0TDZZZ5M4`); OI/mark ULIDs missing from known set. A β-adjusted residual vs BTC over a **named window** plus an L2 fee/activity residual are **not defined** and the evidence pack is **empty**, so the prior RV/outperformance language is **demoted** (Skeptic #22 FAIL) rather than given a fake protocol. Hawkish Fed compresses duration (backdrop only). Same macro/Senate backdrop as BTC. Do not invent ETH OI/mark obs_ids.
3) **Expected path** — **1–5 sessions:** tracks BTC (beta **description**, not a trade). Funding skew is **speculative** without OI series. **This cycle:** **no ETH/BTC outperformance expectation** and **no α claim**. Cycle residual **empty/speculative** until a residual protocol exists (named window + β method + as-of + L2 fee/activity residual with sources). QUANT 30d/90d/YTD raw vs BTC (simple diff) must **not** be read as edge. Stay **MONITOR** (BTC-beta desk watch).
4) **Catalysts / checkpoints** — ETH ETF multi-day net flows (**monitor**); L2 fee/TVL QoQ (**empty**); staking/fee revenue (**empty**). If a later card defines a β-residual, register window/as-of/method **then** — not here.
5) **Invalidation** — **Primary (single-trigger):** ETH ETF aggregate **net outflows** on ≥5 consecutive US trading days — kill any promotion from BTC-beta **MONITOR** to an independent or RV-vs-BTC pack. Replaces the prior **AND**-gate (raw ETH−BTC ≤−8% over 20d **and** ETF outflows). Raw ETH−BTC is **not** this trigger and is **not** edge.
6) **What would change our mind** — A written residual protocol: β-adjusted ETH vs BTC over a **named** window with as-of, **plus** L2 fee/activity residual from primary dashboards, **plus** ingested ETH OI/mark/fundingHistory. Until then, stay BTC-beta **MONITOR**.
7) **Data still needed before thesis.md** — Residual protocol definition (blocking for any RV revival); ETH ETF flows; HL ETH OI/mark obs_ids; staking/fee revenue; fundingHistory. Do not revive RV/α language while those are empty.
8) **Confidence** — **0.28** (historical Skeptic #22 FAIL haircut ≤ shortlist 0.50 — demoted from prior RV language; residual protocol empty).

---

## 3. UNI (Hyperliquid perp) — governance mapping · Quant **MONITOR**

1) **Expectation** — Quant SoT **MONITOR** (#38) on the SEC PR 2026-90 **mapping test**, not on bounce or a fee-switch event. Membership: **watch_only** (PR #15). Older “deferred governance watch” is **not** Quant **DEFER**. **Not** event-gated. **Not** a hawkish-cycle beta pack. Paper only. **DO NOT SIZE.**
2) **Reasoning** — Fee-switch / governance optionality is a **multi-year recycled** narrative; market has priced delays repeatedly (Skeptic #14 reject still stands methodologically). **No dated primary Uniswap proposal URL** as of 2026-09-17 — therefore **no live fee-switch event gate**. Prior **90-day** “no proposal → kill” calendar was **undated fishing** (Skeptic #22 FAIL) and is **removed**. HL liquidity stamps are **stale lab appendix** (**DO NOT SIZE**; see [appendix](#appendix--stale-hl-lab-snapshot--do-not-size)). No UNI funding obs in known set. QUANT 30d/90d bounce is **footnote, not a thesis**. SEC PR 2026-90 (2026-09-17) is a dated public event (temporary Innovation Exemption for Tokenized Securities Venues / permissioned AMM). That does **not** auto-map to Uniswap protocol revenue — **MONITOR** only, with a falsifiable TSV/Uniswap mapping test. Not “DeFi blue-chip vibes.”
3) **Expected path** — **1–5 sessions:** drift with crypto beta; **no edge** (**speculative**). **This cycle:** **no** binary re-rate / fee-switch expectation. Quant stays **MONITOR** on the mapping test until it fails or a dated primary proposal exists. QUANT raw vs BTC is **not** α.
4) **Catalysts / checkpoints** — Mapping test: does PR 2026-90 name Uniswap / a dated Uniswap listing or fee parameter? A **dated** Uniswap governance proposal **URL** with executable fee-switch parameters would be required to reopen an event card — **none cited**. DEX volume share is **not** a substitute event.
5) **Invalidation** — **Primary (single-trigger):** Event-gated fee-switch / binary re-rate frame is **already killed** by absence of a dated primary proposal URL as of 2026-09-17. This card does **not** run a 90-day fishing clock. Mapping-test **MONITOR** dies if a dated primary shows the exemption does not map to Uniswap. Revival of a fee-switch card requires a **new** card that cites that URL (date, parameters, source).
6) **What would change our mind** — Primary-source dated proposal with executable parameters, plus (separately) volume-share series. Hope is not a calendar. Mapping confirmation is not auto-**RESEARCH_PRIORITY**.
7) **Data still needed before thesis.md** — Dated proposal URL (**blocking** for fee-switch). UNI HL funding obs. Mapping test vs PR 2026-90. Stay **MONITOR** / watch_only.
8) **Confidence** — **0.20** (historical Skeptic #22 FAIL haircut ≤ shortlist 0.38 — no dated Uniswap event).

---

## 4. AAVE (Hyperliquid perp) — utilization empty · Quant **DEFER**

1) **Expectation** — Quant SoT **DEFER** (#38) until an obs-linked utilization **baseline** exists. Membership: **watch_only** (PR #15). **Not** a crypto-credit thesis. SEC PR 2026-90 LP dealer exemption on TSV AMM pools does **not** fill that baseline and is **not** Quant **MONITOR**. **No stale HL sizing.** Paper only. **DO NOT SIZE.**
2) **Reasoning** — Higher-for-longer → Aave borrow demand is a **causation leap** (Skeptic #14 / #22): rate path ≠ utilization ≠ revenue. Credit expectation **demoted**. Macro obs (`01M2PCX90PQAP96J62RR6EWQ35`, `01M2PCX91243QK9V8HCCWQFASY`) are **backdrop only**. HL liquidity stamps are **stale lab appendix** (**DO NOT SIZE** / DO NOT TREAT AS LIVE; 429 on refresh — see [appendix](#appendix--stale-hl-lab-snapshot--do-not-size)) — **not** a micro-size license. No AAVE funding obs in known set. Utilization/revenue **not** obs-linked.
3) **Expected path** — **1–5 sessions:** illiquid drift vs majors (**speculative**; not a trade). **This cycle:** **no** utilization/revenue-rise credit expectation. Stay **DEFER** until a baseline exists (core-market utilization print + source dashboard URL + as-of + obs_id or explicit file cite).
4) **Catalysts / checkpoints** — Aave utilization + protocol revenue **prints** (empty); bad-debt monitors (empty). Do not use the rate path as a substitute print. Do not treat PR 2026-90 adjacency as a catalyst.
5) **Invalidation** — **Primary (single-trigger):** Credit-demand / rate→borrow frame is **already dropped**. Any revival without an obs-linked utilization baseline (source + as-of + print) is methodologically invalid. Prior “≥25% from latest dashboard print within 30 days” is **removed** — that baseline was missing, so the trigger was unfalsifiable theater.
6) **What would change our mind** — Obs-linked utilization/revenue series with a **dated baseline**, independent of pure BTC beta. Until then, **DEFER**.
7) **Data still needed before thesis.md** — Utilization baseline (**blocking**). Revenue dashboards obs-linked. Do not size from HL appendix.
8) **Confidence** — **0.18** (historical Skeptic #22 FAIL haircut ≤ shortlist 0.36 — credit demoted; baseline missing).

---

## 5. NVDA (NASDAQ) — AI-infra **PRIMARY** · Quant **DEFER**

1) **Expectation** — Quant SoT **DEFER** (#38). Membership: **in_universe** AI-infra **PRIMARY** expression. Crowded consensus; mispricing angle still empty — **not** “AI demand exists.” Paper only. **DO NOT SIZE.**
2) **Reasoning** — Theme role: **PRIMARY** single-name AI-infra expression (AVGO satellite; SMH **appendix** after Skeptic #22 — see cards 6–7). Theme role ≠ Quant verdict. Post-FOMC multiple already embeds hyperscaler capex hopes (Skeptic: already priced / extreme crowded). Shortlist evidence is Motley Fool (2026-09-13) + MarketBeat compare — **weak secondaries**; conf 0.58 was too high. Macro `01M2PCX90PQAP96J62RR6EWQ35` explains backdrop only. Survive hawkish Fed **only if** hyperscaler capex holds — circular until primary filings prove it. Equity tape is not in Market Memory (Stooq unavailable on last source-health).
3) **Expected path** — **1–5 sessions:** high-beta to AI-narrative headlines; crowded unwind risk on any capex scare (**speculative**). **This cycle:** further upside only with documented mispricing vs consensus guide — gate **empty**, so Quant stays **DEFER**.
4) **Catalysts / checkpoints** — Next hyperscaler capex guides; NVDA data-center revenue / GM vs guide; China/export headlines; power/grid bottleneck trackers.
5) **Invalidation** — **Primary:** A named hyperscaler (MSFT / GOOGL / AMZN / META) **cuts** AI/data-center capex guide in a dated earnings print or 8-K vs prior guide — kill AI-infra primary thesis-pack promotion for this cycle card.
6) **What would change our mind** — Primary 10-Q / transcript extract showing DC revenue/GM beat **and** an explicit mispricing angle (e.g. Street under-modeling attach or supply) vs “demand exists.”
7) **Data still needed before thesis.md** — Latest 10-Q/earnings transcript extracts (replace Fool/MarketBeat); power/grid trackers; single primary invalidation with dated guide lines (Skeptic). Theme priority locked as primary vs AVGO/SMH. Stay **DEFER**.
8) **Confidence** — **0.48** (historical Skeptic haircut ≤ shortlist 0.58 for secondary evidence; process only).

---

## 6. AVGO (NASDAQ) — AI-infra **SATELLITE** · Quant **INSUFFICIENT_DATA**

1) **Expectation** — Quant SoT **INSUFFICIENT_DATA** (#38). Membership: **in_universe** **SATELLITE** to NVDA. Independence of evidence pack required and **not defined**. Paper only. **DO NOT SIZE.**
2) **Reasoning** — Theme role: **SATELLITE** to NVDA (same AI-infra bet — do not double-count as independent residual). SMH is **appendix** (card 7), not a third AI expression (Skeptic #22). Custom AI ASIC + networking attach is consensus alongside NVDA; same Fool article dual-cited (Skeptic: single weak secondary supporting two names). Rate hike “less fatal if backlog cash-converts” — backlog conversion unshown. Macro backdrop same Fed obs; no fabricated name-level obs_ids. Expectations methodology was **INCONCLUSIVE**. Thin equity tape → Quant **INSUFFICIENT_DATA** rather than a forced **DEFER** that pretends the satellite test exists.
3) **Expected path** — **1–5 sessions:** high correlation to NVDA/SMH (**speculative** residual). **This cycle:** satellite residual only if AI line-item and customer-cohort disclosure show **independent** cash-conversion vs NVDA GPU narrative — **empty**, so stay **INSUFFICIENT_DATA**.
4) **Catalysts / checkpoints** — Next earnings AI semiconductor revenue line-item; customer concentration disclosure; VMware/software margin drag monitor.
5) **Invalidation** — **Primary:** Next reported earnings AI semiconductor revenue guide **cut** vs prior company guide — kill satellite thesis-pack promotion (independent of NVDA tape).
6) **What would change our mind** — Primary AI revenue disclosure that is **not** the same Fool/MarketBeat pack as NVDA; evidence of backlog cash-conversion under higher WACC.
7) **Data still needed before thesis.md** — Customer cohort disclosure; next earnings AI line-item; independence from NVDA evidence pack (Skeptic + shortlist). Stay **INSUFFICIENT_DATA**.
8) **Confidence** — **0.42** (historical satellite + shared-weak-evidence haircut ≤ shortlist 0.55; process only).

---

## 7. SMH (NASDAQ ETF) — AI-infra basket **appendix** · Quant **DEFER**

1) **Expectation** — Quant SoT **DEFER** (#38) — parked **duplicate-beta** of NVDA+AVGO, **not** Quant **MONITOR**. Membership: **watch_only** (PR #15). Theme role: AI-infra basket **appendix**. **Dropped from in-universe thesis-priority.** **Not** a basket-outperform / cycle-broadening claim while NVDA (primary) and AVGO (satellite) remain in-universe. Paper only. **DO NOT SIZE.**
2) **Reasoning** — Same AI-infra theme as NVDA+AVGO. Street already uses SMH for that buildout — definitional, not an edge (Skeptic). **Holdings overlap % vs NVDA/AVGO is unpublished** — any xor vs singles is **blocked** until that % exists. **Double-count disclosure:** SMH + NVDA + AVGO triple-counts one theme. QUANT YTD raw vs SPY is **post-selection descriptive, not a promotion argument**. **Removed:** Yahoo + MarketBeat as if they underwrote a basket-outperform pack (weak secondaries). No invented holdings %.
3) **Expected path** — **1–5 sessions:** tracks AI-semi complex (**description**, not edge). **This cycle:** **no** “basket outperforms if buildout broadens beyond NVDA” expectation. Appendix only. Overlap % required before any xor decision. Quant stays **DEFER**.
4) **Catalysts / checkpoints** — Issuer holdings file: NVDA weight, AVGO weight, combined overlap % (**empty — blocking** for any xor). SIA/TSMC are not a substitute for overlap.
5) **Invalidation** — **Primary (single-trigger):** NVDA primary invalidation (named hyperscaler capex cut — card 5) — SMH appendix is **automatically dropped** with the primary (theme overlap; weights still unpublished). There is **no** independent SMH outperform frame. Prior AND-gate (overlap ≥45% **and** NVDA invalidation) **removed** — overlap % does not exist, so that AND was unfalsifiable.
6) **What would change our mind** — Published holdings overlap % vs NVDA/AVGO **and** an explicit xor (SMH **or** singles) or hedge-mandate decision. Until then, stay appendix; **DEFER**.
7) **Data still needed before thesis.md** — Overlap % (**blocking**). Do not restore basket-outperform language while NVDA+AVGO are in-universe. No memory-semi revival via SMH weights.
8) **Confidence** — **0.22** (historical Skeptic #22 FAIL haircut ≤ shortlist 0.52 — appendix only; outperform dropped).

---

## 8. MSFT (NASDAQ) — Azure extract empty · Quant **INSUFFICIENT_DATA**

1) **Expectation** — Quant SoT **INSUFFICIENT_DATA** (#38). Membership: **in_universe**. Azure growth extract **empty** — not an earnings-gated live pack. Paper only. **DO NOT SIZE.**
2) **Reasoning** — Azure AI + quality compounder under higher rates is consensus fortress narrative (already priced / institutional overweight risk). Sheet evidence is **macro-only** (`01M2PCX90PQAP96J62RR6EWQ35`, `01M2PCX91243QK9V8HCCWQFASY`; Fed statement https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm) — **no Azure growth print** on sheet (Skeptic). Higher-for-longer → quality outperforms is factor folklore without MSFT-specific proof here. Methodology **INCONCLUSIVE**. Thin equity tape. Quant **INSUFFICIENT_DATA**.
3) **Expected path** — **1–5 sessions:** quality mega-cap drift with rates (**speculative**). **This cycle:** multiple holds if Azure growth + capex ROI commentary confirm — **empty**, so stay **INSUFFICIENT_DATA**.
4) **Catalysts / checkpoints** — Next earnings Azure growth / Intelligent Cloud; AI capex ROI commentary; FCF/buyback print.
5) **Invalidation** — **Primary:** Azure constant-currency growth decelerates by ≥300 bps QoQ in the next reported quarter vs prior quarter’s disclosed Azure growth — kill earnings-gated thesis-pack promotion.
6) **What would change our mind** — Latest Azure metrics + explicit ROI commentary from transcript showing durability under higher WACC; valuation not solely “fortress narrative.”
7) **Data still needed before thesis.md** — Latest Azure metrics from earnings; buyback/FCF print; numeric Azure deco threshold locked (Skeptic + shortlist). Stay **INSUFFICIENT_DATA**.
8) **Confidence** — **0.44** (historical haircut ≤ shortlist 0.54; process only).

---

## 9. META (NASDAQ) — ads/AI extracts empty · Quant **INSUFFICIENT_DATA**

1) **Expectation** — Quant SoT **INSUFFICIENT_DATA** (#38). Membership: **in_universe**. Ad ARPU / DAU / capex-ROI extracts **empty** — not an earnings-gated live pack. QUANT overlay asof lags peers (2026-09-15). Paper only. **DO NOT SIZE.**
2) **Reasoning** — Ads + AI infra ROI is 2024–26 consensus META story (crowded / already priced). Macro + SEP links only — **zero** ad ARPU / DAU / capex evidence on sheet (Skeptic). Solvency under higher WACC ≠ mispriced upside. Cite Fed/SEP backdrop only: obs_ids above; SEP https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm (2026-09-16). Methodology **INCONCLUSIVE**. Quant **INSUFFICIENT_DATA**.
3) **Expected path** — **1–5 sessions:** high-beta mega-cap to ad/AI headlines (**speculative**). **This cycle:** re-rate only if ad growth + infra ROI prints beat embedded consensus — **empty**; stay **INSUFFICIENT_DATA**.
4) **Catalysts / checkpoints** — Ad ARPU / family DAU; Reality Labs + infra capex guide; regulatory ad-targeting headlines.
5) **Invalidation** — **Primary:** Next earnings ad revenue growth misses company guide **and** management raises (or refuses to cut) infra capex without ROI KPIs — kill ads+AI ROI thesis-pack promotion.
6) **What would change our mind** — Hard extracts of ad/DAU + capex guide showing ROI inflection not already in Street models.
7) **Data still needed before thesis.md** — Latest ad ARPU / family DAU; capex guide extracts (Skeptic hard-gate; shortlist still-need). Confidence on sheet was unsupported. Stay **INSUFFICIENT_DATA**.
8) **Confidence** — **0.38** (historical haircut ≤ shortlist 0.50; process only).

---

## 10. JPM (NYSE) — financials **PRIMARY** / earnings-watch · Quant **DEFER**

1) **Expectation** — Quant SoT **DEFER** (#38). Membership: **in_universe** financials **PRIMARY** by role; **earnings-watch only**. **Not** a SEP-implied NII residual. Cycle residual **empty/speculative** until an explicit SEP-implied vs company NII guide **gap test** exists (what number, source, as-of, pass/fail rule — **not defined; not invented here**). Paper only. **DO NOT SIZE.**
2) **Reasoning** — Theme role: **PRIMARY** financials expression (XLF = **appendix diversifier** role, research priority strictly below JPM — card 11). Theme role ≠ Quant verdict. FF path → NII is a mechanism **family**, not a print. Same-day/next-day after FOMC+SEP, bank NIM / higher-for-longer is the **most obvious** crowded equity read. **No macro→NII causation without prints** (Skeptic #22 FAIL). Cite: FF `01M2PCX8ZJZCKC52NQ03PHNZWE`, FOMC `01M2PCX90PQAP96J62RR6EWQ35`; SEP https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm. **Removed as causation crutch:** JPM AM “higher-for-longer creates opportunity” insight (commentary, not a gap test). NII guide + charge-offs still need. QUANT: no allocation from FOMC; crowded narrative (**ALREADY_PRICED**).
3) **Expected path** — **1–5 sessions:** may already reflect SEP; **no edge** without a fresh NII print (**speculative**). **This cycle:** **no** “NII beats what SEP already priced” claim — that residual is **undefined** (no numeric SEP-implied NII, no company guide extract, no pass/fail rule). Stay **DEFER** / earnings-watch until the gap test is written with sources.
4) **Catalysts / checkpoints** — Next company NII / NIM **guide** (8-K / earnings) — one side of a *future* gap test, not a residual today; NCO / charge-off trend as a credit **monitor**; do not treat curve shape as NII.
5) **Invalidation** — **Primary (single-trigger):** Next reported quarter **NII misses company guide** — kill any promotion from earnings-watch **DEFER** to a higher-for-longer NII residual pack. NCO/charge-offs remain a credit monitor, **not** a second trigger in this card.
6) **What would change our mind** — An explicit gap test: company NII guide (source URL, as-of, figure) vs a stated SEP-implied path mapping (source, as-of, method) with a numeric pass/fail rule. Until that exists, do not revive residual-upside language.
7) **Data still needed before thesis.md** — Latest NII guide extract; SEP-implied mapping method; charge-off trends. Gap test empty = stay **DEFER** / earnings-watch.
8) **Confidence** — **0.36** (historical Skeptic #22 FAIL haircut ≤ shortlist 0.56 — residual undefined; earnings-watch only).

---

## 11. XLF (NYSE Arca ETF) — financials **appendix** · Quant **DEFER**

1) **Expectation** — Quant SoT **DEFER** (#38) — parked **duplicate** of JPM, **not** Quant **MONITOR**. Membership: **watch_only**. Theme role: financials **appendix diversifier**; research priority strictly below JPM primary. **Not** an independent sector pack. Aggregate bank NII / KRE breadth metrics are **not operationalized**. Paper only. **DO NOT SIZE.**
2) **Reasoning** — Theme role: same higher-for-longer financials theme as JPM — **double-count risk is the default** (one theme, two tickers). QUANT JPM–XLF **0.73** (60d aligned-panel, 2026-05-28 → 2026-09-15, pre-FOMC) is a **sample description, not diversifier proof** (corr ≠ causation; not a pair). **Removed:** gomdorieconomic.com blog (2026-04-22) — weak/stale secondary vs 2026-09-17 FOMC (Skeptic). Fed hike obs_ids are backdrop only. Prefer JPM as primary; XLF is a sector-tape **appendix** (breadth / regional divergence) at strictly lower priority.
3) **Expected path** — **1–5 sessions:** tracks JPM/financials complex (**description**, not edge). **This cycle:** **no** “non-JPM banks add breadth” diversifier-value claim — operational breadth (aggregate bank NII series, KRE vs XLF with as-of/source/threshold) is **empty**. Stay **DEFER** until those metrics exist.
4) **Catalysts / checkpoints** — If later operationalized: FDIC/Fed aggregate bank NII; KRE vs XLF with a registered window; regional stress headlines as **monitors**, not a live gate. Live AUM/ADV still need.
5) **Invalidation** — **Primary (single-trigger):** JPM earnings-watch invalidation (next-quarter NII miss vs company guide — card 10) — XLF appendix sleeve is **automatically dropped** with the primary (double-count). No independent XLF pack to kill. Prior KRE ≤−10% / 20d **and** stress-headline gate **removed** (breadth not operationalized).
6) **What would change our mind** — Operational breadth pack (aggregate NII + KRE) with sources/as-of **and** an explicit Principal mandate that XLF is a diversifier at research priority strictly below JPM rather than a double-count. Until then, **DEFER**.
7) **Data still needed before thesis.md** — Aggregate bank NII; KRE series with thresholds; live AUM/ADV confirm. Do not restore blog citations.
8) **Confidence** — **0.24** (historical Skeptic #22 FAIL haircut ≤ shortlist 0.53 — appendix; breadth empty).

---

## 12. XOM (NYSE) — crude tape empty · Quant **INSUFFICIENT_DATA**

1) **Expectation** — Quant SoT **INSUFFICIENT_DATA** (#38). Membership: **in_universe**. Crude strip / inventory / CL tape **not in Memory** — not a crude-gated live pack. Kill “Fed hike → XOM up” shorthand. Paper only. **DO NOT SIZE.**
2) **Reasoning** — Central Skeptic flaw: Fed hikes because inflation sticky **does not** imply XOM upside; oil supply/demand and refining margins dominate. Macro obs (`01M2PCX90PQAP96J62RR6EWQ35`) + Fed statement are **backdrop only**. Oil tape catalyst (supply/geo): https://www.cnbc.com/2026/09/15/oil-prices-saudi-arabia-east-west-pipeline-iran.html (2026-09-15). Need crude strip + inventory + XOM FCF/buyback primary sources — not hike narrative. Methodology PASSed the crude-gated *path*, but Stooq CL was unavailable — Quant prefers **INSUFFICIENT_DATA** over scoring a crude gate with no strip as-of.
3) **Expected path** — **1–5 sessions:** would track crude strip / inventory prints if those prints existed (**speculative** vs rates). **This cycle:** FCF/buyback capacity supports equity if strip holds — **empty**; stay **INSUFFICIENT_DATA**.
4) **Catalysts / checkpoints** — WTI/Brent strip levels; EIA/API inventory; refining margins; XOM production/FCF/buyback guide; windfall-tax headlines.
5) **Invalidation** — **Primary:** Front-month WTI settles below **$60** for **5 consecutive** sessions **or** company withdraws/cuts buyback on FCF miss in next earnings — kill crude-gated thesis-pack promotion.
6) **What would change our mind** — Crude strip + inventory path supportive **and** XOM FCF/buyback primary extract showing capacity not already priced; mechanism via oil, not Fed.
7) **Data still needed before thesis.md** — Latest production/FCF guide; oil inventory prints; crude strip levels with numeric triggers (Skeptic + shortlist). Kill hike→energy shorthand. Stay **INSUFFICIENT_DATA**.
8) **Confidence** — **0.38** (historical haircut ≤ shortlist 0.48; process only).

---

## Quant SoT summary (IMP-008 / #38 — source of truth)

| Quant verdict | Names | Count |
|---|---|---:|
| **DEFER** | BTC, NVDA, JPM, AAVE, SMH, XLF | 6 |
| **MONITOR** | ETH, UNI | 2 |
| **INSUFFICIENT_DATA** | AVGO, MSFT, META, XOM | 4 |
| **RESEARCH_PRIORITY** | — | **0** |
| **REJECT** | — | **0** |
| **Total locked cards** | | **12** |

**Theme roles (membership, not Quant verdicts):** AI-infra — NVDA primary · AVGO satellite · SMH appendix. Financials — JPM earnings-watch primary · XLF appendix (research priority strictly below JPM; double-count default). ETH = BTC-beta **MONITOR**. UNI = PR 2026-90 mapping-test **MONITOR** (not fee-switch **DEFER**). UNI / AAVE / SMH / XLF / ETH = Principal **watch_only**. BTC universe membership card ≠ RQ-20260917-A funding/basis thesis (PR #9).

**Retired priority language:** “conditional,” “watch-only / benchmark + conditional,” “conditional / earnings-gated,” “conditional / crude-gated,” “deferred governance watch” as if it were Quant **DEFER**, “monitor-only” as if it were Quant **MONITOR**. Historical Skeptic #11 revise-status is **not** current priority. Historical Skeptic #22 FAIL patches remain substance; field-1 labels now match Quant SoT.

**Skeptic #22 (historical):** PASS keepers BTC / NVDA / XOM unchanged in substance. FAIL patches: ETH, JPM, XLF, UNI, AAVE, SMH (see changelog). INCONCLUSIVE AVGO / MSFT / META / IBIT not rewritten for methodology in #23 (AVGO has a one-line SMH-appendix cross-ref only). Quant #38 then scored AVGO/MSFT/META/XOM **INSUFFICIENT_DATA**.

**Explicit non-actions:** No thesis folders opened. No orders. No risk approval. No fabricated observation_ids. No invented NII-gap / overlap / utilization numbers. No `universe.yaml` edit. No memory-semi revival. Must-cuts excluded. No new names. **Paper only.** **DO NOT SIZE.** Promote any name to `thesis.md` only after that card’s field 7 gates clear **and** Quant is **RESEARCH_PRIORITY** with Independent Skeptic.

---

## Appendix — stale HL lab snapshot · **DO NOT SIZE**

```
STALE / PARTIAL HYPERLIQUID CACHE
DO NOT SIZE · DO NOT TREAT AS LIVE · APPENDIX ONLY
Capture: 2026-09-17T00:28:03Z (= 2026-09-17 10:28 AEST)
Live refresh RQ-20260917-A: HTTP 429
fundingHistory 24h: UNAVAILABLE (429)
```

Source of record for these stamps: `research/queue/QUANT-20260917-active-calls.md` appendix (historical pack; filename retained). **Not** a 2026-09-18 print. **Not** a sizing input. Card bodies above must not treat dayNtl / OI$ as live.

| Name | dayNtlVlm | OI$ proxy | Treatment |
| --- | --- | --- | --- |
| BTC | $3.05B | $2.90B | appendix / **DO NOT SIZE** |
| ETH | $1.37B | $2.37B | appendix / **DO NOT SIZE** |
| UNI | $31.2M | $57.8M | appendix / **DO NOT SIZE** |
| AAVE | $12.9M | $67.5M | appendix / **DO NOT SIZE** |

Until a **successful** Intel ingest (fresh `metaAndAssetCtxs` + continuous fundingHistory + verified obs payload bytes), these figures stay appendix-only.

**— End membership cards · Quant SoT 2026-09-18 (#38) · IMP-032 language alignment · paper only · DO NOT SIZE —**
