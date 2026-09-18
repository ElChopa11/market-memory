# Quant Card — NVDA

- **Instrument:** NVDA (`NVDA`)
- **Review date:** 2026-09-18
- **Knowledge watermark (as_of_knowledge):** 2026-09-18T02:00:00+00:00
- **Track(s):** A, B
- **Sector:** ai_infra
- **Benchmark:** NVDA
- **Peers:** AVGO, SMH
- **Data-quality status:** partial
- **Labels:** none
- **Verdict:** DEFER
- **Reason code(s):** RECLAIM_UNCONFIRMED, NO_MISPRICING, CORRELATED_EXPOSURE, NO_CATALYST, THESIS_NOT_FALSIFIABLE, STALE_OR_PARTIAL_DATA
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=no, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=no, single_falsifiable_invalidation=no, acceptable_liquidity=yes, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

Nothing that clears promotion. Crowded AI-infra primary with an empty mispricing gate. Prior screenshot board DEFER; re-score stays DEFER. Equity tape is not in Market Memory; Stooq was unavailable on the last source-health report.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| prior Quant Board NVDA=DEFER | research/quant/2026-09-17/cards/NVDA.md | 2026-09-17T02:42:00+00:00 | IMP-001 board | 0.70 | prior board overlap name |
| expectations methodology PASS: crowded/unwind honesty; cycle upside gated on missing mispricing | research/queue/EXPECTATIONS-20260917-methodology-scorecard.md | 2026-09-17 | Skeptic PR #22 | 0.80 | process artifact |
| QUANT overlay last_close=213.89999389648438 asof=2026-09-16 rel_short=-2.42pp vs SPY (simple-diff, not alpha) | research/queue/quant-20260917/metrics_active_and_watch.csv | 2026-09-17T01:15:47+00:00 | QUANT pack | 0.45 | yfinance:NVDA; US session 2026-09-16; stale vs 2026-09-18 Sydney review |
| Stooq unavailable (canary HTTP 404); FRED missing_env; no equity ingest | ops/reports/source-health/2026-09-17.md | 2026-09-17T04:51:26+00:00 | IMP-003/004 | 0.80 | equity tape gap; do not invent prints |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

No 2026-09-18 equity print. Overlay is one-session-lag descriptive vs SPY, not a residual. Reclaim unconfirmed. AVGO is satellite; SMH is appendix — correlated AI-infra exposure, not three independent books.

## Why overlooked

Already in_universe as AI-infra primary. Still needs a documented mispricing vs consensus guide, not a demand-exists narrative. Personal-TV keep is not RESEARCH_PRIORITY.

## Alternative / skeptic case

Skeptic case: hyperscaler capex hopes are already priced; Fool/MarketBeat secondaries on the call card are weak. A capex scare is unwind risk, not a thesis pack trigger.

## Catalyst / condition to monitor

Next dated hyperscaler capex guide (MSFT / GOOGL / AMZN / META) or NVDA data-center revenue/GM vs company guide. Not in Memory this pass.

## Single invalidation

Call-card primary: a named hyperscaler cuts AI/data-center capex guide in a dated earnings print or 8-K vs prior guide. No such extract on this board.

## Liquidity / execution suitability

Liquidity acceptable for research follow-up (not an execution approval).

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=False, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=False, single_falsifiable_invalidation=False, acceptable_liquidity=True, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: RECLAIM_UNCONFIRMED, NO_MISPRICING, CORRELATED_EXPOSURE, NO_CATALYST, THESIS_NOT_FALSIFIABLE, STALE_OR_PARTIAL_DATA.

Research only. Not a trade instruction, allocation decision, or execution approval.
