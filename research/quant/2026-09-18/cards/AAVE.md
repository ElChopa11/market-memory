# Quant Card — AAVE

- **Instrument:** AAVE (`AAVE`, `AAVEUSDC.P`)
- **Review date:** 2026-09-18
- **Knowledge watermark (as_of_knowledge):** 2026-09-18T02:00:00+00:00
- **Track(s):** A, B
- **Sector:** crypto_perp
- **Benchmark:** BTC
- **Peers:** BTC, ETH, UNI
- **Data-quality status:** partial
- **Labels:** none
- **Verdict:** DEFER
- **Reason code(s):** NO_CATALYST, THESIS_NOT_FALSIFIABLE, DUPLICATE_BETA, CORRELATED_EXPOSURE, STALE_OR_PARTIAL_DATA, INADEQUATE_LIQUIDITY, RECLAIM_UNCONFIRMED, NO_MISPRICING
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=no, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=no, single_falsifiable_invalidation=no, acceptable_liquidity=no, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

SEC PR 2026-90 LP dealer exemption on TSV AMM pools does not fill an Aave utilization baseline and does not imply crypto-credit demand. Credit expectation stays dropped. DEFER. Not MONITOR on narrative adjacency to AMMs.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| SEC PR 2026-90: conditional dealer exemption for TSV AMM liquidity providers in tokenized NMS — not an Aave utilization print | https://www.sec.gov/newsroom/press-releases/2026-90-sec-issues-innovation-exemption-facilitate-trading-tokenized-nms-stock-request-comment | 2026-09-17 | primary press release | 0.85 | read as non-mapping unless a dated Aave listing/baseline exists |
| FAIL patch: deferred/micro watch; rate→credit killed; utilization −25% trigger removed as unfalsifiable | research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md | 2026-09-17 | PR #23 | 0.85 | credit frame already dropped |
| call card: no obs-linked utilization baseline; HL appendix DO NOT SIZE | research/queue/UNIVERSE-20260917-call-cards.md | 2026-09-17 | call cards §4 | 0.75 | membership card |
| QUANT overlay last_close=120.01000213623047 asof=2026-09-17 rel_short=+16.34pp vs BTC (simple-diff, NOT alpha) | research/queue/quant-20260917/metrics_active_and_watch.csv | 2026-09-17T01:15:47+00:00 | QUANT pack | 0.45 | yfinance:AAVE-USD; not utilization |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

Rate path ≠ utilization ≠ revenue (Skeptic #14/#22). TSV dealer exemption ≠ Aave core-market utilization. No dated Aave governance or listing URL tying tokenized NMS collateral to protocol revenue. Duplicate crypto beta vs BTC.

## Why overlooked

watch_only deferred/micro. PR 2026-90 was evaluated and did not supply the blocking baseline.

## Alternative / skeptic case

Skeptic case: higher-for-longer → borrow demand is a causation leap. Thin HL dayNtl must not be treated as a micro-size license.

## Catalyst / condition to monitor

Blocking revival input: obs-linked core-market utilization print (dashboard URL + as-of + figure or observation id). Not present.

## Single invalidation

Credit-demand / rate→borrow frame is already dropped. Any revival without an obs-linked utilization baseline is methodologically invalid. PR 2026-90 does not replace that baseline.

## Liquidity / execution suitability

HL AAVE appendix thin/stale — INADEQUATE_LIQUIDITY for promotion. Not an execution approval.

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=False, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=False, single_falsifiable_invalidation=False, acceptable_liquidity=False, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: NO_CATALYST, THESIS_NOT_FALSIFIABLE, DUPLICATE_BETA, CORRELATED_EXPOSURE, STALE_OR_PARTIAL_DATA, INADEQUATE_LIQUIDITY, RECLAIM_UNCONFIRMED, NO_MISPRICING.

Research only. Not a trade instruction, allocation decision, or execution approval.
