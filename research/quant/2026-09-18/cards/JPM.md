# Quant Card — JPM

- **Instrument:** JPM (`JPM`)
- **Review date:** 2026-09-18
- **Knowledge watermark (as_of_knowledge):** 2026-09-18T02:00:00+00:00
- **Track(s):** A, B
- **Sector:** financials
- **Benchmark:** JPM
- **Peers:** XLF
- **Data-quality status:** partial
- **Labels:** none
- **Verdict:** DEFER
- **Reason code(s):** ALREADY_PRICED, NO_MISPRICING, NO_CATALYST, THESIS_NOT_FALSIFIABLE, STALE_OR_PARTIAL_DATA, RECLAIM_UNCONFIRMED
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)
- **Promotion checklist:** fresh_attributable_data=no, defined_benchmark_peers=yes, specific_anomaly=no, overlooked_reason=yes, catalyst_or_trigger=no, single_falsifiable_invalidation=no, acceptable_liquidity=no, no_unaddressed_duplicate_beta_or_dq=no, independent_skeptic_review_required=yes

## What is objectively unusual?

FAIL-patched to earnings-watch only. SEP-implied NII residual remains undefined (no numeric gap test). Enough process evidence to park the residual frame as DEFER rather than invent INSUFFICIENT_DATA theater on a missing figure.

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| expectations methodology FAIL: NII beats SEP-implied with no numeric gap | research/queue/EXPECTATIONS-20260917-methodology-scorecard.md | 2026-09-17 | Skeptic PR #22 | 0.85 | process artifact |
| FAIL patch: earnings-watch only; residual empty/speculative until gap test exists — not invented | research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md | 2026-09-17 | PR #23 | 0.85 | changelog maps FAIL → patch |
| call card after patch: financials PRIMARY by role; no macro→NII causation without prints | research/queue/UNIVERSE-20260917-call-cards.md | 2026-09-17 | call cards §10 | 0.75 | membership card |
| QUANT overlay last_close=348.9200134277344 asof=2026-09-16 rel_short=-0.93pp vs SPY (simple-diff) | research/queue/quant-20260917/metrics_active_and_watch.csv | 2026-09-17T01:15:47+00:00 | QUANT pack | 0.45 | yfinance:JPM; pre-FOMC corr must not be read as NII |

evidence_confidence is data reliability (0–1), not a board verdict.

## Relative performance and structure

QUANT JPM–XLF 0.73 (window 2026-05-28 → 2026-09-15, pre-FOMC) is description, not a pair. Same-day/next-day after FOMC+SEP, bank NIM / higher-for-longer is the crowded equity read (ALREADY_PRICED). No 2026-09-18 print.

## Why overlooked

in_universe financials primary. Role ≠ residual long. Gap test still empty.

## Alternative / skeptic case

Skeptic case: FF path → NII is a mechanism family, not a print. Inventing a SEP-implied NII figure would fail honesty rules.

## Catalyst / condition to monitor

Next company NII / NIM guide (8-K / earnings) as one side of a future gap test. Not a residual today.

## Single invalidation

FAIL-patch primary: next reported quarter NII misses company guide — kills promotion from earnings-watch to a higher-for-longer NII residual. Company guide extract not on this board.

## Liquidity / execution suitability

ADV not evidenced in Memory this pass.

## What must change for promotion / re-review

Promotion checklist: fresh_attributable_data=False, defined_benchmark_peers=True, specific_anomaly=False, overlooked_reason=True, catalyst_or_trigger=False, single_falsifiable_invalidation=False, acceptable_liquidity=False, no_unaddressed_duplicate_beta_or_dq=False, independent_skeptic_review_required=True. Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass). RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live. Unaddressed reason codes that block promotion: ALREADY_PRICED, NO_MISPRICING, NO_CATALYST, THESIS_NOT_FALSIFIABLE, STALE_OR_PARTIAL_DATA, RECLAIM_UNCONFIRMED.

Research only. Not a trade instruction, allocation decision, or execution approval.
