# Output contract (Principal briefing)

Research / desk product copy for the Principal. **Not an order. Not Execution. Not a Skeptic or Risk self-clear.**

Fill every section. Missing tape stays `unavailable` (degrade, never invent). Knowledge watermark is `as_of_knowledge` (lockstep with `ingested_at`) — never `published_at` / `market_time`.

## Writer hard rules

1. Do not invent prints, catalysts, or coverage. If a slot is empty, write `unavailable` and put it under **DATA GAPS**.
2. **TRADE IDEAS are intent-only.** No order instruction, no sizing, no venue routing, no “fill this”. Forbidden investment-call language (recommendation-as-order, allocation-as-order).
3. Do not self-approve. Authoring desk cannot claim Skeptic `pass`, Risk `allow`, or Principal override for its own thesis.
4. Skeptic FAIL **return** (`revise`) and FAIL **archive** (`reject`) are recorded under **SKEPTIC FLAGS**. Do not silently reopen an archive.
5. Risk **BLOCK** is terminal without Principal override. Record it under **RISK STATUS**. Do not treat BLOCK as allow.
6. Point-in-time law: what we knew is `as_of_knowledge`. Backtests use `available_at`.
7. No secrets, keys, wallet material, or `live.yaml` edits in this artifact.
8. Closed Quant vocabulary only: `RESEARCH_PRIORITY` | `MONITOR` | `DEFER` | `REJECT` | `INSUFFICIENT_DATA`. Membership (`in_universe` / `watch_only`) is not a Quant verdict.
9. Live remains hard-gated. Paper is not live. This file does not authorise either.

---

## HEADER

- **As-of (Australia/Sydney):**
- **Knowledge watermark (as_of_knowledge):**
- **Authoring desk / tier:** 3a Crypto | 3b Equities | 4 Quant | other:
- **Universe membership:** `in_universe` | `watch_only` | `not_in_membership`
- **Lifecycle status:** `draft` | `in_research` | `in_skeptic` | `paper` | `rejected` | `retired`
- **Intent / thesis id:**
- **Data quality:** `fresh` | `stale` | `partial` | `unavailable`

## TAPE

What the tape showed at the watermark. Source + freshness on every row. No invented last print.

| instrument | metric | value | source | freshness | observation_id |
| --- | --- | --- | --- | --- | --- |

## WHAT CHANGED

What is new versus the prior briefing / prior close. If nothing new, write `none` (do not recycle commentary).

## TRADE IDEAS (intent-only)

Falsifiable intents, not orders. Each row needs invalidation language. No size. No execution path.

| instrument | intent (one sentence) | invalidation | horizon | evidence refs |
| --- | --- | --- | --- | --- |

If none: `none`.

## QUANT NOTE

- **Verdict:** `RESEARCH_PRIORITY` | `MONITOR` | `DEFER` | `REJECT` | `INSUFFICIENT_DATA` | `unset`
- **Reason code(s):**
- **Relative-value / reclaim / structure (not executable-arb unless criteria are complete):**

## SKEPTIC FLAGS

- **Independent Skeptic of record:** (not the author)
- **Verdict:** `pending` | `pass` | `revise` (FAIL return) | `reject` (FAIL archive)
- **Leakage / look-ahead / crowding / already-priced / invalidation quality:**

## RISK STATUS

- **Decision:** `pending` | `allow` | `block`
- **rule_id / config_version:**
- **BLOCK terminal?** yes (no paper/live) unless Principal override recorded
- **Principal override:** `none` | recorded by Principal (not the proposing desk)

## BOOK

Paper/shadow book only. Live is later and hard-gated. Empty is honest.

| thesis_id | paper status | invalidation | max loss | notes |
| --- | --- | --- | --- | --- |

## DATA GAPS

Always list. Paid feeds, Polygon (5b), HL depth, Telegram delivery (5e) are not filled by this template.

| gap | impact | owner desk |
| --- | --- | --- |
