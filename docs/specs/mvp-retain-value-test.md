# MVP retain value test

**Status.** Frozen method, 2026-09-24, version `mvp-retain-value-test-v1`. Written before any retain data. A test written after the results is not a test.

Read with [the capture contract](mvp-retain-capture-contract.md). That contract is the behaviour this test scores. Quadrant deltas are not computed in draft #122. This test does not wait for them, and it does not invent them.

Paper only. Not a trade. Not a size. Not a Quant verdict. Not a Skeptic pass on a thesis. Passing this bar does not enable Neon, cron, or Telegram.

## Why the bar is fixed now

The P0 reconstruction put novel value at about one session in ten. The desk will ask again when eleven captures have been stored. The continue rule and the stop rule are set here, while the count is still zero.

This version stays frozen through those eleven captures, and through the second window if the 2-out-of-10 rule opens one. The definition of a hit, the judge, and the thresholds do not move after capture 1 lands. A change is a new version, and a new version does not rescore captures already in flight.

## What is being scored

The unit is the morning session, not the instrument. One morning can add at most one hit, however many names look interesting.

Eleven stored captures produce ten scored mornings: capture 2 against capture 1, capture 3 against capture 2, and so on through capture 11 against capture 10. Capture 1 is logged and is not a scored morning. It has no prior.

The re-ask happens when eleven captures have been stored, and not before. A short series is not scored early.

A calendar morning that never captured is not a scored morning and is not a hit. It is recorded as missed. The next real pair is still one morning, including when the gap is long. A 14 hour gap and a 26 hour gap are one pair each, matching the capture contract. The long gap is not split and is not an automatic no.

Every one of the ten mornings stays in the denominator. Inside those ten, a morning marked not scorable counts as a no at the tally. It is not dropped. Capture 1 is the only not-scorable line that sits outside the ten. Empty fields therefore make the bar harder, which is the point.

## What counts as beyond a chart glance

A scored morning is beyond a chart glance only when every line below is true.

1. The morning is a real pair. Both captures exist, both timestamps are the ones stored, and `interval_seconds` on the later capture is the elapsed time between them.
2. The note names one bound perp that is not blocked. CASHCAT and PONS cannot be the named instrument. DRV cannot be the named instrument. An equity close cannot be the named instrument. JUP or NIL may be named only if the line says monitor, and the line does not treat the name as promoted.
3. The note uses open interest or funding from the two stored captures. A restatement of `mid_px`, or of an equity close, is a chart glance.
4. The fact is a relationship the price chart does not show. Open interest and mid moved in opposite directions. Open interest changed while mid was flat. Funding changed sign, or stepped, while the mid move is the ordinary chart. Both numbers and both timestamps are cited from the stored rows.
5. The cited open interest, or the cited funding, and the cited mid are all present. A null is not a fact. The mark is not a substitute for a null mid.
6. No quadrant label is required. None may be invented. While #122 does not compute quadrant deltas, the judge compares the stored levels. The words "long quadrant" without the stored open interest and the two timestamps do not count.

Examples that count:

- BTC open interest fell from the capture-1 print to the capture-2 print while the stored mid rose, both timestamps cited.
- ETH funding changed sign between the two stored captures while the stored mid was unchanged.

Examples that do not count:

- "BTC was up overnight."
- "QQQ closed at X."
- "DRV mid was 1.25."
- A blocked name as the only cited instrument.
- A comparison that uses the mark because the mid was null.
- A quadrant word with no stored open interest or funding behind it.

## Who judges

The desk that produced the morning brief, or the retain note, does not score that morning. Author and scorer are different people.

| Role | Does |
|---|---|
| Ops, or Research if they write the interpretation | Writes the evidence note from stored rows. Does not score it. |
| IC/Risk Skeptic gate | Scores the morning yes or no against the definition above. |
| Principal | Accepts the tally at eleven captures. Scores a morning directly only when the Skeptic would be scoring a note that Skeptic wrote. |

Quant does not score this test. A Quant verdict is a different gate.

A self-score is invalid. If the morning has not been scored by the independent role before the eleven-capture tally, it counts as a no.

## Thresholds

Numerator: how many of the ten scored mornings are beyond a chart glance.

Denominator: ten. Always.

| Result | What happens |
|---|---|
| **3 or more out of 10** | Continue. The retain set stays a candidate morning input under this same method. |
| **1 or fewer out of 10** | Stop. This matches the reconstruction prior, or lands under it. |
| **2 out of 10** | Inconclusive on the pre-committed rule below. Not a Principal coin-flip after seeing the names. |

### The 2-out-of-10 rule

Hold one more window. That window is the next ten scored mornings: the pairs from capture 11→12 through capture 20→21. Ten further captures after the eleventh.

Score that window by itself, with the same definition and the same judge rule.

- 3 or more out of 10 in the second window: continue.
- 2 or fewer out of 10 in the second window: stop.

The two windows are not added together. Two-out-of-ten followed by two-out-of-ten is a stop, not four out of twenty. There is no third window.

### What continue means, and what stop means

Continue means the same 37-instrument set remains worth keeping as a morning input. It does not widen the set. It does not enable Neon. It does not start a cron. It does not send Telegram. It does not authorize quadrant code. Those stay separate Principal decisions.

Stop means the series is not an input to the morning brief, and the set is not widened. Rows already stored stay stored. This method does not delete them. There is no consolation window after a stop.

Either result is recorded by the Principal at the re-ask, citing this version and the ten morning lines.

## What we log each morning

One line per capture, written the morning it happens, from stored rows only. The scorer's fields are filled by the judge, not by the author. The tally is filled only at the re-ask.

| Field | What it holds |
|---|---|
| `method_version` | `mvp-retain-value-test-v1` |
| `capture_index` | 1, 2, 3, … |
| `session_date` | The Sydney calendar date of the morning |
| `captured_at` | The real UTC timestamp stored on the rows |
| `prior_captured_at` | Empty on capture 1. Otherwise the prior timestamp actually supplied |
| `interval_seconds` | Empty on capture 1. Otherwise the stored elapsed seconds, unbucketed |
| `calendar_gap` | `none`, or `missed` when a Sydney morning produced no capture before this one. A note for the audit. The retain rows do not carry this label |
| `row_count` | Stored observations this capture. This set writes 75 every time, including empty rows |
| `null_mids` | Instruments whose `mid_px` is empty. Mark is not listed as a fill |
| `null_closes` | Equity tickers whose close is empty |
| `drv_mid` | The stored DRV mid, or empty, plus whether the pair resolved as DRV/USDC at index 700 |
| `quadrant_deltas_computed` | `false` for as long as #122 is the behaviour |
| `evidence_note` | A short note that cites stored numbers and both timestamps, or states that there is nothing beyond the chart |
| `author_desk` | The desk that wrote the note |
| `author` | The person who wrote the note |
| `cited_instrument` | The one bound perp named for a possible hit, or empty |
| `cited_tier` | `blocked`, `monitor`, or empty, copied from the row |
| `cited_fields` | Which stored fields the note actually used |
| `beyond_chart_glance` | `yes`, `no`, or `not_scorable`. Filled by the judge. Capture 1 is `not_scorable` and is outside the ten |
| `score_reason` | One sentence from the judge, pointing at the definition line that passed or failed |
| `scorer_role` | `ic_risk_skeptic`, or `principal` when the author conflict rule applies |
| `scorer` | The person who scored. Must differ from `author` |
| `self_score_refused` | `true` when an author attempt to score was rejected |

Checklist before the line is closed:

1. The capture time is the real stored time.
2. The prior is either empty, on a first capture, or the timestamp that was actually supplied.
3. `interval_seconds` is the raw stored number, with no 14-hour versus 26-hour label.
4. Null mids and null closes are still null.
5. The note cites stored values only. No quadrant word without those values.
6. The author is named, with their desk.
7. The scorer is a different person, in the Skeptic role, or the Principal under the conflict rule.
8. A `yes` names one eligible bound perp and uses open interest or funding.
9. A morning with no independent score stays a `no` at the tally.

At eleven captures, and again at the end of a second window if the 2-out-of-10 rule opens one, add:

| Field | What it holds |
|---|---|
| `window` | `first` or `second` |
| `hits` | Count of `yes` in that window's ten mornings |
| `denominator` | 10 |
| `result` | `continue`, `stop`, or `second_window` (only the first window may record `second_window`, and only at exactly 2 hits) |
| `accepted_by` | Principal |
| `accepted_at` | The date of the re-ask |
