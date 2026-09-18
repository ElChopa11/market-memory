# Quant Card — XLF

- **Instrument:** XLF (`XLF`)
- **Review date:** 2026-09-18
- **Knowledge watermark (as_of_knowledge):** 2026-09-18T02:00:00+00:00
- **Track(s):** A, B
- **Sector:** financials
- **Benchmark:** JPM
- **Peers:** JPM
- **Data-quality status:** partial
- **Labels:** none
- **Verdict:** DEFER
- **Reason code(s):** DUPLICATE_BETA, CORRELATED_EXPOSURE, NO_MISPRICING, NO_CATALYST, THESIS_NOT_FALSIFIABLE, STALE_OR_PARTIAL_DATA, RECLAIM_UNCONFIRMED
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=no, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=no, single_falsifiable_invalidation=no, acceptable_liquidity=no, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

FAIL-patched to monitor-only diversifier with research priority strictly below JPM. Aggregate bank NII / KRE breadth still empty. DEFER (duplicate of JPM), not an independent MONITOR sleeve that could be misread as a second financials book.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| FAIL patch: double-count is the default; corr 0.73 = description not proof; blog removed | research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md | 2026-09-17 | PR #23 | 0.85 | diversifier-value claim removed |
| universe.yaml watch_only; XLF = monitor ≪ JPM (FAIL-patch PR #23) | config/universe.yaml | 2026-09-17 | Principal membership | 0.90 | membership ≠ Quant verdict |
| QUANT overlay last_close=55.93000030517578 asof=2026-09-16; JPM–XLF 0.73 pre-FOMC 60d | research/queue/quant-20260917/metrics_active_and_watch.csv | 2026-09-17T01:15:47+00:00 | QUANT pack + run_meta corr | 0.45 | corr ≠ causation; not a pair |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

Tracks JPM/financials complex as description. Breadth metrics (FDIC/Fed aggregate bank NII, KRE vs XLF with a registered window) are not operationalized. No 2026-09-18 print.

## Why overlooked

watch_only diversifier. Same higher-for-longer theme as JPM — two tickers, one idea.

## Alternative / skeptic case

Skeptic case: treating XLF as independent sector expression double-counts JPM. Pre-FOMC corr cannot underwrite a diversifier.

## Catalyst / condition to monitor

Operational breadth pack (aggregate NII + KRE with sources/as-of). Empty this pass.

## Single invalidation

FAIL-patch primary: JPM NII-miss invalidation auto-drops the XLF sleeve (double-count). No independent XLF frame to kill.

## Liquidity / execution suitability

ETF ADV not evidenced in Memory this pass.

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=False, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=False, single_falsifiable_invalidation=False, acceptable_liquidity=False, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: DUPLICATE_BETA, CORRELATED_EXPOSURE, NO_MISPRICING, NO_CATALYST, THESIS_NOT_FALSIFIABLE, STALE_OR_PARTIAL_DATA, RECLAIM_UNCONFIRMED.

Research only. Not a trade instruction, allocation decision, or execution approval.
