# Equities thesis card (research-only)

Research (Investment Research) / equities sleeve artifact. Companion to generic `thesis.md` (lifecycle spine). Not a trade instruction, allocation decision, or execution approval.

- **Thesis id:**
- **Status / version:** draft
- **Desk:** Research (Investment Research) / equities sleeve
- **Author role:** Research
- **Instrument:**
- **Asset class:** equity
- **Time horizon:**
- **Principal membership:** unset
- **Watchlist tier:** unset
- **Membership note:** Principal keys are `in_universe` / `watch_only` (IMP-005). Watchlist tiers are `universe` / `monitor` / `blocked` (`config/watchlist/monitor.yaml`). Membership is not a Quant verdict and not a recommendation. This card does not change `config/universe.yaml`. Research must state tier on every idea. Monitor-tier ideas publish UNSIZED. NEW_LISTING names use the listings / post-IPO framework, not SMA200.
- **Working Quant verdict:** unset
- **Reason code(s):**
- **Knowledge watermark (as_of_knowledge):**
- **Independent Skeptic review required:** yes
- **Independent Skeptic verdict:** pending (not claimed as pass)

Closed Quant verdicts (IMP-001) only: `RESEARCH_PRIORITY` | `MONITOR` | `DEFER` | `REJECT` | `INSUFFICIENT_DATA`.

Post-IPO / reclaim **screen** is a separate Equities product (`lab equities reclaim-screen`, IMP-006). This card is not that screen.

## Non-goals

- No sizing.
- No execution, no order intent, no signing.
- No investment-call language.
- Does not edit `config/universe.yaml` or expand membership.
- Does not treat a drawdown as a thesis. A beaten-down IPO is not a candidate just because it is down.
- Does not approve risk. Author cannot be the sole Skeptic.

## Hypothesis

## Why now

## Why the market may be late or incomplete

## Filings / peers / liquidity (never invent missing prints)

No equity-feed ingest into Market Memory yet. Missing filings, earnings extracts, lock-up, dilution, or liquidity evidence stay `unavailable`. Capture clock is `as_of_knowledge` (lockstep with `ingested_at`); never `published_at` / `market_time`.

| item | value | source | as_of_knowledge | evidence_confidence | provenance |
| --- | --- | --- | --- | --- | --- |
| last attributable print | unavailable |  |  |  |  |
| peer / benchmark context | unavailable |  |  |  |  |
| liquidity | unavailable |  |  |  |  |
| filings / event calendar | unavailable |  |  |  |  |

## Evidence

| claim | source | timestamp | capture | evidence_confidence | provenance / observation id |
| --- | --- | --- | --- | --- | --- |

## Expected path

## Catalyst / condition to monitor

## Single invalidation

## Risks and alternative explanations

## What would change our mind

## Independent Skeptic stub

Reviewer must not be the author. Record via `lab skeptic` (`pass` | `revise` | `reject`). Checklist: bias / leakage / look-ahead; crowding / reflexivity; liquidity / leverage / slippage; alternatives; already-priced evidence; invalidation quality.

- **Skeptic findings:** pending
- **Required fixes before paper:** n/a until review

---
Research only. Not a trade instruction, allocation decision, or execution approval. A Quant verdict is not permission to paper or live. Principal gate still required for anything beyond research.
