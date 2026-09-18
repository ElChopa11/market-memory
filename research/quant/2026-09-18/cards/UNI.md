# Quant Card — UNI

- **Instrument:** UNI (`UNI`, `UNIUSDC.P`)
- **Review date:** 2026-09-18
- **Knowledge watermark (as_of_knowledge):** 2026-09-18T02:00:00+00:00
- **Track(s):** A, B
- **Sector:** crypto_perp
- **Benchmark:** BTC
- **Peers:** BTC, ETH, AAVE
- **Data-quality status:** partial
- **Labels:** none
- **Verdict:** MONITOR
- **Reason code(s):** EVENT_RISK, NO_MISPRICING, DUPLICATE_BETA, CORRELATED_EXPOSURE, THESIS_NOT_FALSIFIABLE, STALE_OR_PARTIAL_DATA, RECLAIM_UNCONFIRMED
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=no, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=yes, single_falsifiable_invalidation=yes, acceptable_liquidity=no, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

SEC PR 2026-90 (2026-09-17) is a dated public event: temporary Innovation Exemption for Tokenized Securities Venues using permissioned AMM liquidity pools for tokenized NMS stock. That does not auto-map to Uniswap protocol revenue. MONITOR only, with a falsifiable mapping test. Not RESEARCH_PRIORITY. QUANT 30d/90d bounce remains a footnote.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| SEC PR 2026-90 Innovation Exemption: permissioned TSV AMM pools for tokenized NMS; 5-year term; issuer objection window; LP dealer exemption | https://www.sec.gov/newsroom/press-releases/2026-90-sec-issues-innovation-exemption-facilitate-trading-tokenized-nms-stock-request-comment | 2026-09-17 | primary press release | 0.85 | as_of_knowledge 2026-09-18 Sydney; order text on SEC.gov |
| Skeptic #14/#22: event-gated fee-switch with no dated Uniswap proposal URL; 90-day fishing removed | research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md | 2026-09-17 | PR #23 + scorecard PR #22 | 0.85 | FAIL → deferred governance watch |
| call card: deferred governance watch; watch_only membership; bounce ≠ thesis | research/queue/UNIVERSE-20260917-call-cards.md | 2026-09-17 | call cards §3 | 0.75 | membership card |
| QUANT overlay last_close=6.7085 asof=2026-09-17 rel_short=+85.66pp vs BTC (simple-diff, NOT alpha); shorter Kraken history from 2024-09-27 | research/queue/quant-20260917/metrics_active_and_watch.csv | 2026-09-17T01:15:47+00:00 | QUANT pack (kraken:UNIUSD) | 0.40 | footnote only; do not promote on bounce |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

PR 2026-90 conditions that block a naive Uniswap map: access is permissioned; tokenized NMS must carry the same rights as traditional NMS of an equivalent class; TSV must post public notice and offer the issuer of third-party tokenized stock a chance to object; smart contracts sit on a public permissionless ledger but the venue is not thereby Uniswap. QUANT bounce vs BTC is not a structure regime and is not ARBITRAGE.

## Why overlooked

watch_only deferred governance name. Fresh public-law event exists; protocol mapping does not. Honest MONITOR rather than narrative upgrade.

## Alternative / skeptic case

Skeptic case: fee-switch / governance optionality is a multi-year recycled narrative. Permissioned TSV pools can list without Uniswap. Synthetics are outside the order. HL dayNtl appendix remains DO NOT SIZE.

## Catalyst / condition to monitor

Falsifiable mapping to monitor (not a thesis pack): a dated Uniswap governance proposal URL with executable fee parameters, or a TSV public notice required by PR 2026-90, that cites Uniswap contracts or UNI fee parameters for tokenized NMS. DEX volume share is not a substitute event.

## Single invalidation

Single trigger for the mapping: a TSV public notice (or issuer objection / absence of Uniswap citation in that notice) that does not name Uniswap contracts or UNI fee parameters — mapping from PR 2026-90 to UNI protocol revenue is then false for that venue. Revival of an event-gated UNI frame still requires a new card citing the URL (date, parameters, source). No 90-day fishing clock.

## Liquidity / execution suitability

HL UNI dayNtl appendix is stale; INADEQUATE for promotion. Not an execution approval.

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=False, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=True, single_falsifiable_invalidation=True, acceptable_liquidity=False, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: EVENT_RISK, NO_MISPRICING, DUPLICATE_BETA, CORRELATED_EXPOSURE, THESIS_NOT_FALSIFIABLE, STALE_OR_PARTIAL_DATA, RECLAIM_UNCONFIRMED.

Research only. Not a trade instruction, allocation decision, or execution approval.
