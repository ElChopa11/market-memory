# Quant Card — ETH

- **Instrument:** ETH (`ETH`, `ETHUSDC.P`)
- **Review date:** 2026-09-18
- **Knowledge watermark (as_of_knowledge):** 2026-09-18T02:00:00+00:00
- **Track(s):** A, B
- **Sector:** crypto_perp
- **Benchmark:** BTC
- **Peers:** BTC, UNI, AAVE
- **Data-quality status:** partial
- **Labels:** none
- **Verdict:** MONITOR
- **Reason code(s):** DUPLICATE_BETA, CORRELATED_EXPOSURE, NO_MISPRICING, RECLAIM_UNCONFIRMED, NO_CATALYST, THESIS_NOT_FALSIFIABLE
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=no, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=yes, single_falsifiable_invalidation=yes, acceptable_liquidity=yes, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

Re-score does not keep MONITOR because QUANT raw ETH−BTC was large. FAIL patch banned α. MONITOR is the BTC-beta desk watch with a single ETF-outflow trigger — membership watch_only, not an independent residual.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| prior Quant Board ETH=MONITOR (screenshot overlay rel vs BTC treated as descriptive RV) | research/quant/2026-09-17/cards/ETH.md | 2026-09-17T02:42:00+00:00 | IMP-001 board | 0.60 | prior board; do not rubber-stamp overlay as alpha |
| expectations methodology FAIL then patch: BTC-beta watch; residual empty until β protocol exists | research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md | 2026-09-17 | PR #23 | 0.85 | FAIL → demote |
| QUANT overlay last_close=2415.419922 asof=2026-09-17 rel_short=+8.19pp vs BTC (simple-diff, NOT alpha) | research/queue/quant-20260917/metrics_active_and_watch.csv | 2026-09-17T01:15:47+00:00 | QUANT pack | 0.50 | yfinance:ETH-USD; rel_method=simple_diff_NOT_alpha |
| universe.yaml watch_only; ETH = BTC-beta watch (PR #23 / Skeptic PASS on FAIL patch) | config/universe.yaml | 2026-09-17 | Principal membership | 0.90 | membership ≠ Quant verdict |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

Raw ETH−BTC is not edge. No named-window β residual and no L2 fee/activity residual. Prior board MONITOR from overlay magnitude is retired as an α read. Duplicate-beta vs BTC is the default.

## Why overlooked

watch_only BTC-beta. Board still watches ETF flows; it does not promote an RV long.

## Alternative / skeptic case

Skeptic case: HL #2 book stamps are stale appendix (DO NOT SIZE). Funding skew without OI series is incomplete microstructure.

## Catalyst / condition to monitor

ETH ETF aggregate net flows (monitor). L2 fee/activity residual still empty.

## Single invalidation

FAIL-patch primary: ETH ETF aggregate net outflows on ≥5 consecutive US trading days kills promotion from BTC-beta watch to an independent or RV-vs-BTC frame. Raw ETH−BTC is not this trigger.

## Liquidity / execution suitability

Liquidity acceptable for research follow-up (not an execution approval).

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=False, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=True, single_falsifiable_invalidation=True, acceptable_liquidity=True, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: DUPLICATE_BETA, CORRELATED_EXPOSURE, NO_MISPRICING, RECLAIM_UNCONFIRMED, NO_CATALYST, THESIS_NOT_FALSIFIABLE.

Research only. Not a trade instruction, allocation decision, or execution approval.
