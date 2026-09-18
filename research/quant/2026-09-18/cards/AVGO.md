# Quant Card — AVGO

- **Instrument:** AVGO (`AVGO`)
- **Review date:** 2026-09-18
- **Knowledge watermark (as_of_knowledge):** 2026-09-18T02:00:00+00:00
- **Track(s):** A, B
- **Sector:** ai_infra
- **Benchmark:** NVDA
- **Peers:** NVDA, SMH
- **Data-quality status:** partial
- **Labels:** none
- **Verdict:** INSUFFICIENT_DATA
- **Reason code(s):** STALE_OR_PARTIAL_DATA, DUPLICATE_BETA, CORRELATED_EXPOSURE, NO_MISPRICING, NO_CATALYST, THESIS_NOT_FALSIFIABLE, RECLAIM_UNCONFIRMED
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=no, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=no, single_falsifiable_invalidation=no, acceptable_liquidity=no, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

No independent cash-conversion residual vs NVDA is defined. Expectations methodology was INCONCLUSIVE. Thin equity tape → INSUFFICIENT_DATA rather than a forced DEFER that pretends the satellite test exists.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| expectations methodology INCONCLUSIVE: satellite residual named but not specified | research/queue/EXPECTATIONS-20260917-methodology-scorecard.md | 2026-09-17 | Skeptic PR #22 | 0.80 | process artifact |
| call card: independence of evidence pack required; shared weak secondary with NVDA | research/queue/UNIVERSE-20260917-call-cards.md | 2026-09-17 | FAIL-patch cross-ref | 0.70 | membership card; not a Quant verdict |
| QUANT overlay last_close=339.510009765625 asof=2026-09-16 rel_short=-11.08pp vs SPY (simple-diff, not alpha) | research/queue/quant-20260917/metrics_active_and_watch.csv | 2026-09-17T01:15:47+00:00 | QUANT pack | 0.45 | yfinance:AVGO; not a 2026-09-18 print; raw vs SPY is not a residual vs NVDA |
| no AVGO card on 2026-09-17 screenshot board; Stooq unavailable | ops/reports/source-health/2026-09-17.md | 2026-09-17T04:51:26+00:00 | source-health + prior board coverage | 0.75 | name was absent from screenshot universe |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

QUANT NVDA–AVGO 0.46 (pre-FOMC 60d aligned panel, ends 2026-09-15) is a sample description, not two-name license. No regression window or AI line-item extract. SMH appendix is not a third expression.

## Why overlooked

in_universe satellite to NVDA. Satellite status is membership role, not a residual.

## Alternative / skeptic case

Skeptic case: same AI-infra bet as NVDA; backlog cash-conversion under higher WACC is unshown. Treating overlay underperformance vs SPY as independence would violate rel≠α.

## Catalyst / condition to monitor

Next earnings AI semiconductor revenue line-item vs prior company guide. Empty this pass.

## Single invalidation

Call-card primary: next reported earnings AI semiconductor revenue guide cut vs prior company guide. Guide extract not on this board, so the trigger cannot be scored.

## Liquidity / execution suitability

ADV not evidenced in Memory this pass — do not treat QUANT last_close as liquidity proof.

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=False, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=False, single_falsifiable_invalidation=False, acceptable_liquidity=False, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: STALE_OR_PARTIAL_DATA, DUPLICATE_BETA, CORRELATED_EXPOSURE, NO_MISPRICING, NO_CATALYST, THESIS_NOT_FALSIFIABLE, RECLAIM_UNCONFIRMED.

Research only. Not a trade instruction, allocation decision, or execution approval.
