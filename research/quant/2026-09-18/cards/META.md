# Quant Card — META

- **Instrument:** META (`META`)
- **Review date:** 2026-09-18
- **Knowledge watermark (as_of_knowledge):** 2026-09-18T02:00:00+00:00
- **Track(s):** A, B
- **Sector:** mega_quality
- **Benchmark:** MSFT
- **Peers:** MSFT
- **Data-quality status:** stale
- **Labels:** none
- **Verdict:** INSUFFICIENT_DATA
- **Reason code(s):** STALE_OR_PARTIAL_DATA, INSUFFICIENT_HISTORY, NO_CATALYST, THESIS_NOT_FALSIFIABLE, NO_MISPRICING, CORRELATED_EXPOSURE, RECLAIM_UNCONFIRMED
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=no, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=no, single_falsifiable_invalidation=no, acceptable_liquidity=no, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

Ad ARPU / family DAU / capex-ROI extracts are empty. QUANT asof lags peers (2026-09-15). Methodology INCONCLUSIVE. INSUFFICIENT_DATA.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| expectations methodology INCONCLUSIVE: empty fundamental gates + QUANT META lag | research/queue/EXPECTATIONS-20260917-methodology-scorecard.md | 2026-09-17 | Skeptic PR #22 | 0.80 | process artifact |
| QUANT overlay last_close=670.239990234375 asof=2026-09-15 LAG vs equity peers; SPY rel not contemporaneous | research/queue/quant-20260917/metrics_active_and_watch.csv | 2026-09-17T01:15:47+00:00 | QUANT pack run_meta asof_flag | 0.30 | yfinance:META; asof_note LAG_vs_equity_peers |
| call card: zero ad ARPU / DAU / capex evidence on sheet | research/queue/UNIVERSE-20260917-call-cards.md | 2026-09-17 | call cards §9 | 0.70 | membership card |
| Stooq unavailable; no equity ingest | ops/reports/source-health/2026-09-17.md | 2026-09-17T04:51:26+00:00 | source-health | 0.75 | tape gap |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

QUANT short-window rel vs SPY fails as-of discipline until the META lag is fixed (scorecard). Do not score a 2026-09-18 structure regime from a 2026-09-15 overlay.

## Why overlooked

in_universe ads+AI ROI story is 2024–26 consensus; Quant has no contemporaneous tape or extracts.

## Alternative / skeptic case

Skeptic case: solvency under higher WACC is not mispriced upside. Crowded ads+AI narrative is already priced until extracts exist.

## Catalyst / condition to monitor

Next earnings ad revenue vs company guide plus infra capex ROI KPIs. Empty this pass.

## Single invalidation

Call-card primary: next earnings ad revenue growth misses company guide and management raises (or refuses to cut) infra capex without ROI KPIs. Guide lines not extracted.

## Liquidity / execution suitability

ADV not evidenced in Memory this pass.

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=False, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=False, single_falsifiable_invalidation=False, acceptable_liquidity=False, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: STALE_OR_PARTIAL_DATA, INSUFFICIENT_HISTORY, NO_CATALYST, THESIS_NOT_FALSIFIABLE, NO_MISPRICING, CORRELATED_EXPOSURE, RECLAIM_UNCONFIRMED.

Research only. Not a trade instruction, allocation decision, or execution approval.
