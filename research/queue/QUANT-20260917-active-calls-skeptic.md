# Skeptic review — QUANT-20260917 active-calls pack (methodology)

| Field | Value |
|---|---|
| **Artifact under review** | `research/queue/QUANT-20260917-active-calls.md` + `research/queue/quant-20260917/` |
| **Source PR** | https://github.com/ElChopa11/market-memory/pull/19 · branch `cursor/quant-20260917-active-calls-aa38` |
| **Reviewer** | Skeptic (independent of Research author) |
| **Reviewed at** | 2026-09-17 (Australia/Sydney, AEST) |
| **Scope** | **Methodology only** — look-ahead, cherry-picked windows, survivorship, stale HL/429 misuse, correlation≠causation, overclaiming from partial data. Not a trade review. |
| **Stance** | Prefer **revise / reject** on method. No rubber stamps. No trades. No credentials. |

## Verdict summary

| Object | Verdict |
|---|---|
| **Pack overall (methodology)** | **revise** |
| **Price/vol/return pipeline** (`build_quant_pack.py`) | **revise** |
| **60d corr module** | **revise** |
| **HL liquidity block (stale/429)** | **reject as sizing / concurrent input** · **revise as labeled appendix** |
| **Macro “regime implication” paragraph** | **reject** (causal overclaim) |
| **Honesty / gap labeling** | **pass** (narrow — disclosure quality only) |

| Count lens | pass | revise | reject |
|---|---:|---:|---:|
| Method objects above (excl. overall) | 1 | 2 | 2 |
| **Overall pack** | — | **1** | — |

**Overall: REVISE** — Reproducible script, run_meta, labeled 429/stale, “not a trade,” and per-name Skeptic honesty lines are real process wins. They do **not** clear a methodology pass: **as-of fractures**, **unregistered windows**, **stale HL sitting in primary liquidity columns**, **simple-diff “relative” returns read like alpha**, **corr truncated by META NaN without design disclosure**, and a **hawkish regime implication** that smuggles causation from a pre-FOMC corr window.

**Hard rule:** Do **not** use this pack for sizing, paper entry, or thesis promotion until revise items land. No trades from this review.

---

## Checklist (Don’s assign)

1. Look-ahead / as-of leakage
2. Cherry-picked windows
3. Survivorship / selection conditioning
4. Stale HL + HTTP 429 misuse
5. Correlation ≠ causation
6. Overclaiming from partial data

---

## Cross-cutting findings

1. **Disclosure ≠ safety.** Labeling “stale/partial,” “speculative,” and “not a trade” is necessary and mostly well done. It does not stop a downstream reader from treating the summary table as a concurrent dashboard.
2. **Mixed clocks in one table.** HL liquidity @ **2026-09-17T00:28:03Z**, equity ADV @ **00:49:39Z**, yfinance equities mostly **asof 2026-09-16**, META **2026-09-15**, crypto spot **2026-09-17**, pack written **11:18 AEST**. Presenting Liquidity | RV | Returns | Rel in one row implies concurrency it does not have.
3. **Post-FOMC narrative on pre-FOMC dependence structure.** Corr window ends **2026-09-15**; FOMC is **2026-09-16**. Macro regime note then interprets clusters as if they inform the hawkish tape. That is look-ahead of *interpretation* even when the matrix numbers are “just history.”
4. **Relative return ≠ residual alpha.** `name total return − bench total return` ignores β. ETH “+20.1% vs BTC / 3m” and MSFT “+24.0% vs SPY / 3m” will be misread as edge. Require β-adjusted or labeled **raw outperformance only**.
5. **√365 vs √252 in one glance table** overclaims cross-asset RV comparability. Separate crypto/equity vol panels or annotate non-comparability.

---

## 1. Look-ahead / as-of leakage — **revise**

| Issue | Detail | Required fix |
|---|---|---|
| **Mixed as-of across names** | META series ends 2026-09-15 (NaN auto-adjust on 2026-09-16); most equities 2026-09-16; crypto 2026-09-17 | Pin a single **pack as-of knowledge** timestamp; drop or flag names that cannot meet it; do not silent-lag META inside “active” peers |
| **Corr end < FOMC** | `corr.end = 2026-09-15` while pack discusses 2026-09-16 hike | Either extend corr through first post-FOMC bar when data exist, **or** explicitly title matrix **“pre-FOMC 60d dependence (ends 2026-09-15)”** and ban regime inference from it |
| **Stale HL + fresh returns** | dayNtl/OI from 10:28 AEST stamp next to RV/returns from 11:15 AEST run | Move HL block to **Appendix: stale lab snapshot**; never same summary grid as live price metrics |
| **ADV scan ≠ yfinance last** | Pack admits scan last/prevClose may differ from series last | Stop blending ADV notional with series last into one “liquidity” story without a reconciliation row |
| **YTD uses path after selection** | Locked universe already chosen; YTD printed as if descriptive support | Label **post-selection descriptive only**; ban using YTD/rel windows to justify lock |

**Look-ahead verdict:** No classic future-return-in-feature bug in `build_quant_pack.py` (returns are trailing). Leakage is **as-of / interpretation look-ahead** — still disqualifying for promotion use.

---

## 2. Cherry-picked windows — **revise**

| Issue | Detail | Required fix |
|---|---|---|
| **Unregistered 20/60/21/63/30/90** | No sensitivity, no pre-reg, no alternate windows | Publish ≥1 robustness set (e.g. 10/40/120) or state “arbitrary dashboard defaults — not research design” in the TLDR |
| **Corr = last 60 after inner-join** | Window end dictated by META hole / incomplete panel, not economic design | Disclose: “n_obs=60 truncated by META as-of 2026-09-15”; show how many bars dropped for crypto weekend inner-join |
| **UNI 1m +103% / vs BTC +85%** | Driven by bounce from ~$3.20 (2026-08-14) — pack warns not a thesis, still centers huge prints in appendix | Cap watch appendix to liquidity + RV/MDD; move extreme return prints to footnote or omit |
| **YTD calendar year** | Economic regimes ≠ Jan 1 | Add regime-relative window (e.g. since FOMC-1) as peer, or demote YTD |

**Cherry-pick verdict:** Defaults are conventional but **unjustified**. Conventional ≠ registered.

---

## 3. Survivorship / selection conditioning — **revise**

| Issue | Detail | Required fix |
|---|---|---|
| **Active set = post-Skeptic survivors** | Packing metrics only on locked names cannot validate the selection | Header must say: **conditioned on Principal lock after Skeptic #11/#14 — not an evaluation of the selection rule** |
| **SMH YTD +46% / +35% vs SPY while watch-only** | Invites “survivorship regret / should have kept” narrative | Either omit YTD for watch names or hard-ban promotion language; keep liquidity only |
| **UNI Kraken history starts 2024-09-27** vs peers 2024-09-17 | Vendor switch shortens history | Flag shorter sample; do not compare MDD/YTD to yfinance crypto peers without alignment note |
| **No dead-name panel** | Must-cuts absent (per brief) — fine for scope, bad if someone cites pack as “universe quant” | Title must remain **active-calls pack**, never “universe quant” |

---

## 4. Stale HL / HTTP 429 misuse — **reject as primary input; revise as appendix**

**What Research did right:** Labeled stale/partial; documented live refresh **429**; fundingHistory unavailable; lab paths omitted; RQ-A cited.

**What still fails:**

1. **Primary one-pagers and summary table lead with stale dayNtl/OI$** as “Liquidity.” That is the highest-misuse surface in the pack.
2. **Instant funding from the stale stamp** is paired with MM obs_id cites while docs/ops TSV payloads are **unavailable via gh** — ID citation without verifiable payload is **provenance theater**.
3. **429 absence of fundingHistory** is correctly blocking for thesis — but the pack still centers microstructure that could not be refreshed. Do not let stale HL substitute for the missing series.

**Required:**
- HL block → appendix only, banner **DO NOT SIZE / DO NOT TREAT AS LIVE**.
- Remove HL columns from active summary table until a successful refresh with obs_ids lands.
- funding / OI rows: either verified MM payload bytes or **unavailable** — not “cite ID + lab JSON we couldn’t re-read.”

**429 misuse verdict:** Not fabricating numbers; **mis-placing** failed-refresh data into live-looking slots. Reject that placement.

---

## 5. Correlation ≠ causation — **revise pack; reject regime paragraph**

| Claim surface | Problem | Fix |
|---|---|---|
| Corr matrix “Read” (BTC–ETH, JPM–XLF, XOM neg vs semis) | Fine as **description** of one 60d sample | Keep; add “no hedge ratio / no stability claim”; no CIs |
| **Macro regime implication:** higher real rates favor cash-flow/NII/energy frames over crypto beta / AI multiples | Causal leap from descriptive corr + public macro | **Delete or rewrite** to: “Macro is backdrop only; corr window is pre-FOMC; **no** allocation implication from this pack.” |
| NVDA–AVGO 0.46 as “co-movement not identity” | Soft OK | Add: not a license to hold both without residual study (call-cards already flagged) |
| Using XOM’s negative corr as support for energy sleeve under hawkish Fed | Classic corr-as-causation (Skeptic #11/#14 on XOM) | Explicit ban |

**Reject:** the regime-implication paragraph as written. Descriptive macro table + obs_ids may stay.

---

## 6. Overclaiming from partial data — **revise**

| Overclaim | Why | Fix |
|---|---|---|
| Simple-diff rel returns as “Rel (bench)” | Looks like alpha; not β-adjusted | Rename **raw outperformance (not α)**; or add β-residual column with method |
| MSFT “60d vol vs 20d = regime shift” | Two scalars ≠ regime identification | Delete “regime shift”; say “RV20≪RV60 in this sample” |
| ETH trailing outperformance vs BTC in active one-pager | Honesty caveat buried under big numbers | Demote rel prints; require flow/L2 gates (already known) before centering |
| Cross-asset RV table | √365 vs √252 | Split tables or annotate |
| Corr n=60, 9 names, weekend drop | Effective DF thin; no HAC/CI | Report n_obs, weekday-only note; “point estimate only” |
| ADV notional = last × ADV shares from different snap | Partial | Single-source ADV or omit notional |
| Pack as “what unlocks a real thesis” while publishing full active dashboards | Soft-promotes readiness | Keep gap table; shrink one-pagers to method-safe fields only (asof, RV, MDD, source) until HL live |

---

## Script-level notes (`build_quant_pack.py`)

**Credit:** Clear docstring; no silent fills; errors list; Kraken fallback explicit; run_meta versions; reproducible CSV outputs.

**Revise items in code/docs:**
1. Document that corr `dropna(how="any")` across 9 names **drops crypto weekends** and any name with a hole (META) truncates everyone’s window.
2. Do not imply HL is in-script (README already says ADV/HL not refreshed by script — good); pack markdown must match that boundary visually.
3. Consider aligning all series to a common last timestamp before computing cross-name relative windows (META lag biases short-window comps).
4. `total_return(..., days)` uses bar counts not calendar — OK if labeled **N bars**, not “1m/3m” months (crypto 30/90 ≠ equity 21/63 “month” language). Rename to **21d/63d (eq) · 30d/90d (crypto)** everywhere (pack TLDR already approximates; summary headers still say 1m/3m).

---

## What would earn revise→pass (methodology)

1. Single pack `as_of_knowledge`; names that miss it flagged or dropped.
2. HL stale data appendix-only; summary table HL-free until live ingest.
3. Regime-implication paragraph removed; corr titled pre-FOMC if end < hike.
4. Rel returns relabeled raw / or β-adjusted with method.
5. Window choices registered or explicitly “dashboard defaults, not design.”
6. META NaN truncation disclosed in corr meta (and preferably fixed via vendor).
7. No YTD-as-justification for lock; survivorship header present.
8. RV cross-asset comparability caveat or split panels.

Until then: **methodology revise**; **reject** use for trades/sizing/promotion.

---

## Explicit non-actions

- No trades recommended or discouraged beyond “do not trade this pack.”
- No risk approval.
- No trading credentials accessed.
- No universe expand / no must-cut reopen.
- Memory-semi (#17/#18) remains Principal-killed — out of scope here.

**Signed:** Skeptic · 2026-09-17 · overall methodology **revise** · HL-as-primary-liquidity **reject** · regime-implication paragraph **reject** · disclosure quality **pass** (narrow)
