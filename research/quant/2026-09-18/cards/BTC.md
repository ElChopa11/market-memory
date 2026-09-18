# Quant Card — BTC

- **Instrument:** BTC (`BTC`, `BTCUSDC.P`)
- **Review date:** 2026-09-18
- **Knowledge watermark (as_of_knowledge):** 2026-09-18T02:00:00+00:00
- **Track(s):** A, B
- **Sector:** crypto_perp
- **Benchmark:** BTC
- **Peers:** ETH, UNI, AAVE
- **Data-quality status:** partial
- **Labels:** none
- **Verdict:** DEFER
- **Reason code(s):** RECLAIM_UNCONFIRMED, NO_MISPRICING, NO_CATALYST, THESIS_NOT_FALSIFIABLE, CORRELATED_EXPOSURE, STALE_OR_PARTIAL_DATA
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=no, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=no, single_falsifiable_invalidation=no, acceptable_liquidity=yes, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

Nothing that clears promotion. in_universe membership and a methodology PASS on a benchmark/range expectation are not a structure anomaly. Prior screenshot board (2026-09-17) was DEFER; this pass stays DEFER after re-score.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| prior Quant Board BTC=DEFER (screenshot universe, not locked membership) | research/quant/2026-09-17/cards/BTC.md | 2026-09-17T02:42:00+00:00 | IMP-001 board | 0.70 | prior board; overlap name only |
| expectations methodology PASS: range/benchmark path; cycle gates empty | research/queue/EXPECTATIONS-20260917-methodology-scorecard.md | 2026-09-17 | Skeptic PR #22 | 0.80 | process artifact; not a tape print |
| QUANT overlay last_close=76201.0234375 asof=2026-09-17 ret_short=+18.13% (native; not residual) | research/queue/quant-20260917/metrics_active_and_watch.csv | 2026-09-17T01:15:47+00:00 | QUANT pack run_meta.json | 0.55 | yfinance:BTC-USD overlay; clocks not mixed with a 2026-09-18 print |
| HL /info probe ok; no fundingHistory continuity in Memory this pass | ops/reports/source-health/2026-09-17.md | 2026-09-17T04:51:26+00:00 | IMP-003/004 source-health | 0.70 | health/provenance only; no mids copied |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

No 2026-09-18 session print in Market Memory. QUANT native series is descriptive. Reclaim unconfirmed. Track D not scored (no BTC_FUT on this locked board). Crypto-perp peers are operational, not a residual book.

## Why overlooked

Already in_universe membership. Board still requires an anomaly plus invalidation before a thesis pack. Personal-TV keep on the WATCHLIST-DD cut-review is not this board's RESEARCH_PRIORITY.

## Alternative / skeptic case

Skeptic case: hawkish-Fed and legislative setbacks are already public; deepest HL book is a liquidity reference, not mispricing. RQ-A funding/basis remains a separate workstream and is not auto-promoted here.

## Catalyst / condition to monitor

Monitor only: verified multi-day spot BTC ETF aggregate net inflows plus HL fundingHistory continuity. Neither series is in this pass's Memory snapshot.

## Single invalidation

Call-card primary remains: ≥5 consecutive US trading days of spot BTC ETF aggregate net outflows while HL funding stays ≥ +0.01%/8h with OI$ declining ≥15% from a dated capture baseline. Gates empty on this board — not a live trigger print.

## Liquidity / execution suitability

Liquidity acceptable for research follow-up (not an execution approval).

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=False, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=False, single_falsifiable_invalidation=False, acceptable_liquidity=True, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: RECLAIM_UNCONFIRMED, NO_MISPRICING, NO_CATALYST, THESIS_NOT_FALSIFIABLE, CORRELATED_EXPOSURE, STALE_OR_PARTIAL_DATA.

Research only. Not a trade instruction, allocation decision, or execution approval.
