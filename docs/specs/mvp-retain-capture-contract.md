# MVP retain capture contract

**Status.** Principal reading copy, 2026-09-24. Describes the behaviour in draft [PR #122](https://github.com/ElChopa11/market-memory/pull/122) (`cursor/mvp-retain-forward-only-3151`) as implemented. Paper only. This page does not merge that draft, enable Neon, start a cron, or send Telegram.

Read with [the value test](mvp-retain-value-test.md). The test bar is frozen before any retain rows exist.

## The locked set

One capture is one pass over the same set. Every pass makes three HTTP calls and writes one observation per retained field.

| Call | What is requested | What is kept |
|---|---|---|
| 1 | Hyperliquid perp snapshot (`metaAndAssetCtxs`) | 19 bound perps: open interest, funding, and `mid_px` |
| 2 | Polygon US grouped daily, one calendar session date | 17 equity session closes |
| 3 | Hyperliquid spot snapshot (`spotMetaAndAssetCtxs`) | DRV/USDC at spot index 700: `mid_px` only |

37 instruments. Every capture writes 75 observations: 19 × 3, plus one DRV mid, plus 17 closes. A missing field is still a row, with an empty value.

**Bound perps (19).** BTC, ETH, SOL, JUP, HYPE, LIT, NEAR, ARB, UNI, VVV, ZEC, DOGE, XMR, CASHCAT, PONS, CHIP, LTC, NIL, PURR. PURR is one of the 19. LIT and LTC are both kept, as separate names.

**Price only (1).** DRV, the spot pair DRV/USDC at index 700. A capture always requests the spot book. The mid is kept only when that book contains DRV/USDC at index 700. Any other spot result leaves the mid empty. One mid. No open interest. No funding. No quadrant.

**Equity closes (17).** QQQ, CRCL, TSLA, SPCX, NVDA, BB, GLXY, IBIT, BMNR, MRNA, GOOG, HOOD, NOW, CBRS, MSTR, STRC, AMD.

**Not in the set.** KNT and KNTQ. The other-venue queue: SPX, NQ1!, CL1!, BTC1!, SAMSUN, KOSDA. Nothing is invented for a name that is absent.

Tiers are labels on the stored row. They do not size, trigger, or promote.

| Label | Names | What the row means |
|---|---|---|
| Blocked, store only | CASHCAT, PONS | Kept so the book is complete. Not an input to a call. |
| Monitor | JUP, NIL, DRV | Kept. Membership stays monitor until the Principal promotes it. |
| Unlabelled | The other bound perps and the 17 closes | Stored under the same store-only rule. |

The equity call uses one session date, not a range. Hyperliquid rows carry no exchange event time (`market_time` empty). An equity row keeps the vendor bar time on `market_time` when the vendor sent one. Knowledge time is the capture time: `as_of_knowledge` and `ingested_at` are that same timestamp. A reader asking what was known at T uses the capture time.

There is no fixed Sydney slot and no default clock inside this path. The capture time is the time the caller supplies, stored in UTC. A Sydney morning stamp is the matching UTC instant. An off-window time is stored as given.

The same number at a later time is a new observation. It does not replace the earlier print, and it is not recorded as a contradiction. The capture time is part of the observation's identity.

History before the first capture is not reconstructed. There is no backfill on this path.

The command that exists on the draft runs from a fixture and does not open a database. `LIVE_NEON_ENABLED` stays false. The landing below is what a capture contains when the writer runs. It is not a statement that overnight rows are already in Market Memory.

## What lands on capture 1, capture 2, and capture 3

"Capture 1, 2, and 3" means the first three times this set is taken, in order. Each of those times still makes the same three HTTP calls.

### Capture 1

Levels only.

- 57 bound-perp observations: open interest, funding, and `mid_px` for each of the 19, including PURR.
- One DRV observation: `mid_px` from the spot pair, when the pair is the real DRV/USDC at index 700.
- 17 equity closes for the session date.
- No prior time, no `interval_seconds`, and no pair mark.
- No quadrant, no quadrant label, no open-interest change, and no price change.

A field that is missing still has a row. The value is empty and the quality is partial. See [a null mid](#what-a-null-mid-does).

### Capture 2

A second set of the same 75 levels, at the second real timestamp.

When the caller supplies capture 1's timestamp, and that timestamp is strictly earlier, every row of capture 2 also carries:

- the prior capture time
- `interval_seconds`, the elapsed seconds between the two real timestamps
- a pair mark of consecutive capture (stored as `consecutive_capture`)

That stamp is the raw material for a later delta. It is not the delta. Quadrant deltas are not computed in #122. Capture 2 does not add a quadrant, a quadrant label, an open-interest change, or a price change.

If the caller does not supply a prior time, capture 2 lands as capture 1 does: levels only, no interval, no pair.

### Capture 3

A third set of the same 75 levels, at the third real timestamp.

The row remembers one prior, the one the caller supplies. Pointed at capture 2, capture 3 records the interval from capture 2 to capture 3 only. The interval from capture 1 to capture 2 stays on capture 2's rows. Capture 3 does not carry a three-point bundle.

Quadrant deltas are still not computed.

If the prior is omitted, capture 3 lands as a first capture and the pair chain breaks at that point.

A prior that is not strictly earlier is refused. That attempt does not count as a capture and does not write a pair. Two stamps at the same instant are not a pair.

## What stays insufficient, and why

This path does not write a Quant verdict. "Insufficient" here means the retain set cannot support that claim yet. Empty stays empty.

| What | Why it stays insufficient |
|---|---|
| Any quadrant reading, including after capture 2 and capture 3 | The draft stores levels and, once a prior time is supplied, the elapsed seconds. It does not compute a quadrant. A flag on the 19 bound perps says they are eligible for one later. Eligibility is not a result. |
| Capture 1, for every name | There is no prior print. A change cannot be stated. |
| DRV, on every capture | Price only. One mid. No open interest and no funding, so a quadrant has nothing to stand on. A non-null DRV mid is still only a price. |
| The 17 equity closes, on every capture | A session close is a chart print. These rows are not eligible for a quadrant. |
| A null or absent field | The row is partial. The value stays empty. A null mid is not zero, and it is not the mark. A missing close is not taken from another ticker. |
| Names outside the 37 | KNT, KNTQ, and the venue queue are not retained. No stand-in row is written. |
| Anything before capture 1 | No backfill. The past is not filled in. |
| Blocked and monitor labels | CASHCAT and PONS are stored as blocked. JUP, NIL, and DRV are stored as monitor. Storage is not a verdict and not a promotion. |
| A live book in Neon | The draft command does not persist. Until the Principal allows a database write in a later decision, these captures are not in Market Memory. |

A bound perp that is missing from the perp snapshot still produces three rows, all empty. An equity call that fails, or a missing Polygon key, still produces 17 close rows, all empty. The perp rows and the DRV row from the other calls still land. Closes are not invented. A DRV pair that is absent or is not actually DRV/USDC at index 700 produces one empty mid row, and no open-interest or funding row.

## When the first quadrant delta can be computed

The earliest pair is capture 2 against capture 1.

That pair is usable as raw material only when all of the following are true:

- Both captures exist, with the real timestamps the caller supplied. There is no stand-in clock.
- Capture 2 was given capture 1's timestamp as its prior, and that prior is strictly earlier.
- `interval_seconds` is present on capture 2. It is present only in that case.
- The name is one of the 19 bound perps.
- Open interest and `mid_px` are both present on both captures. A null on either leg leaves that leg empty.

The eligible flag is on all 19 bound perps, including the blocked names CASHCAT and PONS. The flag does not lift the blocked label, and the value test still refuses those two names as hits. JUP and NIL carry the flag and the monitor label together.

Funding is stored on those rows. This draft does not define how funding would enter a quadrant.

**The delta itself is not computed in #122.** Capture 2 and capture 3 do not write a quadrant, a quadrant label, an open-interest change, or a price change. A later change would have to read the stored pair and compute it. This contract does not authorize that change. Until then, a quadrant claim is insufficient, including on the first clean pair.

Capture 3 adds a second pair (capture 2 → capture 3). It does not go back and compute the first pair.

DRV and the equity closes never become that pair. Their rows can carry `interval_seconds` when a prior was supplied. That number is the gap between captures. It is not a quadrant.

## What a null mid does

A null or missing `midPx` leaves `mid_px` empty. The row is partial.

The mark (`markPx`) stays the mark. It is not copied into `mid_px`.

On a bound perp, open interest and funding still land when those fields are present. Only the mid row is empty. On DRV there is only the mid row, so a null mid is the whole DRV print for that capture, and it is still partial.

An honest null is the accepted print. The writer will keep writing null for as long as the source has no mid.

**Revisit rule.** If the same instrument's mid is null on three captures in a row, reopen the source question: empty book, or the wrong instrument. The revisit is a human look at the source. It is not a prompt to fill the mid from the mark.

## What a missed session does to the pair chain

A session that does not run writes nothing. There is no placeholder, no late mark, and no filled price for the gap.

This path has no schedule, so it does not notice that a morning was skipped. The next capture behaves entirely according to the prior time it is given.

- Given the last successful capture time, the new capture is still marked a consecutive pair, and `interval_seconds` is the whole gap. The missed morning is not inserted between them. The chain does not grow a hole marker. It grows a longer interval.
- Given no prior, the new capture lands as a first capture. Levels only. The pair chain restarts. Later deltas cannot bridge the gap unless a caller points a capture back at an earlier real timestamp.

The morning log in the value test is where a person records that a session was missed. The retain rows themselves will not say so.

## A 14 hour interval and a 26 hour interval

They are treated the same.

| Gap | `interval_seconds` | Pair mark | Late? | Split into a miss plus a session? |
|---|---|---|---|---|
| 14 hours | 50400 | consecutive capture | no | no |
| 26 hours | 93600 | consecutive capture | no | no |

Both are the elapsed seconds between the two real timestamps. Both are accepted. Neither is a different kind of pair. There is no slot window that would call 26 hours late and 14 hours on time. A fresh print is not marked stale because the previous capture was further away. The only interval that is refused is one that is zero or negative.
