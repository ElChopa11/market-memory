# Quant Card — MSFT

- **Instrument:** MSFT (`MSFT`)
- **Review date:** 2026-09-18
- **Knowledge watermark (as_of_knowledge):** 2026-09-18T02:00:00+00:00
- **Track(s):** A, B
- **Sector:** mega_quality
- **Benchmark:** MSFT
- **Peers:** META
- **Data-quality status:** partial
- **Labels:** none
- **Verdict:** INSUFFICIENT_DATA
- **Reason code(s):** STALE_OR_PARTIAL_DATA, NO_CATALYST, THESIS_NOT_FALSIFIABLE, NO_MISPRICING, CORRELATED_EXPOSURE, RECLAIM_UNCONFIRMED
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=no, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=no, single_falsifiable_invalidation=no, acceptable_liquidity=no, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

Earnings-gated Azure/ROI claim has no Azure extract on sheet. Methodology INCONCLUSIVE. Thin equity tape. INSUFFICIENT_DATA.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| expectations methodology INCONCLUSIVE: Azure extract empty so path cannot be scored | research/queue/EXPECTATIONS-20260917-methodology-scorecard.md | 2026-09-17 | Skeptic PR #22 | 0.80 | process artifact |
| call card: sheet evidence is macro-only; no Azure growth print | research/queue/UNIVERSE-20260917-call-cards.md | 2026-09-17 | call cards §8 | 0.70 | membership card |
| QUANT overlay last_close=490.29998779296875 asof=2026-09-16 rel_short=+4.67pp vs SPY (simple-diff, not alpha) | research/queue/quant-20260917/metrics_active_and_watch.csv | 2026-09-17T01:15:47+00:00 | QUANT pack | 0.45 | yfinance:MSFT; large raw vs-SPY is not residual alpha (QUANT honesty) |
| Stooq unavailable; no equity ingest; no MSFT on 2026-09-17 screenshot board | ops/reports/source-health/2026-09-17.md | 2026-09-17T04:51:26+00:00 | source-health | 0.75 | tape gap |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

No 2026-09-18 print. Overlay rel vs SPY must not confirm the earnings-gated path. Peer META has a lagged QUANT asof (2026-09-15), so mega-quality relative structure is not contemporaneous.

## Why overlooked

in_universe quality compounder narrative is consensus; Quant still needs Azure extracts.

## Alternative / skeptic case

Skeptic case: fortress/quality-under-higher-rates is already priced folklore without MSFT-specific proof on sheet.

## Catalyst / condition to monitor

Next earnings Azure constant-currency growth / Intelligent Cloud extract. Empty this pass.

## Single invalidation

Call-card primary: Azure constant-currency growth decelerates by ≥300 bps QoQ vs the prior quarter's disclosed Azure growth. Prior-quarter figure is not extracted here.

## Liquidity / execution suitability

ADV not evidenced in Memory this pass.

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=False, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=False, single_falsifiable_invalidation=False, acceptable_liquidity=False, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: STALE_OR_PARTIAL_DATA, NO_CATALYST, THESIS_NOT_FALSIFIABLE, NO_MISPRICING, CORRELATED_EXPOSURE, RECLAIM_UNCONFIRMED.

Research only. Not a trade instruction, allocation decision, or execution approval.
