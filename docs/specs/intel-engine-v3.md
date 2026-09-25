# Intel engine v3

Docs only. Paper only. This file does not author a panel, change a renderer, open Neon, send Telegram, or start a workflow.

Principal proposal of 25 Sep 2026: twenty brief segments, plus an engine (market / macro / news, then normaliser, regime detector, momentum / positioning / anomalies, signal engine, confidence engine, scenario generator, visual engine, Telegram). Numbers in the proposal and in the two attached mockups (heatmap, three charts) are illustrative. They are not prints.

Build stays frozen through the eleven-capture test in [eleven-capture-test.md](eleven-capture-test.md). Captures 2–11 are the scored mornings (Mon 28 Sep 2026 through Mon 12 Oct 2026). Capture 1 is Mon 28 Sep 2026 and is not scored. Continue only if the Principal's informative count is at least 3/10. A count of 0–2/10 is stop. The scoresheet dates in that file are still blank; this page uses the dates above as the calendar for history math.

## Status words

| Word | Meaning in this file |
|---|---|
| HELD | The Sydney morning retain writes an `observation` row for it. Cite below. |
| FETCHED NOT STORED | A morning or brief path requests it and does not write the retain row. |
| FREE AND UNWIRED | A free source is named in this repo and the morning capture does not call it. |
| PAID | A vendor or tier already named in config. No purchase is assumed. |
| UNAVAILABLE | No fetcher in this repo, and no free source was verified here. |
| Unverified | The code path was read; a live vendor body or a Neon row was not. |

A missing input renders as a gap. It does not render as zero.

Weekdays only, from capture 1 = Mon 28 Sep 2026. No holiday calendar (the retain path already has none: [docs/runbooks/mvp-retain.md](../runbooks/mvp-retain.md)).

| Captures stored | Calendar date | What that count is |
|---|---|---|
| 1 | Mon 28 Sep 2026 | Levels only. No delta. |
| 2 | Tue 29 Sep 2026 | First prior. `trailing_return` with `bars=1` (`packages/quant/src/mm_quant/mathutil.py`) needs 2 prices. |
| 5 | Fri 2 Oct 2026 | Five prints. Not a 5-session return. |
| 6 | Mon 5 Oct 2026 | `trailing_return(..., bars=5)` needs 6 prices. |
| 11 | Mon 12 Oct 2026 | Last scored capture. |
| 20 | Fri 23 Oct 2026 | `sma(..., window=20)` (`mathutil.py`). Inside the test window a 20-session average does not exist. |
| 21 | Mon 26 Oct 2026 | `trailing_return(..., bars=20)` and 20 close-to-close returns. |
| 50 | Fri 4 Dec 2026 | `sma(..., window=50)`. |

The morning job writes the capture after it renders the brief. `.github/workflows/hybrid-sydney-morning.yml` runs `lab brief close --live --no-db`, then `lab retain morning`, then one `lab deliver pack`. The brief does not read the rows it is about to store. Stored history does not appear in the message until a reader is built. That reader is not on main.

## What main stores

There is no capture table. Alembic heads at `0012_heartbeat_if_not_exists` (`packages/memory/src/mm_memory/migrations/versions/0012_heartbeat_if_not_exists.py`). Revisions `0011` and `0012` create `schedule_heartbeat`. The retain writer inserts `observation` rows from revision `0001` (`0001_phase1_market_memory_core.py`). `payload_json.retain_series` is `mvp_retain`. `as_of_knowledge`, `ingested_at`, and `published_at` are the capture time. Equity `market_time` is the vendor bar time when the bar has `t`. Hyperliquid `market_time` is null (`packages/ingest/src/mm_ingest/mvp_retain.py`, `docs/runbooks/mvp-retain.md`).

One morning capture, three HTTP calls (`config/ingest/mvp_retain.yaml`):

| Call | Request | Rows written |
|---|---|---|
| 1 | Hyperliquid `metaAndAssetCtxs` (`mm_ingest/hl_info.py`) | 19 perps × `open_interest`, `funding`, `mid_px` |
| 2 | Polygon grouped daily, one session date (`mm_ingest/equities/polygon.py` via retain) | 17 closes, metric `close` |
| 3 | Hyperliquid `spotMetaAndAssetCtxs` | DRV `mid_px` only, spot index 700 |

75 rows, 37 instruments, when every field lands. A null stays null. `quadrant_eligible` is a boolean on the payload. No `quadrant` or `quadrant_label` metric is written (`docs/runbooks/ingest.md`). DRV is not quadrant-eligible.

Bound perps: BTC, ETH, SOL, JUP, HYPE, LIT, NEAR, ARB, UNI, VVV, ZEC, DOGE, XMR, CASHCAT, PONS, CHIP, LTC, NIL, PURR. Equity closes: QQQ, CRCL, TSLA, SPCX, NVDA, BB, GLXY, IBIT, BMNR, MRNA, GOOG, HOOD, NOW, CBRS, MSTR, STRC, AMD. CASHCAT and PONS are `blocked`. JUP, NIL, and DRV are `monitor`. Store-only. Not a call.

Each Hyperliquid row stores the asset-context object on `payload.raw` (`_policy_payload`). The writer reads `midPx` / `funding` / `openInterest` only (`_HL_FIELDS`). Other keys on that object, if the vendor sent them, are stored and unused. Mark, oracle, and `prevDayPx` were not confirmed on a live row. This page does not treat them as parsed metrics.

Each equity row stores the grouped-daily object on `payload.raw` and reads `c` and `t` only. Other keys on that object, if sent, are stored and unused. Open, high, low, volume, and the vendor daily VWAP were not confirmed by a live read.

`prior_captured_at` and `interval_seconds` are stamped when an earlier non-proof capture exists (`_stamp_interval`). Proof rows (`capture_kind=proof`) are excluded from that prior (`docs/runbooks/mvp-retain.md`).

## What the morning brief fetches and does not store

`lab brief close --live --no-db` (`apps/lab-cli/src/mm_lab_cli/briefing.py`, workflow above). `--no-db` skips the `brief` table from migration `0003`.

`config/briefing/macro.yaml` `live.polygon.symbols`: ES→SPY, NQ→QQQ, DXY→UUP, CL→USO. VIX is `structural_unavailable` (Cboe entitlement; the same note says VIXY is not VIX). `live.fred.series` is US10Y→`DGS10` only. `limit` on that FRED request is 2 (`mm_briefing/fetchers.py` `_fetch_fred`). Polygon aggs use `lookback_calendar_days: 10` and set `prior_close` from the previous bar in that response. That one-step change is the vendor's prior bar. It is not a Neon delta.

Crypto table slots are Hyperliquid `mid_px` for BTC and ETH (`HL_BRIEF_INSTRUMENTS` in `mm_briefing/models.py`). `apply_crypto_pulse_from_hl` leaves crypto `prior_close` empty, so the table does not invent a BTC or ETH 1-day change from one mid. CoinGecko is fetched on `--live` as a secondary check (`macro.yaml` `crypto_pulse`). Those prints stay in notes. They are not retain rows.

The live Hyperliquid snapshot for the brief (`mm_briefing/hl.py` `hl_from_live_info`) requests `metaAndAssetCtxs` and `recentTrades` for BTC and ETH. It is not written by retain. `recentTrades` liquidations are trades that carry a `liquidation` object (`mm_provenance/normalize.py` `normalize_liquidations`). An empty window is not a stored zero. `liquidation_size_sum` still returns `0.0` when the list is empty (`mm_briefing/hl.py`), and the close renderer prints that sum (`mm_briefing/render.py` `_hl_section`). That print is the gap-as-zero failure this spec forbids.

Basis on the brief is mark minus oracle in memory (`basis_mark_oracle`). Retain does not write a basis metric.

## Free and unwired, paid, unavailable

These clients and series exist. The morning capture does not call them.

| Input | Status | Where |
|---|---|---|
| Hyperliquid `fundingHistory`, `candleSnapshot` | FREE AND UNWIRED | Allowlist in `mm_ingest/hl_info.py`. `ingest_from_client` in `mm_ingest/pipeline.py` can persist them. No workflow runs that ingest. The morning path stores one funding snapshot, not the history. |
| Hyperliquid `l2Book` spread and top-of-book size | FREE AND UNWIRED | `normalize_l2_book` in `mm_ingest/structure.py`, metric `l2_spread`. Same unused ingest path. |
| Hyperliquid `predictedFundings` | FREE AND UNWIRED | Same ingest path. |
| FRED `VIXCLS`, `DTWEXBGS`, `DGS2`, `T10Y2Y`, `BAMLH0A0HYM2`, `DCOILWTICO` | FREE AND UNWIRED | Named in `config/macro/regimes.yaml` `fred_series`. `mm_macro/engine.py` classifies values it is given. It does not fetch. |
| FRED `CPIAUCSL`, `PAYEMS` | FREE AND UNWIRED | Freshness overrides in `config/briefing/macro.yaml`. They are not in `live.fred.series`. |
| FRED GDP | Unverified as a wired series | The token `GDP` appears in `config/macro/regimes.yaml` `event_risk.cb_name_tokens`. No series id is fetched. |
| Polygon tickers outside the retain 17 and the brief four | FREE AND UNWIRED on the existing grouped-daily call, if the stocks plan returns them | The retain GET is the full US grouped daily. `_filter_grouped` keeps the 17. SPY, UUP, USO, GLD, IWM, and sector or factor ETFs are not in that list. Whether today's body contains each ticker was not probed. SPY, UUP, and USO are already fetched by the brief (row above) and dropped by retain. |
| Cboe VIX / VX, CME ES, NQ, CL, ICE DXY | PAID | `macro.yaml` says true VIX/VX needs a Cboe entitlement not on the Polygon stocks plan, and true ES/NQ/CL need a futures subscription. ICE DXY is not a series in this repo. UUP is the wired proxy. |
| News tape | UNAVAILABLE | No news fetcher under `packages/ingest`. `mm_ingest/edgar.py` is SEC filings (IMP-024), not a news tape. A free wire was not verified. A paid wire is the Principal's call. |
| Next-24h macro calendar | UNAVAILABLE as a live feed | `config/briefing/calendar.yaml` is a frozen March 2026 fixture (`source: fixture`). `config/macro/event_calendar.yaml` is one earnings row, BB on 2026-09-24, and it is the gate-5 file, not the brief. `mm_briefing/calendar.py` filters that fixture. |

QQQ is both fetched by the brief and stored by retain. The other three brief ETFs and DGS10 are FETCHED NOT STORED.

## Files that are not on main

Read, not shipped. The live message is `render_close` in `packages/briefing/src/mm_briefing/render.py`.

| Path | Where it lives |
|---|---|
| `packages/briefing/src/mm_briefing/prior.py` | Open PR #131. `NullPriorCaptureReader` returns no prior. The morning brief does not import it. |
| `packages/briefing/src/mm_briefing/health.py` | Open PR #131. Coverage rollup, not confidence. |
| `config/briefing/presentation.yaml` | Open PR #131. Not in the main tree. |
| `docs/specs/brief-v2-questions.md` | Open PR #126. |
| `docs/specs/mvp-retain-capture-contract.md`, `docs/specs/mvp-retain-value-test.md` | Open PR #125. They describe draft #122. The writer that landed is #132, on main, cited above. |
| `docs/specs/brief-format-freeze.md`, `docs/specs/brief-card-split-deferred.md` | Open PR #131. |

#131 records two Principal decisions of 25 Sep 2026. `KEY TAKEAWAY` does not ship: a line that is the same every morning is not information, and the standing-rule tests on that branch assert the heading is absent. The 6–8 card split stays deferred until a partial send has a receipt and a retry cannot duplicate a card already sent. The morning product on that branch is one message of at most 4096 characters. Segments 1 and 20 of this proposal reverse both decisions. That reversal is the Principal's later ask. It is not a build during the freeze.

On main, delivery of the morning pack is one `deliver()` call with no `png` (`apps/lab-cli/src/mm_lab_cli/deliver.py`). `chunk_markdown_v2` (`packages/delivery/src/mm_delivery/format.py`) splits only when the escaped text exceeds 4096 (`config/delivery/telegram.yaml`). A later chunk failure returns `sent=false` after earlier chunks may already have posted (`mm_delivery/deliver.py`). That is not a card receipt. `send_photo` exists on `mm_delivery/telegram.py` and is unused by this pack. `mm_desks/chart.py` `render_png` draws a 160×90 research-levels image. It does not draw the heatmap or the three charts.

`render_close` prints two monitor lines that do not depend on the tape: the Asia funding/OI/liquidation sentence and the Europe USD/yields sentence (`render.py`). Under the 25 Sep standing rule those lines are not information.

## Judgements

A judgement needs a rule that uses stored or fetched inputs, and a way to score it against a later outcome. Where that rule is absent, the cell is **NOT BUILDABLE WITHOUT A RULE**. Candidate rules below are proposals. They are not thresholds in force.

Two classifiers already exist and are not this grid:

- `mm_macro/regime.py` `classify_macro_regime` tags `{risk_on|risk_neutral|risk_off}_{usd_weak|usd_mid|usd_strong}` from VIX and DXY, using `config/macro/regimes.yaml` (VIX below 18 / above 25, DXY below 100 / above 106). Missing either input returns `unavailable`. Those two series are not fetched by the morning job. The confidence number there is coverage plus distance from the midpoints. It is not a brief confidence bar.
- `mm_quant/regime.py` `classify_regime` buckets realised vol, ADX, z-score, and funding against `config/quant/regime.yaml` (funding crowded at `0.0003`). It needs factor rows this capture does not produce. It is not the six coloured states.

Sign of a stored change, once two captures exist: later minus earlier. Positive, negative, or zero. Zero is unchanged. Unchanged is a gap in any four-cell map. No epsilon is in force. **Proposal:** do not add an epsilon until one is written down and scored.

`trailing_return` and `sma` are arithmetic on a price list. They are not a state, a colour, or a confidence.

The eleven-capture score is the Principal's Y/N on whether one line told him something a chart glance would not (`eleven-capture-test.md`). That score is not a substitute for an outcome rule on a forecast.

## Segment 1 — Header, regime colours, pulse bars, key message

1. **Inputs.** Header text needs no series. Pulse bars: S&P = SPY, FETCHED NOT STORED (`macro.yaml`). Nasdaq proxy QQQ, HELD as `close` and also fetched live. BTC and ETH mids, HELD; the live brief also fetches them and does not read the stored row. Regime colours Risk, Liquidity, Volatility, Rates, USD, Crypto: no series is bound to those six names. USD proxy UUP is FETCHED NOT STORED. Volatility as VIX is PAID (Cboe) or FREE AND UNWIRED (`VIXCLS`). Rates as DGS10 are FETCHED NOT STORED. Liquidity has no wired book or reserve series.
2. **History.** One mid or one close can print on capture 1 (Mon 28 Sep 2026). A bar that is a change needs 2 captures (Tue 29 Sep) for a 1-session gap, 6 for a 5-session return (Mon 5 Oct), 21 for a 20-session return (Mon 26 Oct).
3. **Judgement.** The six colours and the 2–4 sentence key message are **NOT BUILDABLE WITHOUT A RULE**. The key message is the panel #131 removed under `KEY TAKEAWAY`. **Proposal, not in force:** omit the paragraph; print only a number that changed since the prior capture, with both timestamps.
4. **Delivery.** Text. Fits the one-message path if the paragraph is omitted. The paragraph plus the rest of this proposal does not fit in 4096 and wants the deferred card split.
5. **Conflicts.** Colours with no input. A standing headline that repeats. Segment 1 reverses the 25 Sep removal of the takeaway.

## Segment 2 — Cross-asset table

Columns: Asset, Last, Δ1D, Δ5D, Δ20D, Vol, Regime. Rows: S&P, Nasdaq, US10Y, USD, Oil, VIX, BTC, ETH.

1. **Inputs.** Last: BTC, ETH HELD (`mid_px`). Nasdaq-as-QQQ HELD (`close`). S&P/SPY, USD/UUP, Oil/USO FETCHED NOT STORED. US10Y/DGS10 FETCHED NOT STORED (the brief already has a 1-step change from FRED `limit: 2`, which is not Δ1D/Δ5D/Δ20D from captures). VIX PAID or FRED `VIXCLS` FREE AND UNWIRED. Vol as realised vol can be computed only for a HELD series, after the window below. Regime column: see segment 4.
2. **History.** Δ1D: 2 captures, Tue 29 Sep 2026, and only for HELD series until SPY, UUP, USO, and DGS10 are stored. Δ5D under `trailing_return` bars=5: 6 captures, Mon 5 Oct 2026. Δ20D bars=20: 21 captures, Mon 26 Oct 2026, after the test. Realised vol in `mathutil.realised_vol` needs 20 returns (21 closes) and `config/quant/factors.yaml` `min_bars: 20`. A 20-session vol cell is Mon 26 Oct 2026 at the earliest, for QQQ, BTC, and ETH only.
3. **Judgement.** The return cells are arithmetic, not a judgement. The Regime cell is **NOT BUILDABLE WITHOUT A RULE**. **Proposal:** leave Regime blank until segment 4 has a rule whose inputs are on the same row.
4. **Delivery.** Text table. No image.
5. **Conflicts.** A vol or delta printed as 0 when the prior is missing. VIX coloured without a print.

## Segment 3 — Data health

1. **Inputs.** The proposal's six domains are Equities, Rates, USD, Oil, Volatility, Crypto. Equities on the brief are SPY and QQQ (QQQ HELD, SPY FETCHED NOT STORED). Rates FETCHED NOT STORED. USD FETCHED NOT STORED. Oil FETCHED NOT STORED. Volatility PAID / FREE AND UNWIRED. Crypto HELD and also fetched live. Main's close brief prints a quality word (`render_close`), not a percentage.
2. **History.** A domain can be fresh or missing on capture 1. A "stale because the print did not roll" rule needs 2 captures. That rule exists only on unmerged #131 (same UTC date as the prior capture's observation date). It is not on main.
3. **Judgement.** The only written percentage is on unmerged #131 `health.py` `score_data_health`: `round(100 * sum(weights) / scored domains)` with weights fresh 1, degraded 0.5, stale 0, unavailable 0 (`presentation.yaml` on that branch). One fresh domain and five zero-weight domains is 17%, not 42%. The mockup's 42% with 1 of 6 fresh does not match that formula. There is no health percentage on main. Treating 42% as the score is **NOT BUILDABLE WITHOUT A RULE**. #131 also says the percentage is coverage, not confidence. **Proposal:** if a percentage is ever printed, print the weights beside it so the figure recomputes from the line.
4. **Delivery.** One text line. No image.
5. **Conflicts.** 42% is not recomputable from "1 of 6 fresh". A health line that lists the same missing domain every morning is not information. **Proposal:** print a domain only when its state changed since the prior morning.

## Segment 4 — Market regime grid

Growth, Inflation, Liquidity, Risk Appetite, Volatility, USD Pressure, Rates Pressure, plus an overall label.

1. **Inputs.** Growth: no series fetched. GDP is a name in `regimes.yaml` event tokens, not a print. Inflation: `CPIAUCSL` is FREE AND UNWIRED. Liquidity: no wired input. Risk appetite: no series. Volatility: VIX PAID or `VIXCLS` FREE AND UNWIRED. USD pressure: UUP FETCHED NOT STORED; `DTWEXBGS` FREE AND UNWIRED; the macro tag's DXY thresholds expect an index level near 100–106, which an ETF price is not. Rates pressure: DGS10 FETCHED NOT STORED; `T10Y2Y` FREE AND UNWIRED.
2. **History.** A level can print when the series is stored. A pressure state that is a change needs the same 2 / 6 / 21 capture counts. None of these states have a series on the retain path, so the dates do not start.
3. **Judgement.** **NOT BUILDABLE WITHOUT A RULE.** The macro tag cited above is a different pair of inputs and still lacks those inputs on the morning path. Colouring Growth or Inflation with no print is the conflict in the mockup. **Proposal:** one cell, one series id, one written cut, missing stays a gap. No overall word until every required cell has a print.
4. **Delivery.** Text grid. The mockup uses colour. Colour is still text-safe if the state word is present. An image is not required for the words.
5. **Conflicts.** Colour with no input. An overall label such as DATA-CONSTRAINED that appears every morning until the feeds exist is not information. **Proposal:** omit the grid while every cell is a gap.

## Segment 5 — Cross-asset heatmap or dot grid

Rows in the mockup: S&P, Nasdaq, Russell, US10Y, DXY, Oil, Gold, BTC, ETH. Columns 1D, 5D, 20D.

1. **Inputs.** BTC, ETH HELD. Nasdaq-as-QQQ HELD. S&P/SPY, DXY/UUP, Oil/USO FETCHED NOT STORED. US10Y FETCHED NOT STORED. Russell (IWM or RUT) FREE AND UNWIRED on Polygon if the grouped-daily body contains the ticker; RUT futures were not verified and the CME note in `macro.yaml` covers index futures as PAID. Gold: GLD is the same Polygon case, FREE AND UNWIRED as a retain row; COMEX gold was not verified. GLD is a deferred name in `config/universe.yaml`, not a retain ticker. The finviz-style sector board in the mockup needs sector ETFs. Those tickers are not in the retain 17. Same grouped-daily call, currently dropped. Unverified per ticker.
2. **History.** A 1D dot for a HELD series: Tue 29 Sep 2026. A 5D dot under `trailing_return`: Mon 5 Oct 2026. A 20D dot: Mon 26 Oct 2026. Rows that are not stored have no date.
3. **Judgement.** A dot that is only the sign of `trailing_return` is arithmetic. A colour scale with unpublished cuts is a judgement. **Proposal:** three signs (up, down, unchanged) and no third colour until a cut is written. Unchanged and missing are different glyphs.
4. **Delivery.** The mockup is an image. Image send is not on the morning path (see the delivery section above). A text dot grid can ride the one message. The finviz board cannot.
5. **Conflicts.** A green or red cell with no stored return. Russell, DXY, gold, and oil coloured from nothing.

## Segment 6 — Three charts

**(a) Equity risk.** S&P and Nasdaq, VWAP, 20-day average, 50-day average, momentum arrow.

1. **Inputs.** QQQ `close` HELD. SPY FETCHED NOT STORED. Intraday VWAP needs intraday bars. The retain path stores one bar per weekday. `mm_desks/chart.py` `compute_levels` can compute a session VWAP from high, low, close, and volume. Those keys are not read by retain. If they sit on `payload.raw`, that is Unverified. A daily Polygon `vw` field would be one number per day, not the intraday line in the mockup. 20-day and 50-day averages are `sma` on closes once the counts exist.
2. **History.** One QQQ point: Mon 28 Sep 2026. 20-day average: Fri 23 Oct 2026. 50-day average: Fri 4 Dec 2026. SPY has no stored series, so no date.
3. **Judgement.** The averages are arithmetic. The up/down momentum arrow is **NOT BUILDABLE WITHOUT A RULE** unless it is defined as the sign of a named return. **Proposal:** the arrow is the sign of `trailing_return` over a written bar count, and only after that count exists.
4. **Delivery.** Image. Not on the morning path.
5. **Conflicts.** A VWAP line with no volume and no intraday bars. An arrow that is the same glyph by default.

**(b) Macro transmission.** US10Y, DXY, S&P/Nasdaq, and a label for rates, dollar, growth, or liquidity.

1. **Inputs.** US10Y FETCHED NOT STORED. DXY/UUP FETCHED NOT STORED. S&P/SPY FETCHED NOT STORED. QQQ HELD. Growth and liquidity have no series (segment 4).
2. **History.** An overlay of stored QQQ can start Mon 28 Sep 2026 as a single point. The other three lines start when those series are stored, then follow the 2 / 6 / 21 capture counts for changes.
3. **Judgement.** "Driven by rates / dollar / growth / liquidity" is **NOT BUILDABLE WITHOUT A RULE**. **Proposal:** plot the stored lines and print no driver word.
4. **Delivery.** Image. Not on the morning path. Text can list the three changes once they exist.
5. **Conflicts.** A coloured driver with no input. That is the same failure as Growth/Inflation in segment 4.

**(c) Crypto positioning.** BTC price, open interest, funding, liquidations.

1. **Inputs.** BTC `mid_px`, `open_interest`, and `funding` are HELD (one snapshot each morning). Funding history is FREE AND UNWIRED (`fundingHistory`). Liquidations are FETCHED NOT STORED on the brief via `recentTrades`, and only for the recent window, and only when the trade object has `liquidation`. They are not retain rows. A historical liquidation tape was not found.
2. **History.** Price, OI, and funding levels: Mon 28 Sep 2026. A second point on each line: Tue 29 Sep 2026. A liquidation bar has no stored history, so no date.
3. **Judgement.** The three stored lines are prints. A liquidation bar is not a print until a row exists. No state word belongs on this chart without segment 7's rule.
4. **Delivery.** Image. Not on the morning path. The three numbers can be text on capture 2.
5. **Conflicts.** The mockup's "Liquidations $0" is a gap rendered as zero. The close brief can do the same via `liquidation_size_sum`.

## Segment 7 — BTC positioning card

Price, 1-day change, OI and its change, funding, basis, liquidations, positioning state, interpretation.

1. **Inputs.** Price, OI, funding: HELD for BTC. 1-day change and OI change: the same two rows, from capture 2. Basis: not a retain metric. The brief computes mark minus oracle from the live snapshot (FETCHED NOT STORED). `payload.raw` may contain `markPx` and `oraclePx`; Unverified. Liquidations: FETCHED NOT STORED, not a history. Positioning state and the interpretation sentence: no series of their own.
2. **History.** Levels on Mon 28 Sep 2026. Deltas on Tue 29 Sep 2026. Basis on the same day the raw keys are confirmed, or when a basis metric is written. Liquidations: no date.
3. **Judgement.** The state word and the interpretation are **NOT BUILDABLE WITHOUT A RULE**. The four sign cells in segment 8 are a description of the pair, not this card's prose. **Proposal:** print the three levels, the two deltas, and a gap line for basis and liquidations. No adjective.
4. **Delivery.** Text card. The funding "bar" and basis "bar" in the proposal are graphics. Text numbers do not need an image.
5. **Conflicts.** A state word with no rule. Liquidations as $0. An interpretation that restates the same relationship every day.

## Segment 8 — OI × price quadrant

Price up and OI up; price down and OI up; price up and OI down; price down and OI down. Place BTC and ETH.

1. **Inputs.** HELD. BTC and ETH `mid_px` and `open_interest`. The same pair exists for every `quadrant_eligible` perp. DRV has no OI. CASHCAT and PONS are stored and blocked; the value-test note on unmerged #125 already excludes them from a scored line. This spec does not promote them.
2. **History.** Two captures. Tue 29 Sep 2026. Capture 1 has no cell.
3. **Judgement.** The cell is the pair of signs from the rule in the judgements section. Both values must be non-null on both captures. A zero change is not a cell. The glosses ("short build", "long liquidation risk", "short covering", "deleveraging") are **NOT BUILDABLE WITHOUT A RULE** as forecasts. They are labels for a past pair, not a prediction. Scoring against a later outcome needs a pre-written event (for example a liquidation print inside a written number of captures). Liquidation history is not stored, so that score cannot be computed. The audit score is whether the two stored numbers had those signs. The eleven-capture Y/N stays the Principal's.
4. **Delivery.** Text. Four lines, or one line per name that moved. No image required. Segment 9's chart is the same pair drawn.
5. **Conflicts.** A name placed in a quadrant when one delta is missing or zero. A blocked name drawn as if it were a book input.

## Segment 9 — Positioning versus price chart

BTC price line, OI sparkline, quadrant label.

1. **Inputs.** Same as segment 8. HELD.
2. **History.** Two points on Tue 29 Sep 2026. A longer line grows one weekday at a time. It does not exist inside the test as a 20-session chart.
3. **Judgement.** The label is segment 8's sign cell. No second classifier.
4. **Delivery.** The sparkline is an image, or a text list of the stored points. Image send is not on the morning path. Text is.
5. **Conflicts.** A chart that fills a missing OI with a flat zero line.

## Segment 10 — What changed

Only rows that changed. The proposal names BTC OI, BTC funding, US10Y in basis points, DXY in percent, VIX in percent, each with a one-line consequence.

1. **Inputs.** BTC OI and BTC funding: HELD, delta from capture 2. US10Y: FETCHED NOT STORED. The brief's FRED change is one vendor step, not a capture delta, and it is not in basis points unless `unit` is `%` (`AssetPrint.change_bp` in `mm_briefing/models.py`). DGS10 from FRED is a percent yield; the basis-point scaling is implemented for that unit. It is still not stored. DXY percent: UUP FETCHED NOT STORED, and UUP percent is not the DXY index percent. VIX percent: PAID or FREE AND UNWIRED.
2. **History.** BTC rows: Tue 29 Sep 2026. The other three: the second stored capture after someone stores them. No date until then.
3. **Judgement.** "Changed" is a non-zero sign on a stored pair, using the zero rule above. The consequence sentence is **NOT BUILDABLE WITHOUT A RULE**. **Proposal:** the line is the name, the two values, the two timestamps, and no verb after that.
4. **Delivery.** Text. This is the panel that can stay inside one message. Empty means the section is omitted. A section of "nothing changed" every quiet morning is not information.
5. **Conflicts.** Printing US10Y, DXY, or VIX as 0 when the series is absent. A consequence sentence that does not change when the numbers do.

## Segment 11 — Market narrative and confidence

1. **Inputs.** The narrative has no series. The "limited by" list can name the gaps in this file. Confidence has no input series. #131's health percentage is coverage of domain states, and the macro regime confidence is a different formula whose VIX and DXY inputs are absent.
2. **History.** A gap list can be written on Mon 28 Sep 2026. It will be the same list every morning until a source is added, which makes it fail the standing rule. A confidence figure has no date.
3. **Judgement.** The paragraph and the confidence percentage are **NOT BUILDABLE WITHOUT A RULE**. **Proposal:** do not print a confidence number. Print a missing feed only on the morning it changes status.
4. **Delivery.** Text. No image.
5. **Conflicts.** A 60% bar that cannot be recomputed from the lines above it. A narrative that is the key message segment 1 already asked for, which #131 removed.

## Segment 12 — Catalyst radar

Intensity bars for the next 24 hours: US macro, US equities, crypto, Europe, Asia. Dated events when available.

1. **Inputs.** No live calendar. The brief fixture is March 2026 (`config/briefing/calendar.yaml`). Gate 5 has one past equity event (`config/macro/event_calendar.yaml`, BB earnings 2026-09-24). Region tags US, Europe, and Asia are not a feed. Crypto has no event source in `packages/ingest`.
2. **History.** An empty window can be shown on Mon 28 Sep 2026 as "none in the file". That sentence does not become a 24-hour radar. Intensity has no history because it has no input.
3. **Judgement.** Intensity bars are **NOT BUILDABLE WITHOUT A RULE**. There is no map from an event type to a bar height, and no later outcome (realised move after the event) is defined. **Proposal:** list a dated event only when the file has one inside the existing look-ahead (`mm_briefing/calendar.py`, 36 hours forward, 6 back), with the source path on the line. No bar.
4. **Delivery.** Text. The current close brief already lists fixture events. An intensity graphic needs an image or a fake scale.
5. **Conflicts.** A full bar chart while the calendar file is empty or stale. Five region bars that look the same every morning.

## Segment 13 — Scenario map and invalidation

A condition / behaviour / confirmation table for the four OI × price states, plus invalidation lines: funding acceleration, OI expansion without price confirmation, basis widening, liquidation cluster, losing a structural level.

1. **Inputs.** The condition column is segment 8 (HELD from capture 2). Funding level is HELD; "acceleration" needs a definition and at least three funding prints. OI and price are HELD. Basis is not a metric (segment 7). Liquidation cluster is not stored. A structural level is not defined for this brief. `mm_desks/chart.py` levels need bars this capture does not parse.
2. **History.** The condition cell: Tue 29 Sep 2026. Three funding prints for a second difference: Wed 30 Sep 2026, and only after "acceleration" is defined. The other invalidation lines have no date.
3. **Judgement.** Behaviour, confirmation, and the five invalidation lines are **NOT BUILDABLE WITHOUT A RULE**. No directional call is the right constraint, and it still needs numeric cuts before a line can fire. **Proposal:** the table's condition column is the segment 8 cell. The other two columns stay off the page. Invalidation stays off the page until each line has a cut, a series, and a later check.
4. **Delivery.** Text table. No image. Sharing the segment 8 line avoids a second message.
5. **Conflicts.** Four scenario rows that print every morning with the same behaviour sentences. An invalidation that fires from a missing basis or a zero liquidation.

## Segment 14 — Signal board

Factor, state, confidence. Factors: Trend, Momentum, Positioning, Funding, Liquidations, Volatility, Macro. State and confidence are different columns.

1. **Inputs.** Momentum as a return: HELD series only, after the window. Positioning: segment 8. Funding: the level is HELD; a state is not. Liquidations: not stored. Volatility: realised vol on a HELD series after 21 closes, or VIX which is not stored. Macro: segment 4, no inputs. Trend: `config/quant/factors.yaml` does not define a trend state for this board. ADX exists in `mm_quant` and needs the bar counts in that config (`adx` period 14, min 28 in `mm_quant/config.py`). Those bars are not the morning capture.
2. **History.** No state on capture 1. A funding level can sit in the row on Mon 28 Sep 2026 without a state word. Returns follow segment 2's dates.
3. **Judgement.** State and confidence for every row are **NOT BUILDABLE WITHOUT A RULE**. Reusing the macro regime confidence or the #131 health percentage would mix three different formulas. **Proposal:** no board until each factor has a written state rule and a separate written confidence rule, and both can be recomputed from the row.
4. **Delivery.** Text. Wide. It pushes the one-message cap. It is not an image by itself.
5. **Conflicts.** A confidence column that does not add from the numbers shown. A liquidations state of "calm" because the sum was zero.

## Segment 15 — Thesis scorecard

Thesis, date, signal, outcome, status, and a 30-day quality block (evaluated, confirmed, invalidated, pending, precision).

1. **Inputs.** Thesis cards live in the research workspace (`mm_research_kit`), not in the morning retain. The close brief can list hooks from memory when it is not `--no-db` (`render_close` "Lab right/wrong hooks"). The morning job is `--no-db`, so that block is the empty line. Pack scorecards (`mm_quant/scorecard.py`, IMP-030) compare like-for-like packs. They do not compute a 30-day signal precision.
2. **History.** A 30-day window of weekday captures is 30 stored mornings: capture 30 is Fri 6 Nov 2026. That is after the test. The window is meaningless until a signal definition exists. The Principal's own caveat on this segment: without a methodology and stored history, the precision is fake.
3. **Judgement.** **NOT BUILDABLE WITHOUT A RULE.** Precision needs a pre-written signal, a pre-written outcome, a horizon, and stored outcomes. None of those are in the retain row. **Proposal:** do not print a precision number. Do not print an empty scorecard of zeros.
4. **Delivery.** Text. Omits cleanly when there is no scored thesis.
5. **Conflicts.** A precision percentage on a short sample. A status of "pending" repeated every morning with no thesis id.

## Segment 16 — Anomaly radar

The proposal lists: BTC up and OI down; BTC up and funding up; ETH up and BTC flat; DXY up and bonds up; oil up and inflation down.

1. **Inputs.** BTC up and OI down: HELD, segment 8. BTC up and funding up: HELD from capture 2 (both signs). ETH up and BTC flat: HELD mids from capture 2; "flat" needs the zero rule. DXY up: UUP FETCHED NOT STORED. Bonds up: no bond price series. DGS10 is a yield, FETCHED NOT STORED, and yield up is price down. Oil: USO FETCHED NOT STORED. Inflation: `CPIAUCSL` FREE AND UNWIRED, and it does not update daily. `config/briefing/divergences.yaml` has five rules (`equity_vol`, `crypto_equity`, `usd_equity`, `yields_equity`, `oil_usd`) with numeric cuts, evaluated by `mm_briefing/divergences.py`. They need ES, VIX, DXY, US10Y, and CL changes on `AssetPrint`. VIX is unavailable. The others are fetched, not stored, and the crypto side of `crypto_equity` needs a BTC `change_pct` the live path leaves empty. Those rules are not the five lines in this segment.
2. **History.** The two BTC/ETH lines: Tue 29 Sep 2026. The DXY, bond, oil, and inflation lines: no date until stored.
3. **Judgement.** A flag that is only the segment 8 sign pair is the sign rule, scored by audit against the two rows. "Confirmed" on "BTC up and funding up" is **NOT BUILDABLE WITHOUT A RULE** (confirmed against what later outcome?). The cross-asset lines that lack a series are not flags. The `divergences.yaml` cuts are in force for that function only. They are not adopted here as the radar, because the morning retain does not feed that function. **Proposal:** one flag, the segment 8 cell, and only when both signs are non-zero. No "confirmed" word.
4. **Delivery.** Text. One line when a flag exists. Omit when none exist.
5. **Conflicts.** A divergence icon with one side missing. Inflation "down" with no CPI print. Bonds inferred from a missing yield.

## Segment 17 — Relative strength

Crypto: ETH/BTC, SOL/BTC, BTC/DXY at 1D, 5D, 20D. Equity: Nasdaq/S&P, small/large, value/growth, semis/Nasdaq.

1. **Inputs.** ETH, BTC, and SOL `mid_px` are HELD. BTC/DXY needs DXY or UUP; UUP is FETCHED NOT STORED. Nasdaq/S&P as QQQ/SPY needs SPY, FETCHED NOT STORED; QQQ is HELD. Small/large and value/growth have no tickers in config. Semis has a name: `config/quant/factors.yaml` maps semiconductors to SMH and financials to XLF, and the equity benchmark there is SPY. SMH, XLF, and SPY are not retain tickers. FREE AND UNWIRED on the same grouped-daily call if the body contains them. Unverified per ticker. Semis/Nasdaq as SMH/QQQ is not the ratio that file computes.
2. **History.** A 1-session ratio change for ETH/BTC or SOL/BTC: Tue 29 Sep 2026 (two mids each). 5-session: Mon 5 Oct 2026. 20-session: Mon 26 Oct 2026. The equity ratios have no date until both legs are stored.
3. **Judgement.** A ratio of two stored prices is arithmetic (`end/start - 1` on each leg, then the difference, or a ratio of ratios). **Proposal:** print `(ETH_mid / BTC_mid)` change with both timestamps, and the same for SOL/BTC. No rank word and no colour cut. Anything beyond that is **NOT BUILDABLE WITHOUT A RULE**.
4. **Delivery.** Text table. No image.
5. **Conflicts.** A ratio printed as 0 when one leg is missing. A factor ratio with the tickers still unnamed.

## Segment 18 — Liquidity

Order-book depth, bid/ask spread, funding, OI, liquidation bars, and a liquidity regime.

1. **Inputs.** Depth and spread: FREE AND UNWIRED (`l2Book`, `l2_spread`). Funding and OI: HELD as levels. Liquidation bars: not stored (segment 6c). Liquidity regime: no series beyond those.
2. **History.** Funding and OI levels: Mon 28 Sep 2026. Their changes: Tue 29 Sep 2026. Book and liquidations: no date. A regime that needs a spread history needs that series plus a written window.
3. **Judgement.** The regime word is **NOT BUILDABLE WITHOUT A RULE**. **Proposal:** print funding and OI. Print spread only after `l2_spread` is on the retain path. Missing book and missing liquidations stay gaps.
4. **Delivery.** Text for the two held numbers. Bars are graphics and need the image path or they are omitted.
5. **Conflicts.** A full liquidity bar set with a zero liquidation and a zero depth. A regime colour with funding as the only input, which does not match the label.

## Segment 19 — News impact matrix

Story, asset, direction, magnitude, confidence, and a transmission chain from news to macro expectations, rates, USD, equity valuation, risk appetite, and crypto.

1. **Inputs.** News: UNAVAILABLE. The rest of the chain reuses segments 2 and 4. Rates and USD are FETCHED NOT STORED. Equity valuation and risk appetite have no series.
2. **History.** No story row has a start date. The chain has no start date.
3. **Judgement.** Direction, magnitude, and confidence on a story are **NOT BUILDABLE WITHOUT A RULE**. There is no story to score. A later outcome (the asset's stored move after the timestamp) cannot be defined until a story row exists with an asset id and a timestamp. **Proposal:** omit the matrix. Do not invent a neutral row.
4. **Delivery.** Text if it ever has rows. The mockup's chain diagram is an image. Neither is sendable as a product today.
5. **Conflicts.** A magnitude of 0 and a confidence of 0 filling an empty matrix. A transmission arrow coloured with no rate and no dollar print.

## Segment 20 — Six to eight Telegram cards and a visual system

Cards: Executive, Dashboard, Macro, Crypto, Positioning, News, Scenarios, Audit. Header "DONCAPO MARKET INTEL". Icon legend. Colours are data states, not buy/sell.

1. **Inputs.** Each card is the segments above. Audit can list domain gaps (segment 3) and the freshest `captured_at` once the brief reads retain. It does not read them today. The icon set on unmerged #131 `presentation.yaml` is fresh / degraded / stale / unavailable. The proposal's legend (confirmed, developing, stress, missing, divergence, watch, tick, invalidated) is a different set and is not in that file.
2. **History.** Same dates as the segments on each card. A card of gaps can be assembled on Mon 28 Sep 2026 and should not be sent (the deferred-split note says skip a card that has nothing to say).
3. **Judgement.** Mapping colour to confirmed / developing / stress / invalidated is **NOT BUILDABLE WITHOUT A RULE**. Those words are outcomes. The #131 icons are data-state weights, and they are not on main. **Proposal:** do not add the new legend. Keep one message until the receipt rule below is true.
4. **Delivery.** This segment is the delivery change. It needs multi-message send with a partial-send receipt and a retry that does not duplicate a sent card. That pair is not built. `send_photo` is not the morning path. Segment 20 reverses the 25 Sep deferral. It waits.
5. **Conflicts.** Eight messages that repeat the same header and the same legend every morning. A green icon meaning "buy". A white icon meaning "zero".

## Engine layers

The proposal's pipeline, in order. Telegram stays the last step.

### Market data

1. **Inputs.** HELD retain set: 19 perp mids, funding, OI; DRV mid; 17 closes. FETCHED NOT STORED on the brief: SPY, UUP, USO, BTC/ETH mark and oracle, `recentTrades` liquidations, CoinGecko. QQQ is in both.
2. **History.** Levels Mon 28 Sep 2026. Deltas Tue 29 Sep 2026.
3. **Judgement.** None in the split itself.
4. **Delivery.** None until a later layer renders.
5. **Conflicts.** Reading the brief's live snapshot and the retain row as one series without saying which timestamp won.

### Macro data

1. **Inputs.** DGS10 FETCHED NOT STORED. The other FRED ids in `config/macro/regimes.yaml` and the CPI/NFP freshness overrides are FREE AND UNWIRED. VIX index PAID. UUP and USO are the brief's proxies, FETCHED NOT STORED.
2. **History.** A stored macro series starts the day it joins the retain allowlist, then uses the same weekday counts. Nothing in this layer is on that allowlist today, so the macro clock has not started.
3. **Judgement.** None until the regime layer.
4. **Delivery.** None.
5. **Conflicts.** Treating a FRED `limit: 2` change as a 5-day or 20-day capture delta.

### News data

1. **Inputs.** UNAVAILABLE. EDGAR is filings, not this split.
2. **History.** No start date.
3. **Judgement.** None. A magnitude would be segment 19.
4. **Delivery.** None.
5. **Conflicts.** An empty news object passed downstream as magnitude 0.

### Normaliser

1. **Inputs.** Observation envelopes already exist (`mm_provenance/envelope.py`, retain writer). They normalise one vendor field into one metric. They do not emit a cross-asset panel.
2. **History.** A normalised delta needs two HELD prints. Same dates as `trailing_return`.
3. **Judgement.** Unit conversion that is already coded can stand: FRED yield change in basis points when `unit` is `%` (`change_bp`). A z-score (`mathutil` via `mm_quant/factors.py`, window 20) needs 20 prices and is arithmetic, not a regime. **Proposal:** the normaliser outputs value, prior value, timestamps, and a gap. It does not output a colour.
4. **Delivery.** None.
5. **Conflicts.** Filling a gap with 0 so a later average can run. `sma` already returns `None` when the window is short. Callers must keep that `None`.

### Regime detector

1. **Inputs.** The mockup grid's inputs are segment 4. They are not HELD. The two existing classifiers are cited in the judgements section and do not see morning rows.
2. **History.** No start date for the mockup grid.
3. **Judgement.** **NOT BUILDABLE WITHOUT A RULE** for Growth, Inflation, Liquidity, Risk Appetite, Volatility, USD Pressure, Rates Pressure, Crypto, and the overall word. The macro tag remains a separate function with its own YAML. It is not wired to this brief, and its driving series are not on the capture.
4. **Delivery.** Text, if a rule ever exists. Colour is a state word, not an image.
5. **Conflicts.** Painting a cell from a proxy that is not the series the threshold was written for (UUP price against a DXY 100/106 cut).

### Momentum

1. **Inputs.** HELD closes and mids only. SPY, UUP, USO, DGS10 are not in the list.
2. **History.** `sma` window 20: Fri 23 Oct 2026. `trailing_return` bars 20: Mon 26 Oct 2026. `sma` window 50: Fri 4 Dec 2026. Factor windows in `config/quant/factors.yaml` (equity 21/63, crypto 30/90) are later than the test and longer than 20.
3. **Judgement.** The return and the average are arithmetic. An arrow or a "trend state" is **NOT BUILDABLE WITHOUT A RULE**. **Proposal:** publish the return and the sample count. No arrow.
4. **Delivery.** Text. A chart of the same numbers is segment 6a and needs an image.
5. **Conflicts.** A momentum glyph on capture 1.

### Positioning

1. **Inputs.** HELD `mid_px`, `open_interest`, `funding` for quadrant-eligible perps. Basis and liquidations are not metrics on this path.
2. **History.** Tue 29 Sep 2026 for the first sign cell.
3. **Judgement.** The sign cell in segment 8 is the rule. A positioning state, a funding state, and a liquidation state are **NOT BUILDABLE WITHOUT A RULE**.
4. **Delivery.** Text. The chart form is segment 9.
5. **Conflicts.** DRV, CASHCAT, or PONS forced into a quadrant. A null mid replaced by mark (retain already refuses that substitution).

### Anomalies

1. **Inputs.** Segment 16. Two of the proposal's pairs are HELD. The macro pairs are not. `divergences.yaml` is a different rule set and is not fed by retain.
2. **History.** Tue 29 Sep 2026 for BTC/ETH pairs.
3. **Judgement.** Sign pairs only. "Confirmed" and any flag whose series is missing are **NOT BUILDABLE WITHOUT A RULE**.
4. **Delivery.** One text line, omitted when empty.
5. **Conflicts.** A standing "no anomalies" line.

### Signal engine

1. **Inputs.** Segment 14. No board inputs are complete.
2. **History.** No start date for a state.
3. **Judgement.** **NOT BUILDABLE WITHOUT A RULE.** State and confidence stay separate, and neither has a formula for this board.
4. **Delivery.** Text, later. Not during the freeze.
5. **Conflicts.** A confidence that is the health percentage, the macro-regime confidence, or a constant.

### Confidence engine

1. **Inputs.** No series. #131 health weights are coverage. Macro regime confidence needs VIX and DXY levels this job does not fetch.
2. **History.** No start date.
3. **Judgement.** **NOT BUILDABLE WITHOUT A RULE.** A percentage must recompute from the line that shows it. The mockup 60% and the mockup 42% do not.
4. **Delivery.** Omit.
5. **Conflicts.** Printing a bar because the layout has a slot.

### Scenario generator

1. **Inputs.** Segment 8 for the condition. Segment 13 for everything else.
2. **History.** Tue 29 Sep 2026 for the condition. No date for behaviour, confirmation, or invalidation.
3. **Judgement.** The condition is the sign cell. The rest is **NOT BUILDABLE WITHOUT A RULE**. No directional call, including a call written as a scenario.
4. **Delivery.** The condition can share segment 8's line. A four-row table of standing behaviour text is omitted.
5. **Conflicts.** Four rows every morning.

### Visual engine

1. **Inputs.** Whatever the chart's series are. HELD series can be listed as numbers. SPY, UUP, USO, DGS10, VIX, gold, Russell, liquidations, and the book cannot.
2. **History.** Same as the chart. A 20-day average image is Fri 23 Oct 2026 at the earliest, and only for a HELD series.
3. **Judgement.** A picture of a number is not a new judgement. A colour scale, a driver label, or an arrow is the judgement of the segment it illustrates, and those are **NOT BUILDABLE WITHOUT A RULE** where that segment says so.
4. **Delivery.** Needs a PNG the morning pack does not build, and `send_photo` or `send_document`, which the pack does not call. `render_png` in `mm_desks/chart.py` is the wrong picture.
5. **Conflicts.** An image of illustrative mockup numbers. A chart axis that uses 0 for a gap.

### Telegram

1. **Inputs.** The rendered string. Today that string is `render_close` plus LATE, DEADMAN, and CAPTURE appended in `mm_lab_cli/deliver.py` on the live DM path. CAPTURE is the retain read-back (`docs/runbooks/mvp-retain.md`). The group route stays frozen (`docs/runbooks/telegram.md`).
2. **History.** Not a series.
3. **Judgement.** None in the transport. The card legend in segment 20 is a judgement and is **NOT BUILDABLE WITHOUT A RULE**.
4. **Delivery.** One `sendMessage` when the escaped body is at most 4096. Overflow chunking exists and is not a proven card sender. Partial failure has no per-card receipt. Images are not attached. Segment 20 waits on that receipt and on a retry that cannot duplicate a sent card. #131 deferred the split for this reason. This proposal's segment 20 reverses that deferral and does not lift it.
5. **Conflicts.** Six cards that repeat a header. A second message whose only content is a standing legend.

## Rule conflicts to keep visible

- A missing print is a gap. `liquidation_size_sum` returns `0.0` on an empty list, and `_hl_section` prints it. The mockup line "Liquidations $0" is the same failure.
- Growth and Inflation are coloured in the mockup. No growth series is fetched. CPI is named and not fetched.
- A percentage recomputes from the line. Health 42% with one fresh domain out of six does not match `round(100 * 1 / 6)` under the only written weights (unmerged #131). Those weights are not on main. Main prints no health percentage.
- A line that is identical every morning is not information. `render_close` still has two such monitor sentences. A permanent "VIX unavailable" line is the same class. **Proposal:** say it when the status changes.
- Segment 1's key message reverses the 25 Sep removal of `KEY TAKEAWAY`. Segment 20's card split reverses the 25 Sep deferral. Both reversals are the Principal's decision. They are not built here, and they are not built before the score.
- UUP is not DXY. USO is not CL. SPY is not ES. QQQ is not the Nasdaq composite. The brief labels already say so (`mm_briefing/fetchers.py` `ASSET_NAMES`). A later panel keeps those labels.
- Colour is a data state. It is not a buy or a sell. That constraint is already written on unmerged `presentation.yaml` and is the rule for any legend that ships later.

## Build order

After Mon 12 Oct 2026, and only if the Principal's informative count is at least 3/10. A count of 0–2/10 stops panel work (`eleven-capture-test.md`).

These segments are one feature, not three: segment 8, segment 9's label, and segment 13's condition column. Inputs are HELD `mid_px` and `open_interest` on quadrant-eligible perps. The rule is the sign pair. First morning it can exist: Tue 29 Sep 2026. The morning brief does not read those rows today, so the feature includes a reader. It does not include the gloss, the behaviour column, or an image.

From HELD rows alone, after the score, in this order:

1. What changed for BTC and ETH open interest, funding, and mid, plus the sign cell. Text. One message. Omit the section when nothing changed. Segments 7 (numbers only), 8, 10 (BTC rows only), 16 (those pairs only), 17 (ETH/BTC and SOL/BTC only).
2. The same deltas for the other quadrant-eligible perps that are not blocked. Monitor names stay labelled monitor.
3. QQQ and the other 16 stored closes: last, and `trailing_return` when the count allows. No SPX label. No 20-day cell until Mon 26 Oct 2026. No 50-day average until Fri 4 Dec 2026.
4. Basis only as `(mark - oracle) / oracle` when `markPx` and `oraclePx` are present on the stored `payload.raw`. That ratio is `derive_basis_from_ctx` in `packages/ingest/src/mm_ingest/structure.py`. The close brief's `basis_mark_oracle` is the difference, not this ratio, and it is not stored. Absence is a gap. This stays Unverified until a reader sees the keys. Do not parse mark into a null mid.

Blocked on a source or a purchase decision, which this file does not make:

| Need | Block |
|---|---|
| S&P, USD, oil as stored series | Not a new vendor. SPY, UUP, and USO are already fetched. Storing them is an allowlist change. |
| DXY index, CL futures, ES/NQ futures | PAID. Named in `macro.yaml`. UUP and USO remain the proxies until the Principal buys the licence. |
| VIX | PAID Cboe index, or FREE AND UNWIRED FRED `VIXCLS`. The Principal chooses. VIXY is not a stand-in. |
| Russell, gold, sector and factor ETFs | Same Polygon grouped daily, tickers not on the allowlist. Unverified that each ticker is in the body. `config/quant/factors.yaml` names SMH and XLF. It does not name a Russell, gold, value, or growth ticker. |
| US10Y as a stored series | FRED `DGS10` is already fetched. Storing it is a retain change, not a purchase. `DGS2` and `T10Y2Y` are free and unwired. |
| Funding history, candles, L2 spread | Free Hyperliquid methods already on the client. Not on the morning capture. |
| Liquidation history | No historical feed in this repo. `recentTrades` is a window and is not retained. |
| Inflation and growth | Free FRED ids are named and not fetched. No growth series id is configured. |
| News | UNAVAILABLE. Any vendor is a purchase decision. |
| Next-24h calendar | No live feed. The fixture and the one past earnings row do not fill it. |
| Heatmap, the three charts, card images | Image product plus photo send. Not a data purchase. Still after the score, and after the series exist. |
| Six to eight cards | Receipt for a partial send, and a retry that cannot duplicate a sent card. Principal already deferred this. |

## NOT BUILDABLE WITHOUT A RULE

- Regime colours and the overall regime word (segments 1, 2, 4, regime detector).
- Key message and market narrative (segments 1 and 11).
- Confidence percentage, including signal-board confidence and the confidence engine (segments 11 and 14).
- The mockup health percentage of 42%. The only written health formula is unmerged and does not yield 42% from one fresh domain out of six.
- Catalyst intensity (segment 12).
- Positioning state and interpretation (segment 7).
- Scenario behaviour, confirmation, and the five invalidation lines (segment 13, scenario generator).
- Signal-board states (segment 14, signal engine).
- Thesis-scorecard precision (segment 15).
- Anomaly flags that are not the sign of two stored numbers, including the word "confirmed" (segment 16).
- Macro "driven by" label (segment 6b).
- Momentum arrow, unless it is defined as the sign of a named return (segment 6a).
- Liquidity regime (segment 18).
- News direction, magnitude, and confidence (segment 19).
- The segment 20 legend of confirmed, developing, stress, divergence, watch, tick, and invalidated.

Arithmetic that can wait for stored prints, and is not in that list: `trailing_return`, `sma`, a ratio of two HELD mids, and the sign of those changes.
