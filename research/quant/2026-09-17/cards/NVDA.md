# Quant Card — NVDA

- **Instrument:** NVDA (`NVDA`)
- **Review date:** 2026-09-17
- **Knowledge watermark (as_of_knowledge):** 2026-09-17T02:42:00+00:00
- **Track(s):** A, B
- **Sector:** us_mega
- **Benchmark:** SPX
- **Peers:** QQQ, GOOG, TSLA
- **Data-quality status:** ok
- **Labels:** none
- **Verdict:** DEFER
- **Reason code(s):** RECLAIM_UNCONFIRMED, NO_MISPRICING, CORRELATED_EXPOSURE, NO_CATALYST, THESIS_NOT_FALSIFIABLE
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=yes, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=no, single_falsifiable_invalidation=no, acceptable_liquidity=yes, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

Session vs peers is ordinary on this one print.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| session print last=213.9 chg=1.73 chg%=+0.82% | principal_watchlist_screenshot | 2026-09-17T02:42:00Z | IMP-001 screenshots; clock_on_image=false | 0.45 | fixture/watchlist snapshot; not fabricated |
| overlay last_close=213.899994 ret_short=-4.83% rel_short=-2.42% asof=2026-09-16 | yfinance:NVDA | 2026-09-17T11:15:47.495030+10:00 | 2026-09-17T11:15:47.495030+10:00 | 0.70 | QUANT pack / series overlay; clocks are not mixed with the screenshot print |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

Session vs last print: +0.82% (one session; not a structure regime). Series overlay is descriptive (raw vs benchmark difference, not alpha, not residual). Bullish reclaim is unconfirmed: needs prior breakdown level, reclaim of that level, and hold ≥ 2 sessions. A one-day bounce is not a reclaim. Overlay RV20=0.45477396424199784 RV60=0.40383567256580905 MDD=-0.20214384555482312 (native series; not cross-asset comparable). Session vs peer median (us_mega peers QQQ, GOOG, TSLA): +0.82% vs median +0.03% (gap +0.79 pp). This is a relative-value observation, not ARBITRAGE.

## Why overlooked

Already in locked ingest membership; board still requires an anomaly + invalidation before any thesis pack.

## Alternative / skeptic case

Skeptic case: the session print is noise, peer grouping is operational not fundamental, and any overlay difference is raw vs benchmark (not alpha). Duplicate crypto/tech beta is the default.

## Catalyst / condition to monitor

unknown — not in snapshot; not fabricated

## Single invalidation

unknown — not in snapshot; not fabricated

## Liquidity / execution suitability

Liquidity acceptable for research follow-up (not an execution approval).

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=True, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=False, single_falsifiable_invalidation=False, acceptable_liquidity=True, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: RECLAIM_UNCONFIRMED, NO_MISPRICING, CORRELATED_EXPOSURE, NO_CATALYST, THESIS_NOT_FALSIFIABLE.

Research only. Not a trade instruction, allocation decision, or execution approval.
