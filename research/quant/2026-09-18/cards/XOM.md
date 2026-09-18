# Quant Card — XOM

- **Instrument:** XOM (`XOM`)
- **Review date:** 2026-09-18
- **Knowledge watermark (as_of_knowledge):** 2026-09-18T02:00:00+00:00
- **Track(s):** A, B
- **Sector:** energy
- **Benchmark:** XOM
- **Peers:** none
- **Data-quality status:** partial
- **Labels:** none
- **Verdict:** INSUFFICIENT_DATA
- **Reason code(s):** STALE_OR_PARTIAL_DATA, INSUFFICIENT_HISTORY, NO_CATALYST, THESIS_NOT_FALSIFIABLE, NO_MISPRICING, RECLAIM_UNCONFIRMED
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=no, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=no, single_falsifiable_invalidation=no, acceptable_liquidity=no, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

Crude-gated methodology PASSed, but crude strip / inventory / CL tape are not in Memory. Stooq CL was unavailable. Prefer INSUFFICIENT_DATA over scoring a crude gate with no strip as-of.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| expectations methodology PASS: crude-gated path; hike→XOM shorthand killed | research/queue/EXPECTATIONS-20260917-methodology-scorecard.md | 2026-09-17 | Skeptic PR #22 | 0.80 | process artifact; methodology ≠ tape |
| call card: need crude strip + inventory + FCF/buyback primary sources — not hike narrative | research/queue/UNIVERSE-20260917-call-cards.md | 2026-09-17 | call cards §12 | 0.70 | membership card; field 7 still empty |
| QUANT overlay last_close=163.32000732421875 asof=2026-09-16 rel_short=+3.56pp vs SPY (simple-diff, not alpha) | research/queue/quant-20260917/metrics_active_and_watch.csv | 2026-09-17T01:15:47+00:00 | QUANT pack | 0.45 | yfinance:XOM; not a crude strip |
| Stooq CL canary/configured symbol unavailable (http 404 class); FRED missing_env | ops/reports/source-health/2026-09-17.md | 2026-09-17T04:51:26+00:00 | IMP-003/004 | 0.80 | oil tape gap |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

No energy-future print this pass. QUANT equity overlay is not WTI/Brent. Negative macro corr is not an energy sleeve (QUANT honesty). Reclaim unconfirmed.

## Why overlooked

in_universe crude-gated name. Clean methodology does not fill missing strip as-of.

## Alternative / skeptic case

Skeptic case: Fed hikes because inflation is sticky does not imply XOM upside; oil supply/demand and refining margins dominate. Do not revive hike→energy shorthand.

## Catalyst / condition to monitor

WTI/Brent strip levels and EIA/API inventory with source+as-of. Empty in Memory this pass.

## Single invalidation

Call-card primary: front-month WTI settles below $60 for 5 consecutive sessions, or company withdraws/cuts the repurchase program on an FCF miss in next earnings. Neither print is on this board.

## Liquidity / execution suitability

ADV not evidenced in Memory this pass.

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=False, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=False, single_falsifiable_invalidation=False, acceptable_liquidity=False, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: STALE_OR_PARTIAL_DATA, INSUFFICIENT_HISTORY, NO_CATALYST, THESIS_NOT_FALSIFIABLE, NO_MISPRICING, RECLAIM_UNCONFIRMED.

Research only. Not a trade instruction, allocation decision, or execution approval.
