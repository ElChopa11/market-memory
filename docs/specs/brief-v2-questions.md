# Brief v2 — seven questions

**Status.** Principal reading copy, 2026-09-24. Paper only. Docs only. This page does not build a panel, merge a draft, enable Neon, start a cron, send Telegram, or edit a brief renderer.

The seven questions are the brief's purpose. The template is layout. A panel that cannot answer its question renders the house fallback below. It does not grow a sentence to fill the gap.

Nothing in brief v2 ships before the Friday dual-cron prove. This page does not record that prove.

## Binding sources

Token names and stages come only from the mapping. Message numbers come only from the template. Both files are on unmerged draft [#109](https://github.com/ElChopa11/market-memory/pull/109) (`cursor/brief-v2-stage-a-3e6c`). They are not on this branch.

- Template (Messages 1–8): [`docs/specs/brief-v2-template.md`](https://github.com/ElChopa11/market-memory/blob/cursor/brief-v2-stage-a-3e6c/docs/specs/brief-v2-template.md)
- Token source of record: [`docs/specs/brief-v2-mapping.md`](https://github.com/ElChopa11/market-memory/blob/cursor/brief-v2-stage-a-3e6c/docs/specs/brief-v2-mapping.md)
- Stage narrative on the same draft (not a second token list): [`docs/specs/brief-v2.md`](https://github.com/ElChopa11/market-memory/blob/cursor/brief-v2-stage-a-3e6c/docs/specs/brief-v2.md)
- MVP retain behaviour: [`docs/specs/mvp-retain-capture-contract.md`](https://github.com/ElChopa11/market-memory/blob/cursor/mvp-retain-principal-docs-3554/docs/specs/mvp-retain-capture-contract.md) on draft [#125](https://github.com/ElChopa11/market-memory/pull/125), describing draft [#122](https://github.com/ElChopa11/market-memory/pull/122)
- Retain allowlist: [`config/ingest/mvp_retain.yaml`](https://github.com/ElChopa11/market-memory/blob/cursor/mvp-retain-forward-only-3151/config/ingest/mvp_retain.yaml)

No token in this file is new. No token is filled by an LLM.

## Classes and glyphs

Each question has one primary class. Other classes appear in the prose only as limits on a part of the same question.

| Class | Meaning |
|---|---|
| `fillable_now` | A live slot or an approved calendar file can fill the cell without Neon and without a new source. |
| `needs_capture_history` | The cell is a delta, a z-score, a quadrant, or a correlation. The mapping stages it Neon. MVP retain is the capture path that can supply consecutive prints. |
| `needs_source_we_do_not_hold` | The series is not on a feed this lab is allowed to print. |
| `structurally_unanswerable` | The question asks for a cause or a narrative. Omit it. A sequence of signs is not a substitute. |
| `fillable_when_thesis_exists` | The cell is a stated threshold from a thesis card. Empty until that card exists. No external feed is required. |

House glyphs, from the mapping (icon file on #109: `config/briefing/presentation.yaml` `states.unavailable.icon` = ⚪):

| Situation | Render |
|---|---|
| Missing level | ⚪ `unavailable`. The field stays on the card. |
| Δ, z30d, correlation, regime, scenario condition, key takeaway | `INSUFFICIENT DATA` |
| Positioning confidence | `INSUFFICIENT HISTORY` |
| Dominant driver | `indeterminate` |
| Event list with nothing in the window | `none scheduled` |
| Why-narrative, and the optional What Changed add-on | omit the panel |

VIX Last is structural unavailable (Cboe entitlement; VIXY/UVXY are not a proxy). That is a missing source, not a Neon gap.

## Summary

| # | Question | Message | Primary class |
|---|---|---|---|
| 1 | What happened | 2 (deltas also on 3 and 4) | `needs_capture_history` |
| 2 | Why | 3 (news row on 6) | `structurally_unanswerable` |
| 3 | Positioning | 5 | `needs_capture_history` |
| 4 | Market pricing | 5 (basis and funding level) | `fillable_now` |
| 5 | What changed | Δ columns on 2, 3, 4, 5; add-on omitted | `needs_capture_history` |
| 6 | What matters next | 6 | `fillable_now` |
| 7 | What would invalidate | 7 | `fillable_when_thesis_exists` |

Principal read, corrected where the mapping or the live renderer disagrees: Q1 is Last-only on brief v2, and Δ1D needs history. Q2 is omit. Q3, Q5, and Q7 match the provisional map. Q4 and Q6 match the "partially now" lean; the earnings fraction is 0/8.

## 1. What happened

**Question.** What happened.

**Panels.** Message 2 (Market Dashboard): Last, Δ1D, Δ5D, Δ20D. The same Δ columns repeat on Message 3 (Macro) and Message 4 (Crypto tape, plus 20d BTC vs NDX correlation). Message 1 `{3_SENTENCE_SUMMARY}` is not this answer. Its rule is `INSUFFICIENT DATA` until a restatement-only generator exists, and that generator may only restate rendered values.

**Tokens.** `{VAL}` for Last, and for Δ1D / Δ5D / Δ20D / `corr20d`. `{ICON}` is data-state health, not the direction of the move. The mapping's stage cell for `{VAL}` says `now` because Last is now. The same row then says: do not fill Δ1D, Δ5D, Δ20D, z30d, or corr20d until Neon.

**Inputs.** Last, where a live slot exists: Polygon `AssetPrint.last` for ES/SPY, NQ/QQQ, DXY/UUP, CL/USO; FRED `DGS10` for US10Y; Hyperliquid `mid_px` for BTC and ETH. NDX Last is the QQQ print, labelled as not the NDX index and not NQ futures. VIX has no proxy. 2s10s, Gold, Credit, SOL, ZEC, XMR are Unverified in the `{VAL}` row. Δ1D in the mapping is `(last - prior_close) / prior_close` from stored prints. Δ5D and Δ20D are stored prints. corr20d uses the QQQ proxy with that label.

**Fillability.** Primary: `needs_capture_history`.

Last is `fillable_now` for the slots named above. Last is a level. "What happened" is the move. The mapping withholds every Δ until Neon and sets the Δ fallback to `INSUFFICIENT DATA`. Δ5D, Δ20D, and corr20d are the same class.

**Live pulse, checked on main.** The current close/pre-open table is not brief v2. Its columns are Last, Prior close, and Change (`mm_briefing.render._asset_table`). Change is `AssetPrint.change_pct`: `(last - prior_close) / prior_close` when both numbers exist.

- Polygon daily aggs (`_parse_polygon_aggs`, lookback `config/briefing/macro.yaml` `live.polygon.lookback_calendar_days: 10`) set `prior_close` to the previous bar's close inside that same response. That Change prints without Neon. It is one prior bar. The parser does not compute a 5-day or 20-day return.
- FRED (`_fetch_fred`, `limit: 2`) sets `prior_close` to the previous observation in that same response. US10Y can print a basis-point Change without Neon. It is not a 5-day or 20-day window.
- BTC and ETH on the table are Hyperliquid `mid_px`. `apply_crypto_pulse_from_hl` sets `prior_close` to null. The runbook states the rule: do not invent a 24h move from a single mid (`docs/runbooks/market-pulse.md`, crypto pulse source of record).

So the live brief does print a one-step Change for Polygon proxies and for FRED without Neon. It does not print a BTC/ETH Δ1D. Brief v2 still does not adopt that vendor prior as the Message 2 Δ1D cell. The mapping forbids the fill until Neon.

**When it cannot answer.** Δ1D, Δ5D, Δ20D, and corr20d render `INSUFFICIENT DATA`. A missing Last renders ⚪ `unavailable`. VIX Last renders ⚪ `unavailable`. Do not copy the live pulse Change column into the v2 Δ cells.

**Principal read.** Corrected. "Answerable now via Last + Δ1D" does not hold for brief v2. Last-only now. Δ1D needs history.

## 2. Why

**Question.** Why.

**Panels.** Message 3 TRANSMISSION CHAIN and DRIVER. Message 6 NEWS IMPACT MATRIX is the headline form of the same question. Message 1 key takeaway is a restatement slot, not a cause.

**Tokens.** `{RATES_DIR}`, `{USD_DIR}`, `{EQ_DIR}`, `{RISK_DIR}`, `{DOMINANT_DRIVER_OR_"indeterminate"}`, `{3_SENTENCE_SUMMARY}`, `{STORY}`, `{ASSET}`, `{DIR}`, `{MAG}`, `{CONF}`. No other driver token exists.

**Inputs.** `{RATES_DIR}` is `sign(Δ1D)` on US10Y / `DGS10`, staged Neon. `{USD_DIR}` is `sign(Δ1D)` on DXY / UUP, staged Neon. `{EQ_DIR}` is `sign(Δ1D)` on an equity slot the mapping says is not named (ES vs NQ), staged Neon. `{RISK_DIR}` has no risk series, staged later. `{DOMINANT_DRIVER_OR_"indeterminate"}` has no versioned driver rule, staged later, and the derivation says a versioned config rule only, not an LLM read of the tape. `{STORY}` has no news scraper, staged later. `{3_SENTENCE_SUMMARY}` is `INSUFFICIENT DATA` until a restatement-only generator is coded; the future rule forbids "suggests" and "indicates".

**Fillability.** Primary: `structurally_unanswerable`.

A chain of signs is a sequence of moves. "Rates moved and equities followed" is correlation written as a cause. The mapping gives those arrows no causal formula. Filling DRIVER with that sentence would fabricate the answer the question asks for.

A later versioned rule may emit a label from stored signs. That label is a ranking of moves. It is still not a cause, and it does not exist today. The fallback word is `indeterminate`.

News does not repair this. Yahoo is `licence_verdict: prohibited` in `config/ingest.yaml` (IMP-036: no Yahoo HTTP). Benzinga is rejected for Telegram reprint in `ops/reports/source-evaluation/2026-09-18.md` (no redistribution licence). Whale Alert has no row in this repo (Unverified). `{STORY}` stays later either way. A lawful headline would still need a non-LLM binding rule before it could sit in the matrix, and no such rule is in the mapping.

**When it cannot answer.** Omit the why-narrative. Do not add a sentence under DRIVER. If the Message 3 lines stay as layout: direction tokens render ⚪ `unavailable`; DRIVER renders `indeterminate`; `{3_SENTENCE_SUMMARY}` renders `INSUFFICIENT DATA`; `{STORY}` renders ⚪ `unavailable`. Prefer omit over a chain sentence, including after Neon signs exist.

**Principal read.** Confirmed, and tightened. The panel does not become fillable by waiting on Neon. Neon supplies signs. Signs are not a why. Omit.

## 3. Positioning

**Question.** Positioning (who is positioned, and whether that position is building or exiting).

**Panels.** Message 5 (BTC POSITIONING, ETH POSITIONING, OI × PRICE STATE, POSITIONING CONFIDENCE).

**Tokens.** `{VAL}` for price, open interest, funding, basis, liquidations, and CB premium, including their Δ1D and z30d uses. `{QUADRANT_LABEL}`. `{ICON}` for the quadrant (the mapping says the quadrant icon waits on `{QUADRANT_LABEL}`). `{BAR}`. `{CONFIDENCE_OR_"INSUFFICIENT HISTORY"}`.

**Inputs.** Current HL levels the mapping marks now: `mid_px`, `open_interest`, `funding`, `basis_mark_oracle` (mark minus oracle, `mm_briefing.hl.basis_mark_oracle`), `liquidation_size_sum`. Quadrant formula, staged Neon: `sign(Δprice) × sign(ΔOI)` with `Δprice = (last - prior_close) / prior_close` and `ΔOI = (oi - oi_prior) / oi_prior`. z30d is `(x - mean30) / stdev30` from stored prints. CB premium is Unverified in the `{VAL}` row. `{BAR}` has no scale in the repo. Confidence has no signal log.

Live OI change exists only when a prior `open_interest` observation is already in memory (`hl_from_memory` sets `prior_open_interest`). The live snapshot path does not invent that prior. Instruments on the current brief are BTC and ETH (`HL_BRIEF_INSTRUMENTS`).

**MVP retain unlock (#122, as read by the #125 contract).** One capture stores levels: open interest, funding, and `mid_px` on 19 bound perps, including BTC and ETH. Capture 1 has no prior, no price change, and no OI change. Capture 2, given capture 1's timestamp, stores the prior time and `interval_seconds`. It still does not write a quadrant, an OI change, or a price change. The earliest pair that could be read later is capture 2 against capture 1, and only when both mids and both open-interest values are present. DRV is price-only. Equity closes are not quadrant-eligible. The retain metric list does not include mark, oracle, basis, or liquidations, so this path does not store the basis series or the liquidation series.

z30d needs a 30-print mean and standard deviation. Two captures do not unlock it.

**Fillability.** Primary: `needs_capture_history`.

Levels (mid, open interest, funding, mark−oracle basis, liquidation sum) are `fillable_now` on the live HL snapshot when the field is present. The positioning question is the change of state: OI Δ, funding z, quadrant. Those wait on stored pairs. CB premium is `needs_source_we_do_not_hold` until Intel names a source (mapping: Unverified). `{BAR}` is later.

**When it cannot answer.** Price Δ, OI Δ, z30d, and `{QUADRANT_LABEL}` render `INSUFFICIENT DATA`. Quadrant `{ICON}` renders ⚪ `unavailable` until the label exists. `{BAR}` renders ⚪ `unavailable`. Confidence renders `INSUFFICIENT HISTORY`. A missing level renders ⚪ `unavailable`. The four-line legend in the template (price↑ OI↑ = long build, and the three siblings) is layout, not a filled quadrant. Do not light one of those lines from a single snapshot.

**Principal read.** Confirmed. Needs capture history. Message 5. Two captures are the raw material for a later quadrant on the 19 bound perps. They are not the quadrant, and they are not z30d.

## 4. Market pricing

**Question.** What the market is pricing (the level of carry and basis, not the story of why).

**Panels.** Message 5 rows FUNDING, BASIS, and their z30d cells. CB PREMIUM on the same message is a separate Unverified slot. Message 5 does not contain an options-skew row or a CME term row; those tokens were not created.

**Tokens.** `{VAL}` for funding Last, basis Last, funding z30d, basis z30d, and CB premium. `{BAR}` beside the z cells, staged later.

**Inputs.** Funding Last is the live HL `funding` metric (`funding_value`). Basis Last is `basis_mark_oracle`: mark minus oracle on the same snapshot. Both are in the mapping's "current HL levels" list under `{VAL}` / stage now. z30d is Neon. There is no mapped token for an options skew, a CME futures curve, or a VIX term structure.

What this lab does not hold, from `docs/runbooks/market-pulse.md` and `ops/reports/source-evaluation/2026-09-18.md`: true CME ES/NQ/CL (ETF proxies only), Cboe VIX and VIX term (unlicensed JSON is not a source), Polygon options OI (not on the stocks plan). HL basis here is one perp versus its oracle. It is not a term structure.

MVP retain stores funding, so a later funding z could be computed from those rows after a 30-print window. It does not store mark or oracle, so basis z is not in that allowlist. #122 does not compute either z.

**Fillability.** Primary: `fillable_now`.

The honest "priced now" cells are funding level and HL mark−oracle basis. z30d is `needs_capture_history`. Options skew and CME term are `needs_source_we_do_not_hold`. CB premium is Unverified (`needs_source_we_do_not_hold` until a source is named). VIX is structural unavailable, not a stand-in for skew.

**When it cannot answer.** Funding or basis missing on the snapshot: ⚪ `unavailable`. z30d: `INSUFFICIENT DATA`. `{BAR}`: ⚪ `unavailable`. Do not draw a curve from one basis number.

**Principal read.** Confirmed as partially now. Basis level and funding level can fill. z30d needs history. "Term where we have it" is the single HL mark−oracle basis, not a CME strip and not an options skew.

## 5. What changed

**Question.** What changed.

**Panels.** Every Δ column already on Messages 2, 3, 4, and 5 (Δ1D, Δ5D, Δ20D, OI Δ1D, vs BTC where mapped). The template Notes say the "What Changed?" panel and the "Anomaly Radar" are optional add-ons, not drawn, until history retention is confirmed. There is no `{WHAT_CHANGED}` token. This file does not add one.

**Tokens.** `{VAL}` in its Δ uses, and `{QUADRANT_LABEL}` where the change is a state rather than a percent. Same Neon rule as questions 1 and 3. corr20d is a change-in-relationship cell on Message 4 and follows the same fallback (`INSUFFICIENT DATA`).

**Inputs.** Stored prints. The live pulse "What changed since prior US close" section is a different artifact: Polygon and FRED can show a one-step Change from the vendor's previous print (see question 1), and HL OI change renders only when a retained observation exists. The section says missing slots stay unavailable. That behaviour is not a brief-v2 Δ column.

MVP retain capture 1 is levels only. Capture 2 stores an interval when the prior timestamp is supplied, and still writes no price change and no OI change (capture contract). A cell that says "what changed" stays empty through capture 2. A later reader could compute a one-step delta from that pair. Δ5D, Δ20D, and z30d need a longer window than two captures. There is no backfill on the retain path.

**Fillability.** Primary: `needs_capture_history`.

**When it cannot answer.** Omit the optional What Changed add-on and the Anomaly Radar. Δ cells that sit inside Messages 2–5 render `INSUFFICIENT DATA`. Do not print a zero for a missing prior.

**Principal read.** Confirmed. Needs history. Empty until consecutive captures exist, and empty on the card until a later change actually computes the delta. #122 does not do that compute.

## 6. What matters next

**Question.** What matters next.

**Panels.** Message 6 CATALYST RADAR and the dated-event line. The NEWS IMPACT MATRIX on the same message is question 2, not this one.

**Tokens.** `{EVENT_LIST_OR_"none scheduled"}` (stage now). `{BAR}` and `{LEVEL}` on the five region rows (stage later, Unverified). `{DATE}` is the brief stamp, not an event.

**Inputs.** The mapping binds the event list to `config/briefing/calendar.yaml` through `mm_briefing.calendar.relevant_events`. The derivation is: list events in the existing look-ahead window. Not a news scraper. Fallback: `none scheduled`.

The live engine uses two windows. Pre-open calls `relevant_events` with the function default (36 hours ahead, 6 hours back). Close calls it with 24 hours ahead and no lookback (`generate_close`). An empty window is printed, not invented.

That file is a frozen March 2026 fixture: CPI YoY, 10Y auction, FOMC speaker. Zero earnings rows. On 2026-09-24 those three timestamps sit outside both windows. Pre-open then prints "None in the look-ahead window." Close prints "No dated catalysts remaining in the look-ahead window." The runbook states there is no live calendar API.

Gate 5 uses a different file, `config/macro/event_calendar.yaml`. It is not the Message 6 source of record. It currently holds one earnings row: BB (`NYSE:BB`) on 2026-09-24, verification Verified. BB is on `config/watchlist/monitor.yaml` at tier `monitor`. BB is not in `config/universe.yaml` `equities`.

**Earnings-date fraction (equity universe).** Denominator is the locked membership list `config/universe.yaml` `equities`: NVDA, AVGO, SMH, MSFT, META, JPM, XLF, XOM. Eight names. The thesis-priority subset `in_universe.equities` is six (NVDA, AVGO, MSFT, META, JPM, XOM).

Dated earnings rows in `config/briefing/calendar.yaml`: none. Dated earnings rows in `config/macro/event_calendar.yaml` whose ticker is in that eight: none. **0/8** of the equity universe has an earnings date wired. **0/6** of `in_universe` equities as well. The one wired earnings date in the gate-5 file is BB, outside that universe.

`config/ingest.yaml` sets `equities.earnings.enabled: true` with a Polygon events path. That client is not the brief calendar. The 2026-09-18 source evaluation says Polygon earnings on this plan often return 403 and must stay unavailable rather than invent a date. No universe name has a stored earnings date from that path in config.

**Fillability.** Primary: `fillable_now`.

The event list can render today. With the current fixture and today's date, the honest render is an empty window (`none scheduled` on the v2 token; pre-open "None in the look-ahead window."; close "No dated catalysts remaining in the look-ahead window."). Region bars and `{LEVEL}` are later (`needs_source_we_do_not_hold` until Intel names a non-LLM scale). Earnings coverage for the equity universe is not a hidden feed. It is unwired: 0/8.

**When it cannot answer.** Dated events: `none scheduled`. Region `{BAR}` and `{LEVEL}`: ⚪ `unavailable`. Do not promote the BB gate-5 row into Message 6 by implication, and do not invent earnings dates for the eight universe names.

**Principal read.** Confirmed as partially now, and the coverage number is measured: 0/8, not a rounded estimate.

## 7. What would invalidate

**Question.** What would invalidate.

**Panels.** Message 7 INVALIDATION CONDITIONS (three bullets). The BTC SCENARIO MAP above those bullets is a different grid (`{LABEL}` / `{CONDITION}` per OI×price cell). It is not a substitute for a thesis invalidation.

**Tokens.** `{CONDITION_1}`, `{CONDITION_2}`, `{CONDITION_3}`. The scenario grid uses `{LABEL}` and `{CONDITION}`. All five are staged later. Derivation: no formula, no scenario config. Fallback: `INSUFFICIENT DATA`. Not an LLM.

**Inputs.** A thesis card that already states a threshold and the level it is compared to. No HL, Polygon, FRED, calendar, or news input. The mapping's "needs Intel" mark is the missing config binding, not a missing market feed.

Checked on main: no `research/**/thesis.md`. The live close brief prints "No indexed theses to score against this session." when the thesis list is empty (`render` close path). `config/briefing/watchlist.yaml` contains BTC and ETH `invalidation` strings for the pre-open watchlist. Those lines are fixture watchlist copy. They are not a thesis card and they are not Message 7.

**Fillability.** Primary: `fillable_when_thesis_exists`.

Empty because there is no thesis. Not because a print is missing.

**When it cannot answer.** Each condition bullet renders `INSUFFICIENT DATA`. Scenario `{LABEL}` and `{CONDITION}` render `INSUFFICIENT DATA`. Do not copy the watchlist fixture strings into the bullets. Do not derive a threshold from price, OI, or funding.

**Principal read.** Confirmed. We own this panel. It is the cheapest high-discipline card, and it stays empty until a thesis states the invalidation. Do not build it against the tape.

## Build order

Do not implement these panels in this change.

1. Omit question 2. Do not author a transmission sentence, a dominant-driver paragraph, or a news-impact row. `indeterminate` and ⚪ are the layout if the lines remain. A Neon sign chain does not promote this question out of omit.
2. Question 7 when a thesis exists. Bind `{CONDITION_1}`–`{CONDITION_3}` to that card's stated threshold versus its stated level. Until then the bullets stay `INSUFFICIENT DATA`. No external data.
3. Question 3 after MVP retain captures exist. The raw pair starts at capture 2 against capture 1 for a bound perp with both mids and both open-interest values. Computing the quadrant is a later change; #122 does not compute it. z30d waits on a 30-print window, which two captures do not provide. Funding is in the retain set; basis mark/oracle and liquidations are not.
4. Question 1 and question 5 Δ columns stay `INSUFFICIENT DATA` until the mapping's Neon stage is actually bound. Last on question 1 may show for the named live slots. Do not treat the live pulse Change column as that binding.
5. Question 4 may show funding level and HL mark−oracle basis as Last. z30d stays `INSUFFICIENT DATA`. Skew and CME term stay omitted.
6. Question 6 may show `{EVENT_LIST_OR_"none scheduled"}` from `config/briefing/calendar.yaml`. Earnings dates for the equity universe stay absent (0/8) until a Principal-approved calendar row exists. Do not scrape a date.

Sequencing hold: no brief-v2 panel ships before the Friday dual-cron prove. This page does not start that prove and does not report it.

## Holds this page does not touch

Drafts left untouched: #122 (MVP retain), #119 (Polygon session freshness), #120 (Neon runbook), #109 (brief v2 Stage A), #118 (Sydney morning dispatch), and the crypto-pulse item (a) in the market-pulse runbook. No PAT change. No workflow, cron, Telegram, retain, Neon write, or brief-path code change. `brief-v2-mapping.md` and `brief-v2-template.md` are not edited here.
