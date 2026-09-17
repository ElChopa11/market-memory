# UNIVERSE-20260917 — Intent-level expectation cards (Principal / Don)

| Field | Value |
|---|---|
| **Purpose** | Principal ask — reasoning + expectation behind **LOCKED** universe **membership** (not Quant verdicts) |
| **Date** | 2026-09-17 (Australia/Sydney, AEST) |
| **Status** | Intent-level expectation cards only. Survivors remain **revise-status** until Skeptic PR #11 data gates clear. **Not** theses, not orders, not risk approvals. |
| **Principal membership** | Encoded in `config/universe.yaml`. IMP-005 keys: **in_universe** BTC, NVDA, AVGO, MSFT, META, JPM, XOM · **watch_only** ETH, UNI, AAVE, SMH, XLF (membership kept; no thesis-priority). Pack-era PR #15 listed ETH/XLF under the former `active_calls` key; yaml PR #24 demoted them. This file does **not** edit `universe.yaml`. Memory-semi **killed** (not reopened). |
| **Skeptic cite** | Overall **REVISE** — **0 pass / 12 revise / 8 reject** (artifact: `research/queue/UNIVERSE-20260917-skeptic-review.md` (PR #11)). Must-cuts **HYPE, SOL, XRP, ARB, NEAR, LINK, GLD, LLY** excluded here; retained only as learning records outside this file. |
| **Skeptic #22 FAIL patch** | **2026-09-17** — ETH / JPM / XLF / UNI / AAVE / SMH expectations patched for methodology FAILs (`research/queue/EXPECTATIONS-20260917-methodology-scorecard.md`, PR #22). Changelog: `research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md`. PASS keepers BTC / NVDA / XOM **untouched** (substance). INCONCLUSIVE AVGO / MSFT / META / IBIT out of scope except one-line role notes where a FAIL patch forced a cross-ref. QUANT honesty binds (`QUANT-20260917-active-calls.md`, main): rel ≠ α · HL stale = appendix / DO NOT SIZE · corr ≠ causation. |
| **Locked universe (12)** | Crypto HL: BTC, ETH, UNI, AAVE · Equities: NVDA, AVGO, SMH, MSFT, META, JPM, XLF, XOM |
| **Theme-dedupe honesty** | **NVDA / AVGO / SMH** = one AI-infra theme (primary / satellite / **monitor-only appendix** — SMH dropped from active expectations). **JPM / XLF** = one financials theme (earnings-watch primary / **monitor-only diversifier**, size-cap ≪ JPM; corr ≠ diversifier proof). |
| **Separate intent** | **RQ-20260917-A** BTC funding/basis remains a **separate** workstream — link `research/2026/THESIS-0001-post-fomc-btc-funding/intent.md` (PR #9). The BTC card below is the **universe membership** card, not that thesis. |
| **Honesty bar** | No name is thesis-ready (Skeptic). Calls lean **conditional / watch-only / deferred / monitor**. No fabricated obs_ids. No invented gap/overlap/utilization numbers. Confidence ≤ shortlist; FAIL-patched names haircut further. |

**Macro backdrop (shared, not name edge):** FOMC +25bp → FF 3.75–4.00% (`01M2PCX90PQAP96J62RR6EWQ35`); FF (`01M2PCX8ZJZCKC52NQ03PHNZWE`); IORB 3.90% (`01M2PCX9005R4S8GRPQJP96CRP`); primary credit 4.00% (`01M2PCX90C2J9RPG17CSZDTV3Q`); Reuters/SEP partial (`01M2PCX91243QK9V8HCCWQFASY`); Fed statement https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm (2026-09-16). Senate H.R.3633 cloture fail 49–50 (2026-09-15): https://www.senate.gov/legislative/LIS/roll_call_votes/vote1192/vote_119_2_00234.htm.

---

## 1. BTC (Hyperliquid perp) — liquidity benchmark

1) **Expectation** — **watch-only / benchmark + conditional** (funding / basis / ETF / reg gates). **Not** hawkish-Fed-up. Universe **membership** card only; funding/basis research lives under **RQ-20260917-A** (`research/2026/THESIS-0001-post-fomc-btc-funding/intent.md`, PR #9).
2) **Reasoning** — Deepest HL book (dayNtl ~$3.05B, OI$ ~$2.90B at 2026-09-17T00:28:03Z capture) makes BTC the lab liquidity/funding reference, not an upside seed. Falsifiable drivers if/when data exists: (a) multi-day spot ETF net inflow resume; (b) funding/basis dislocation mean-reverts without OI collapse; (c) legislative path after H.R.3633 cloture fail. Cite MM: funding `01M2PCXAFASC2V0WCGWR0E8MZT`, OI `01M2PCXAFMC3792Y1PQ3H2ACVQ`, mark `01M2PCXAEE4BRXTPMV56SYN56V`, oracle `01M2PCXAEY18W6290P82NECSM7`, mid `01M2PCXACWWCDJRR2GJ20RV7D4`; macro `01M2PCX90PQAP96J62RR6EWQ35`, `01M2PCX91243QK9V8HCCWQFASY`; Senate URL above. Hawkish tape + CLARITY setback are **already public** — do not treat as mispricing.
3) **Expected path** — **1–5 sessions:** range / beta to risk tape; funding stamp is a snapshot, not a forecast (**speculative** without fundingHistory continuity). **This cycle IF thesis holds:** only if ETF multi-day inflows + basis/funding gates clear — otherwise stays benchmark (**speculative**; gates empty).
4) **Catalysts / checkpoints** — Daily ETF net flow prints; HL fundingHistory series vs single stamp; CME basis vs HL; any dated substitute bill calendar post–H.R.3633.
5) **Invalidation** — **Primary (single-trigger):** ≥5 consecutive US trading days of spot BTC ETF **net outflows** (aggregate issuer prints) while HL funding stays ≥ +0.01%/8h with OI$ declining ≥15% from capture baseline — kill universe promotion and RQ-A long-bias frames.
6) **What would change our mind** — Verified multi-day ETF inflow streak + CME/HL basis dislocation with intact OI; or dated legislative revival with corridor volume (not hope after known fail).
7) **Data still needed before thesis.md** — Verified multi-day ETF flow series; HL `fundingHistory` continuity; basis vs CME (Skeptic hard-gate + shortlist still-need). Reclassify language away from cycle-upside until gates clear.
8) **Confidence** — **0.45** (≤ shortlist 0.55; revise / watch-only).

---

## 2. ETH (Hyperliquid perp) — BTC-beta watch

1) **Expectation** — **BTC-beta watch** (`watch_only` membership after yaml PR #24; pack-era listed with in-universe names; **not** a residual/RV long vs BTC; **not** standalone beta long). **Ban α language.** QUANT: raw ETH−BTC is **not** edge (`rel ≠ α`; not β-adjusted).
2) **Reasoning** — HL #2 book (dayNtl ~$1.37B, OI$ ~$2.37B at 2026-09-17T00:28:03Z capture) is **stale lab appendix** (QUANT: DO NOT SIZE; live refresh 429) — explains *why ETH sits next to BTC on the board*, not an upside seed. Only **ETH funding** is MM-linked (`01M2PCPEK2ZXFDKPK0TDZZZ5M4`); OI/mark ULIDs missing from known set. A β-adjusted residual vs BTC over a **named window** plus an L2 fee/activity residual are **not defined** and the evidence pack is **empty**, so the prior RV/outperformance expectation is **demoted** (Skeptic #22 FAIL) rather than given a fake protocol. Hawkish Fed compresses duration (backdrop only). Same macro/Senate backdrop as BTC. Do not invent ETH OI/mark obs_ids.
3) **Expected path** — **1–5 sessions:** tracks BTC (beta **description**, not a trade). Funding skew is **speculative** without OI series. **This cycle:** **no ETH/BTC outperformance expectation** and **no α claim**. Cycle residual **empty/speculative** until a residual protocol exists (named window + β method + as-of + L2 fee/activity residual with sources). QUANT 30d/90d/YTD raw vs BTC (simple diff) must **not** be read as edge.
4) **Catalysts / checkpoints** — ETH ETF multi-day net flows (**monitor**); L2 fee/TVL QoQ (**empty**); staking/fee revenue (**empty**). If a later card defines a β-residual, register window/as-of/method **then** — not here.
5) **Invalidation** — **Primary (single-trigger):** ETH ETF aggregate **net outflows** on ≥5 consecutive US trading days — kill any promotion from BTC-beta watch to an independent or RV-vs-BTC long. Replaces the prior **AND**-gate (raw ETH−BTC ≤−8% over 20d **and** ETF outflows). Raw ETH−BTC is **not** this trigger and is **not** edge.
6) **What would change our mind** — A written residual protocol: β-adjusted ETH vs BTC over a **named** window with as-of, **plus** L2 fee/activity residual from primary dashboards, **plus** ingested ETH OI/mark/fundingHistory. Until then, stay BTC-beta watch.
7) **Data still needed before thesis.md** — Residual protocol definition (blocking for any RV revival); ETH ETF flows; HL ETH OI/mark obs_ids; staking/fee revenue; fundingHistory. Do not revive RV/α language while those are empty.
8) **Confidence** — **0.28** (≤ shortlist 0.50; Skeptic #22 FAIL haircut — demoted from conditional RV; residual protocol empty).

---

## 3. UNI (Hyperliquid perp) — deferred governance watch

1) **Expectation** — **deferred governance watch** — **watch-only membership, not a Quant verdict**. Matches Principal `universe.yaml` **watch-only** (PR #15). **Not** event-gated. **Not** a hawkish-cycle beta long.
2) **Reasoning** — Fee-switch / governance optionality is a **multi-year recycled** narrative; market has priced delays repeatedly (Skeptic #14 reject still stands methodologically). **No dated primary proposal URL** as of this patch (2026-09-17) — therefore **no live event gate**. Prior **90-day** “no proposal → kill” calendar was **undated fishing** (Skeptic #22 FAIL) and is **removed**. HL dayNtl ~$31M (2026-09-17T00:28:03Z capture) is **stale lab appendix** (QUANT: DO NOT SIZE). No UNI funding obs in known set. QUANT 30d/90d bounce is **footnote, not a thesis**. Not “DeFi blue-chip vibes.”
3) **Expected path** — **1–5 sessions:** drift with crypto beta; **no edge** (**speculative**). **This cycle:** **no** binary re-rate / fee-switch expectation. Deferred until a dated primary proposal exists. QUANT raw vs BTC is **not** α.
4) **Catalysts / checkpoints** — A **dated** Uniswap governance proposal **URL** with executable fee-switch parameters would be required to reopen an event card — **none cited**. DEX volume share is **not** a substitute event.
5) **Invalidation** — **Primary (single-trigger):** Event-gated long / binary re-rate frame is **already killed** by absence of a dated primary proposal URL as of 2026-09-17. This card does **not** run a 90-day fishing clock. Revival requires a **new** card that cites that URL (date, parameters, source).
6) **What would change our mind** — Primary-source dated proposal with executable parameters, plus (separately) volume-share series. Hope is not a calendar.
7) **Data still needed before thesis.md** — Dated proposal URL (**blocking**). UNI HL funding obs. Stay deferred / watch-only.
8) **Confidence** — **0.20** (≤ shortlist 0.38; Skeptic #22 FAIL haircut — deferred; no dated event).

---

## 4. AAVE (Hyperliquid perp) — deferred / micro watch

1) **Expectation** — **deferred / micro watch** until an obs-linked utilization **baseline** exists. **Not** a crypto-credit thesis. Matches Principal `universe.yaml` **watch-only** (PR #15). **No stale HL sizing.**
2) **Reasoning** — Higher-for-longer → Aave borrow demand is a **causation leap** (Skeptic #14 / #22): rate path ≠ utilization ≠ revenue. Credit expectation **demoted**. Macro obs (`01M2PCX90PQAP96J62RR6EWQ35`, `01M2PCX91243QK9V8HCCWQFASY`) are **backdrop only**. HL dayNtl ~$13M / OI$ ~$67M from 2026-09-17T00:28:03Z capture are **stale lab appendix** (QUANT: DO NOT SIZE / DO NOT TREAT AS LIVE; 429 on refresh) — **not** a micro-size license. No AAVE funding obs in known set. Utilization/revenue **not** obs-linked.
3) **Expected path** — **1–5 sessions:** illiquid drift vs majors (**speculative**; not a trade). **This cycle:** **no** utilization/revenue-rise credit expectation. Deferred until a baseline exists (core-market utilization print + source dashboard URL + as-of + obs_id or explicit file cite).
4) **Catalysts / checkpoints** — Aave utilization + protocol revenue **prints** (empty); bad-debt monitors (empty). Do not use the rate path as a substitute print.
5) **Invalidation** — **Primary (single-trigger):** Credit-demand / rate→borrow frame is **already dropped**. Any revival without an obs-linked utilization baseline (source + as-of + print) is methodologically invalid. Prior “≥25% from latest dashboard print within 30 days” is **removed** — that baseline was missing, so the trigger was unfalsifiable theater.
6) **What would change our mind** — Obs-linked utilization/revenue series with a **dated baseline**, independent of pure BTC beta. Until then, deferred/micro watch.
7) **Data still needed before thesis.md** — Utilization baseline (**blocking**). Revenue dashboards obs-linked. Do not size from HL appendix.
8) **Confidence** — **0.18** (≤ shortlist 0.36; Skeptic #22 FAIL haircut — credit demoted; baseline missing).

---

## 5. NVDA (NASDAQ) — AI-infra **PRIMARY** expression

1) **Expectation** — **conditional** (crowded consensus; requires mispricing angle — not “AI demand exists”).
2) **Reasoning** — Theme role: **PRIMARY** single-name AI-infra expression (AVGO satellite; SMH **monitor-only appendix** after Skeptic #22 — see cards 6–7). Post-FOMC multiple already embeds hyperscaler capex hopes (Skeptic: already priced / extreme crowded). Shortlist evidence is Motley Fool (2026-09-13) + MarketBeat compare — **weak secondaries**; conf 0.58 was too high. Macro `01M2PCX90PQAP96J62RR6EWQ35` explains backdrop only. Survive hawkish Fed **only if** hyperscaler capex holds — circular until primary filings prove it.
3) **Expected path** — **1–5 sessions:** high-beta to AI-narrative headlines; crowded unwind risk on any capex scare (**speculative**). **This cycle IF thesis holds:** further upside only with documented mispricing vs consensus guide (**speculative** without 10-Q/transcript).
4) **Catalysts / checkpoints** — Next hyperscaler capex guides; NVDA data-center revenue / GM vs guide; China/export headlines; power/grid bottleneck trackers.
5) **Invalidation** — **Primary:** A named hyperscaler (MSFT / GOOGL / AMZN / META) **cuts** AI/data-center capex guide in a dated earnings print or 8-K vs prior guide — kill AI-infra primary long frame for this cycle card.
6) **What would change our mind** — Primary 10-Q / transcript extract showing DC revenue/GM beat **and** an explicit mispricing angle (e.g. Street under-modeling attach or supply) vs “demand exists.”
7) **Data still needed before thesis.md** — Latest 10-Q/earnings transcript extracts (replace Fool/MarketBeat); power/grid trackers; single primary invalidation with dated guide lines (Skeptic). Theme priority locked as primary vs AVGO/SMH.
8) **Confidence** — **0.48** (≤ shortlist 0.58; Skeptic haircut for secondary evidence).

---

## 6. AVGO (NASDAQ) — AI-infra **SATELLITE** to NVDA

1) **Expectation** — **conditional** (satellite; independence of evidence pack required).
2) **Reasoning** — Theme role: **SATELLITE** to NVDA (same AI-infra bet — do not double-count as independent alpha). SMH is **monitor-only appendix** (card 7), not a third active AI expression (Skeptic #22). Custom AI ASIC + networking attach is consensus alongside NVDA; same Fool article dual-cited (Skeptic: single weak secondary supporting two names). Rate hike “less fatal if backlog cash-converts” — backlog conversion unshown. Macro backdrop same Fed obs; no fabricated name-level obs_ids.
3) **Expected path** — **1–5 sessions:** high correlation to NVDA/SMH (**speculative** residual). **This cycle IF thesis holds:** satellite add only if AI line-item and customer-cohort disclosure show **independent** cash-conversion vs NVDA GPU narrative (**speculative**).
4) **Catalysts / checkpoints** — Next earnings AI semiconductor revenue line-item; customer concentration disclosure; VMware/software margin drag monitor.
5) **Invalidation** — **Primary:** Next reported earnings AI semiconductor revenue guide **cut** vs prior company guide — kill satellite long frame (independent of NVDA tape).
6) **What would change our mind** — Primary AI revenue disclosure that is **not** the same Fool/MarketBeat pack as NVDA; evidence of backlog cash-conversion under higher WACC.
7) **Data still needed before thesis.md** — Customer cohort disclosure; next earnings AI line-item; independence from NVDA evidence pack (Skeptic + shortlist).
8) **Confidence** — **0.42** (≤ shortlist 0.55; satellite + shared-weak-evidence haircut).

---

## 7. SMH (NASDAQ ETF) — monitor-only AI-infra basket **appendix**

1) **Expectation** — **monitor-only AI-infra basket appendix**. **Dropped from in-universe thesis-priority expectations.** Matches Principal `universe.yaml` **watch-only** (PR #15). **Not** a basket-outperform / cycle-broadening claim while NVDA (primary) and AVGO (satellite) remain in-universe.
2) **Reasoning** — Same AI-infra theme as NVDA+AVGO. Street already uses SMH for that buildout — definitional, not an edge (Skeptic). **Holdings overlap % vs NVDA/AVGO is unpublished** — any xor vs singles is **blocked** until that % exists. **Double-count disclosure:** SMH + NVDA + AVGO triple-counts one theme. QUANT YTD raw vs SPY is **post-selection descriptive, not a promotion argument**. **Removed:** Yahoo + MarketBeat as if they underwrote a basket-outperform call (weak secondaries). No invented holdings %.
3) **Expected path** — **1–5 sessions:** tracks AI-semi complex (**description**, not edge). **This cycle:** **no** “basket outperforms if buildout broadens beyond NVDA” expectation. Appendix/monitor only. Overlap % required before any xor decision.
4) **Catalysts / checkpoints** — Issuer holdings file: NVDA weight, AVGO weight, combined overlap % (**empty — blocking** for any xor). SIA/TSMC are not a substitute for overlap.
5) **Invalidation** — **Primary (single-trigger):** NVDA primary invalidation (named hyperscaler capex cut — card 5) — SMH appendix is **automatically dropped** with the primary (theme overlap; weights still unpublished). There is **no** independent SMH outperform frame. Prior AND-gate (overlap ≥45% **and** NVDA invalidation) **removed** — overlap % does not exist, so that AND was unfalsifiable.
6) **What would change our mind** — Published holdings overlap % vs NVDA/AVGO **and** an explicit xor (SMH **or** singles) or hedge-mandate decision. Until then, stay appendix; **drop from active expectations**.
7) **Data still needed before thesis.md** — Overlap % (**blocking**). Do not restore basket-outperform language while NVDA+AVGO are active. No memory-semi revival via SMH weights.
8) **Confidence** — **0.22** (≤ shortlist 0.52; Skeptic #22 FAIL haircut — appendix only; outperform dropped).

---

## 8. MSFT (NASDAQ) — earnings-gated quality

1) **Expectation** — **conditional / earnings-gated**.
2) **Reasoning** — Azure AI + quality compounder under higher rates is consensus fortress narrative (already priced / institutional overweight risk). Sheet evidence is **macro-only** (`01M2PCX90PQAP96J62RR6EWQ35`, `01M2PCX91243QK9V8HCCWQFASY`; Fed statement https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm) — **no Azure growth print** on sheet (Skeptic). Higher-for-longer → quality outperforms is factor folklore without MSFT-specific proof here.
3) **Expected path** — **1–5 sessions:** quality mega-cap drift with rates (**speculative**). **This cycle IF thesis holds:** multiple holds if Azure growth + capex ROI commentary confirm (**speculative** until earnings extract).
4) **Catalysts / checkpoints** — Next earnings Azure growth / Intelligent Cloud; AI capex ROI commentary; FCF/buyback print.
5) **Invalidation** — **Primary:** Azure constant-currency growth decelerates by ≥300 bps QoQ in the next reported quarter vs prior quarter’s disclosed Azure growth — kill earnings-gated long frame.
6) **What would change our mind** — Latest Azure metrics + explicit ROI commentary from transcript showing durability under higher WACC; valuation not solely “fortress narrative.”
7) **Data still needed before thesis.md** — Latest Azure metrics from earnings; buyback/FCF print; numeric Azure deco threshold locked (Skeptic + shortlist).
8) **Confidence** — **0.44** (≤ shortlist 0.54).

---

## 9. META (NASDAQ) — earnings-gated ads + AI ROI

1) **Expectation** — **conditional / earnings-gated**.
2) **Reasoning** — Ads + AI infra ROI is 2024–26 consensus META story (crowded / already priced). Macro + SEP links only — **zero** ad ARPU / DAU / capex evidence on sheet (Skeptic). Solvency under higher WACC ≠ mispriced upside. Cite Fed/SEP backdrop only: obs_ids above; SEP https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm (2026-09-16).
3) **Expected path** — **1–5 sessions:** high-beta mega-cap to ad/AI headlines (**speculative**). **This cycle IF thesis holds:** re-rate only if ad growth + infra ROI prints beat embedded consensus (**speculative**; still need).
4) **Catalysts / checkpoints** — Ad ARPU / family DAU; Reality Labs + infra capex guide; regulatory ad-targeting headlines.
5) **Invalidation** — **Primary:** Next earnings ad revenue growth misses company guide **and** management raises (or refuses to cut) infra capex without ROI KPIs — kill ads+AI ROI long frame.
6) **What would change our mind** — Hard extracts of ad/DAU + capex guide showing ROI inflection not already in Street models.
7) **Data still needed before thesis.md** — Latest ad ARPU / family DAU; capex guide extracts (Skeptic hard-gate; shortlist still-need). Confidence on sheet was unsupported.
8) **Confidence** — **0.38** (≤ shortlist 0.50).

---

## 10. JPM (NYSE) — financials **PRIMARY** / earnings-watch only

1) **Expectation** — **earnings-watch only** (still financials **PRIMARY** vs XLF by role; **not** a SEP-implied NII residual long). Cycle residual **empty/speculative** until an explicit SEP-implied vs company NII guide **gap test** exists (what number, source, as-of, pass/fail rule — **not defined; not invented here**).
2) **Reasoning** — Theme role: **PRIMARY** financials expression (XLF = **monitor-only diversifier**, size-cap ≪ JPM — card 11). FF path → NII is a mechanism **family**, not a print. Same-day/next-day after FOMC+SEP, bank NIM / higher-for-longer is the **most obvious** crowded equity read. **No macro→NII causation without prints** (Skeptic #22 FAIL). Cite: FF `01M2PCX8ZJZCKC52NQ03PHNZWE`, FOMC `01M2PCX90PQAP96J62RR6EWQ35`; SEP https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm. **Removed as causation crutch:** JPM AM “higher-for-longer creates opportunity” insight (commentary, not a gap test). NII guide + charge-offs still need. QUANT: no allocation from FOMC; crowded narrative.
3) **Expected path** — **1–5 sessions:** may already reflect SEP; **no edge** without a fresh NII print (**speculative**). **This cycle:** **no** “NII beats what SEP already priced” claim — that residual is **undefined** (no numeric SEP-implied NII, no company guide extract, no pass/fail rule). Earnings-watch only until the gap test is written with sources.
4) **Catalysts / checkpoints** — Next company NII / NIM **guide** (8-K / earnings) — one side of a *future* gap test, not a residual today; NCO / charge-off trend as a credit **monitor**; do not treat curve shape as NII.
5) **Invalidation** — **Primary (single-trigger):** Next reported quarter **NII misses company guide** — kill any promotion from earnings-watch to a higher-for-longer NII residual long. NCO/charge-offs remain a credit monitor, **not** a second trigger in this card.
6) **What would change our mind** — An explicit gap test: company NII guide (source URL, as-of, figure) vs a stated SEP-implied path mapping (source, as-of, method) with a numeric pass/fail rule. Until that exists, do not revive residual-upside language.
7) **Data still needed before thesis.md** — Latest NII guide extract; SEP-implied mapping method; charge-off trends. Gap test empty = stay earnings-watch.
8) **Confidence** — **0.36** (≤ shortlist 0.56; Skeptic #22 FAIL haircut — residual undefined; earnings-watch only).

---

## 11. XLF (NYSE Arca ETF) — financials **monitor-only diversifier**

1) **Expectation** — **monitor-only diversifier** to JPM. Research / any future size-cap **≪ JPM primary**. **Not** an independent sector long. Aggregate bank NII / KRE breadth metrics are **not operationalized** — no diversifier-value expectation until they are.
2) **Reasoning** — Theme role: same higher-for-longer financials theme as JPM — **double-count risk is the default** (one theme, two tickers). QUANT JPM–XLF **0.73** (60d aligned-panel, 2026-05-28 → 2026-09-15, pre-FOMC) is a **sample description, not diversifier proof** (corr ≠ causation; not a pair trade). **Removed:** gomdorieconomic.com blog (2026-04-22) — weak/stale secondary vs 2026-09-17 FOMC (Skeptic). Fed hike obs_ids are backdrop only. Prefer JPM as primary; XLF is a sector-tape **monitor** (breadth / regional divergence) at strictly lower priority.
3) **Expected path** — **1–5 sessions:** tracks JPM/financials complex (**description**, not edge). **This cycle:** **no** “non-JPM banks add breadth” diversifier-value claim — operational breadth (aggregate bank NII series, KRE vs XLF with as-of/source/threshold) is **empty**. Monitor-only until those metrics exist.
4) **Catalysts / checkpoints** — If later operationalized: FDIC/Fed aggregate bank NII; KRE vs XLF with a registered window; regional stress headlines as **monitors**, not a live gate. Live AUM/ADV still need.
5) **Invalidation** — **Primary (single-trigger):** JPM earnings-watch invalidation (next-quarter NII miss vs company guide — card 10) — XLF monitor sleeve is **automatically dropped** with the primary (double-count). No independent XLF long frame to kill. Prior KRE ≤−10% / 20d **and** stress-headline gate **removed** (breadth not operationalized).
6) **What would change our mind** — Operational breadth pack (aggregate NII + KRE) with sources/as-of **and** an explicit Principal mandate that XLF is a diversifier at size ≪ JPM rather than a double-count. Until then, monitor-only.
7) **Data still needed before thesis.md** — Aggregate bank NII; KRE series with thresholds; live AUM/ADV confirm. Do not restore blog citations.
8) **Confidence** — **0.24** (≤ shortlist 0.53; Skeptic #22 FAIL haircut — monitor-only; breadth empty).

---

## 12. XOM (NYSE) — conditional / crude-gated

1) **Expectation** — **conditional / crude-gated**. Kill “Fed hike → XOM up” shorthand.
2) **Reasoning** — Central Skeptic flaw: Fed hikes because inflation sticky **does not** imply XOM upside; oil supply/demand and refining margins dominate. Macro obs (`01M2PCX90PQAP96J62RR6EWQ35`) + Fed statement are **backdrop only**. Oil tape catalyst (supply/geo): https://www.cnbc.com/2026/09/15/oil-prices-saudi-arabia-east-west-pipeline-iran.html (2026-09-15). Need crude strip + inventory + XOM FCF/buyback primary sources — not hike narrative.
3) **Expected path** — **1–5 sessions:** tracks crude strip / inventory prints (**speculative** vs rates). **This cycle IF thesis holds:** FCF/buyback capacity supports equity if strip holds (**speculative** without production/FCF guide).
4) **Catalysts / checkpoints** — WTI/Brent strip levels; EIA/API inventory; refining margins; XOM production/FCF/buyback guide; windfall-tax headlines.
5) **Invalidation** — **Primary:** Front-month WTI settles below **$60** for **5 consecutive** sessions **or** company withdraws/cuts buyback on FCF miss in next earnings — kill crude-gated long frame.
6) **What would change our mind** — Crude strip + inventory path supportive **and** XOM FCF/buyback primary extract showing capacity not already priced; mechanism via oil, not Fed.
7) **Data still needed before thesis.md** — Latest production/FCF guide; oil inventory prints; crude strip levels with numeric triggers (Skeptic + shortlist). Kill hike→energy shorthand.
8) **Confidence** — **0.38** (≤ shortlist 0.48).

---

## Expectation-mix summary (for Principal)

| Expectation type | Names | Count |
|---|---|---:|
| watch-only / benchmark (+ conditional gates) | BTC | 1 |
| BTC-beta watch (watch_only membership; no RV/α) | ETH | 1 |
| earnings-watch only (financials primary; residual empty) | JPM | 1 |
| monitor-only diversifier (size-cap ≪ JPM) | XLF | 1 |
| deferred governance watch (watch-only membership; not a Quant verdict) | UNI | 1 |
| deferred / micro watch (not credit) | AAVE | 1 |
| monitor-only AI-infra basket appendix (dropped from in-universe thesis-priority expectations) | SMH | 1 |
| conditional (PASS / INCONCLUSIVE keepers; substance unpatched) | NVDA, AVGO, MSFT, META, XOM | 5 |
| long-bias (aggressive) | — | **0** |
| **Total locked cards** | | **12** |

**Theme roles:** AI-infra — NVDA primary · AVGO satellite · SMH monitor-only appendix (not an in-universe basket-outperform). Financials — JPM earnings-watch primary · XLF monitor-only diversifier (≪ JPM; double-count default). ETH = BTC-beta watch (QUANT rel≠α). UNI / AAVE / SMH = Principal watch-only (`universe.yaml` PR #15). BTC universe membership card ≠ RQ-20260917-A funding/basis thesis (PR #9).

**Skeptic #22:** PASS keepers BTC / NVDA / XOM unchanged in substance. FAIL patches: ETH, JPM, XLF, UNI, AAVE, SMH (see changelog). INCONCLUSIVE AVGO / MSFT / META / IBIT not rewritten (AVGO has a one-line SMH-appendix cross-ref only).

**Explicit non-actions:** No thesis folders opened. No orders. No risk approval. No fabricated observation_ids. No invented NII-gap / overlap / utilization numbers. No `universe.yaml` edit. No memory-semi revival. Must-cuts excluded. Promote any name to `thesis.md` only after that card’s field 7 gates clear.

**— End call cards · 2026-09-17 AEST · Principal / Don · Skeptic #22 FAIL patch —**
