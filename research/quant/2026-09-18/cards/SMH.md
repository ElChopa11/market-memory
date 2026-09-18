# Quant Card — SMH

- **Instrument:** SMH (`SMH`)
- **Review date:** 2026-09-18
- **Knowledge watermark (as_of_knowledge):** 2026-09-18T02:00:00+00:00
- **Track(s):** A, B
- **Sector:** ai_infra
- **Benchmark:** NVDA
- **Peers:** NVDA, AVGO
- **Data-quality status:** partial
- **Labels:** none
- **Verdict:** DEFER
- **Reason code(s):** DUPLICATE_BETA, CORRELATED_EXPOSURE, NO_MISPRICING, NO_CATALYST, THESIS_NOT_FALSIFIABLE, STALE_OR_PARTIAL_DATA, RECLAIM_UNCONFIRMED
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=no, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=no, single_falsifiable_invalidation=no, acceptable_liquidity=no, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

Monitor-only AI-infra basket appendix after FAIL patch. Holdings overlap % vs NVDA/AVGO unpublished. Not a basket-outperform claim. DEFER (parked duplicate), not RESEARCH_PRIORITY, not a tape-driven MONITOR.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| FAIL patch: dropped from in-universe thesis-priority expectations; overlap % required before xor | research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md | 2026-09-17 | PR #23 | 0.85 | basket-outperform removed |
| universe.yaml watch_only; redundant vs NVDA+AVGO (Skeptic PR #14 demotion cite) | config/universe.yaml | 2026-09-17 | Principal membership | 0.90 | membership ≠ Quant verdict |
| QUANT overlay last_close=545.5599975585938 asof=2026-09-16 YTD vs SPY flagged watch_YTD_not_promotion | research/queue/quant-20260917/metrics_active_and_watch.csv | 2026-09-17T01:15:47+00:00 | QUANT pack asof_note | 0.45 | post-selection YTD is not a promotion argument |
| WATCHLIST-DD cut-review: theme-dedupe vs NVDA primary (AMD demoted on the same logic) | research/queue/WATCHLIST-DD-20260917-personal-skeptic.md | 2026-09-17 | Skeptic cut-review | 0.70 | personal-TV pack; not this board's membership expansion |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

Triple-count risk: SMH + NVDA + AVGO = one AI-infra theme. Issuer holdings file (NVDA weight, AVGO weight, combined overlap %) is empty — xor blocked. No 2026-09-18 print.

## Why overlooked

watch_only appendix. Street already uses SMH for the buildout — definitional, not an edge.

## Alternative / skeptic case

Skeptic case: restoring basket-outperform while NVDA+AVGO remain in_universe fails theme-dedupe. Do not revive memory-semi names via unpublished weights.

## Catalyst / condition to monitor

Published holdings overlap % vs NVDA/AVGO. Empty — blocking for any xor.

## Single invalidation

FAIL-patch primary: NVDA primary invalidation (named hyperscaler capex cut) auto-drops the SMH appendix. No independent SMH outperform frame.

## Liquidity / execution suitability

ETF ADV not evidenced in Memory this pass.

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=False, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=False, single_falsifiable_invalidation=False, acceptable_liquidity=False, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: DUPLICATE_BETA, CORRELATED_EXPOSURE, NO_MISPRICING, NO_CATALYST, THESIS_NOT_FALSIFIABLE, STALE_OR_PARTIAL_DATA, RECLAIM_UNCONFIRMED.

Research only. Not a trade instruction, allocation decision, or execution approval.
