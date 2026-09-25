# Brief v2 — US Close / Sydney Morning presentation

Principal target-spec, 2026-09-23. Paper only. The token-only target layout is [brief-v2-template.md](brief-v2-template.md) (format only). Token binding source of record is [brief-v2-mapping.md](brief-v2-mapping.md). This file describes the **end state**, then **stages** what may be built. Stage A fills only template tokens that already have inputs. Stage B and Stage C are not built.

Hive group send stays frozen. This spec does not dispatch workflows, does not edit the Sydney morning cron, and does not send Telegram.

## Shipped morning path

This change brings Stage A forward from draft #109 onto current main and applies the Principal standing rule inside the renderer. Draft #109 is superseded. Where a later bullet still says to render `INSUFFICIENT DATA`, to keep a field that would read the same every morning, to print `KEY TAKEAWAY`, to repeat `obs none` on every line, or to split the send into cards now, this section wins.

Standing rule: a line that says the same thing every morning is not information.

- The morning Telegram brief (`lab brief close`) is one message of at most 4096 characters, through the existing single `sendMessage`. Multi-send is untested. Cards (6–8, order below) remain the end state and are deferred, not discarded. See [brief-card-split-deferred.md](brief-card-split-deferred.md). The approved render is frozen for captures 1–11. See [brief-format-freeze.md](brief-format-freeze.md).
- `KEY TAKEAWAY` does not ship. The renderer does not print a daily `INSUFFICIENT DATA` line. A panel that cannot vary is omitted.
- Empty sections are omitted. They are never rendered as `none`.
- `obs none` is one header state, never per line.
- The overnight reference block is not rendered.
- A metric is shown when it is non-zero or changed versus the prior capture. Otherwise its name sits on one `gaps:` line, and the metric line returns on the first morning it is non-zero or changed.
- Basis is omitted when there is no prior capture. When a prior exists, the line prints that prior value beside the current value.
- Prior values are read through `mm_briefing.prior` (`captured_at`, `prior_captured_at` on #122 retain rows). Capture 1 and a read failure are no prior: basis omitted, `changed` falls back to non-zero only. The brief does not fail.
- Messages 3 and 4 render only panels that can be filled from data that exists today. Transmission chain, cluster leadership, Δ5D/Δ20D, z30d, and the quadrant legend are omitted. Message 5 prints Hyperliquid metrics that pass the gaps rule.
- The eight price rows stay, with the proxy ticker in the Symbol column and the change cell, except a slot whose last is missing: that slot is named on the `gaps:` line and does not occupy a row. Source, Quality, and Label are not columns. Labels are in [brief-row-labels.md](brief-row-labels.md). A quality marker is appended only when the row is not fresh and the change cell is not already `no new session` / `no new print`.
- Health is a coverage rollup, not a pass/fail. A missing last is `unavailable` (weight 0), including structural VIX, so the line lists it and does not call it fresh. An observation date that matches the prior capture is `stale` (weight 0). That is the correct change cell (`no new session` / `no new print`); it is not a failure and it is not fresh. Crypto is not marked stale for a repeated as-of. Weights stay fresh 1, degraded 0.5, stale 0, unavailable 0. The morning line lists only domains that are not fresh (`Health 43% stale Equities USD Oil; n/a Vol`), at most two lines of 42 characters. When every scored domain is fresh the line is `Health 100%`.
- Funding is shown only when the hourly Hyperliquid print is off the interest baseline. The docs fix that baseline at 0.01% per 8 hours (`0.0001`), paid each hour at one eighth, so the hourly baseline is `0.0000125`. A print is on baseline when it is within half of `1e-6` of that rate (the recorded prints use 6 decimal places; `0.000013` is on baseline). Otherwise the name goes to `gaps:`. Cite: Hyperliquid funding, interest component 0.01% / 8h.
- Delivery is Telegram `parse_mode=MarkdownV2`. Pipe tables are not rendered, so the headline is a fenced pre block. The dry-run file is the escaped `sendMessage` text.
- The `As-of knowledge` line is not rendered. The UTC clock line is the capture time.
- A change cell follows the observation as-of, not value equality. The same equity vendor bar date as the prior capture prints `no new session since <date>`. The same FRED observation date prints `no new print since <date>`. A new as-of with an identical value prints `0.00%` or `+0.0bp`. Crypto rows always print the computed change. No prior keeps the existing numeric delta. When a crypto print has no vendor prior close, the change is versus the prior capture.
- Funding is the hourly Hyperliquid rate, printed annualised, and only when it is off the baseline above. On baseline it is a gap even when a prior exists. Open interest is rounded and shown with the prior capture when one exists; with no prior, the name goes to the `gaps:` line. Basis is shown only with that prior. Mid is the headline last and is not repeated.
- Every line inside the pre block is at most 42 characters. Headings are plain lines. A `#` marker is not used, because a MarkdownV2 pre block prints it as a character.
- `LATE`, `DEADMAN`, and `CAPTURE` are appended in that order by `append_dm_status_lines` (alias `append_brief_status_lines`) and stay outside the fence, after the pre block. DEADMAN is `DEADMAN: MISSING` when the Healthchecks start ping is not HTTP 200. CAPTURE is `CAPTURE: <rows>/<expected> rows (37 instruments) @ ...` from the retain helper. `--no-send` does not append them.

## Why it stages

About 70% of the end state is delta-based: Δ1D/5D/20D, the cross-asset heatmap, what-changed, positioning state, anomalies, and the scorecard. Those need stored history.

Intel packet `ops/reports/intel-packets/2026-09-23-us-close-obs-none-neon-backlog.md` states: unique fields 20 = persistence 16 + missing source/key 6 + unwired 0. Building the visual layer before Neon yields a dashboard of em-dashes.

Neon backlog is not a VIX entitlement. VIX stays structural unavailable (Cboe; not on the Polygon stocks plan). A Neon backfill does not create a VIX print.

## Hard rule

Only do this if the methodology is fully defined and the historical data is actually stored. Otherwise you create fake precision.

No confidence percentage, no regime label, and no precision figure computed from absent data. If the inputs are not there, the panel says **INSUFFICIENT DATA** and shows nothing else. A 60% confidence bar derived from nothing is worse than no bar.

Icons in this spec are **data state only**. Green is not a direction and is not a buy.

## End state (describe, do not build here)

One US Close / Sydney Morning brief, split across 6–8 Telegram cards. Skip a card that has nothing to say. Never send a card of dashes.

| Panel | What it is when the inputs exist |
|---|---|
| Regime panel | Mechanical, versioned config. Example shape: risk-on = equities up + spreads down + vol down + USD down. No subjective bullish/bearish score. |
| Data health score | Percentage plus a per-domain state column. |
| Cross-asset heatmap | Δ1D / Δ5D / Δ20D across the slot set, from stored prints. |
| OI × price matrix | Open-interest change against price change, from stored HL history. |
| Scenario map | Named paths with triggers that are defined in config and evaluable from stored data. |
| Signal board | Thesis scorecard, signal precision, confidence — only from the instance ledger. |

### Card order

1. executive
2. dashboard
3. macro
4. crypto
5. positioning
6. catalysts
7. scenarios
8. audit

Skip empty cards entirely. Never send a card of dashes.

### Regime

Definitions must be mechanical and versioned in config. Spec shape example: risk-on = equities up + spreads down + vol down + USD down. No subjective bullish/bearish scoring anywhere.

Stage A does **not** invent regime labels without methodology and stored history. Stage A stubs the panel as **INSUFFICIENT DATA** when regime config and history are not ready.

## STAGE A — now (no history required; pure presentation)

Implemented with this spec. Inputs are the prints the brief already has. Nothing here computes a delta engine, a heatmap, a regime, or a confidence score.

1. **Data health score** replaces the worst-slot header (`Data quality: unavailable` / `Overall data quality`). A structural miss such as VIX must not zero the header. The score is a coverage rollup of observed states with weights versioned in [`config/briefing/presentation.yaml`](../../config/briefing/presentation.yaml): fresh 1.0, degraded 0.5, stale 0.0, unavailable 0.0. Structural-unavailable prints (VIX entitlement) are listed and **excluded from the denominator**. If nothing is scored, the line is **INSUFFICIENT DATA**, not 0% invented from an empty set and not a confidence bar.
2. **Per-domain state column.** States: fresh / degraded / stale / unavailable, rendered as icons. Icons = data state only, never direction. `partial` maps to degraded. The domain table is the dashboard card.
3. **Message splitting.** 6–8 sequential Telegram cards in the order above, not one body chunked at 4096. `lab deliver pack --from-markdown` uses the cards when the file is a US Close or US Pre-Market brief. A single card that exceeds the Telegram cap may still be safety-split; that is not the product design. Desk packs that are not pulse briefs keep the existing 4096 sequencer.
4. **Skip empty cards.** Positioning and scenarios are omitted in Stage A (no methodology + stored history). A calendar that only says "none" is omitted. An all-n/a price table is not sent as the macro card; those rows stay on the audit card. A card whose body is only dashes is omitted.
5. **Proxy symbol column.** When the print is a Polygon ETF proxy, the Symbol column is the ticker that was quoted (`SPY`, `QQQ`, `UUP`, `USO`). The label says what it proxies, so 28.48 / 144.08 are not read as DXY / CL. The slot id stays on the Slot column and as `slot=` on the bullet. VIX has no proxy ticker.
6. **Provenance stays.** Source tags, as_of, #93 proxy labels, observation ids, and `obs none` remain on the audit card and on any card that shows a print. The visual layer sits on top. It does not replace the audit trail.
7. **Regime stub.** Executive says `Regime: INSUFFICIENT DATA` and nothing else in that panel. No risk-on / risk-off label.
8. **`{DATE}`** is the header stamps already rendered: Generated (UTC), America/New_York, Australia/Sydney, and As-of knowledge. Pre-open also repeats the memory-watermark line when that line is already on the brief. Same `generated_at` and `as_of_knowledge`. No second date path.
9. **Audit, from the rendered MacroSnapshot (no Neon).** `{FRESHEST_FEED_NAME}` is the slot symbol, or every slot symbol tied for the latest `as_of`, among the asset rows already on the brief. `{MISSING_FEEDS_LIST}` is every one of those slots whose rendered state is unavailable (including structural VIX). An empty missing list renders `none`. The audit `Data quality:` line is the same health percentage as the header, not `worst_quality`.
10. **`{3_SENTENCE_SUMMARY}` does not ship filled.** Stage A renders the literal line `INSUFFICIENT DATA` under `KEY TAKEAWAY`. No prose. A future generator, not built here, may only restate values present in the render and must not interpret them. No directional language, no "suggests", no "indicates". Every figure must carry the same provenance as the table. If the render is degraded, the summary says which feeds are missing and nothing else. Until those constraints are coded and tested, the line stays `INSUFFICIENT DATA`.

Stage B/C content that would otherwise look like a metric is omitted or, where a named panel must appear, rendered as **INSUFFICIENT DATA** and nothing else. Stage A does not compute confidence, precision, or a regime from absent history. Messages 3–5 are now in the template as tokens. Stage A does not bind those bodies.

### Message 3–5 binding rules (document only; no generators)

These rules are not implemented. Stage A keeps DATE, the audit feed lines, and `INSUFFICIENT DATA` for `{3_SENTENCE_SUMMARY}`. Message 3–5 stay template-only until Stage B.

- Unavailable fields render as ⚪ and the literal word `unavailable` (or the house glyph already used for that state). The field is not omitted.
- `{QUADRANT_LABEL}` is mechanical from the sign of Δprice and ΔOI only. It is not an interpretation. If either delta is unavailable, render `INSUFFICIENT DATA` and do not guess the quadrant.
- `{DOMINANT_DRIVER_OR_"indeterminate"}` and `{LEADING_CLUSTER_OR_"none"}` populate only from a versioned config rule, never an LLM read of the tape. If unresolved, render `indeterminate` and `none` respectively.
- Every Message 5 `z30d` column needs 30 days of history. That is Stage B behind Neon. Stage A leaves it unbound on the `INSUFFICIENT DATA` path.
- BTC vs NDX correlation (20d) is Stage B behind Neon.
- Δ1D / Δ5D / Δ20D on Messages 3 and 4 stay `needs_neon`, the same as the Stage A token audit.

### Related freshness (not a visual panel)

Draft #109 proposed business-day FRED age. This morning-format change does not alter that gate. Daily FRED freshness on main stays calendar lag (default 2). See [../runbooks/market-pulse.md](../runbooks/market-pulse.md). That gate is not Δ5D/Δ20D and it is not Stage B. Monthly CPI/NFP stay on calendar lag 45.

## STAGE B — after Neon

Deltas (Δ1D/5D/20D) including the Message 3–4 columns, BTC vs NDX correlation (20d), Message 5 `z30d` columns, heatmap, OI×price quadrant from stored Δprice and ΔOI, what-changed engine, relative strength, positioning state.

Do not build these on a packet whose history is `obs none`. Only do this if the methodology is fully defined and the historical data is actually stored. Otherwise you create fake precision.

## STAGE C — after the instance ledger

Thesis scorecard, signal precision, confidence scoring.

Same hard rule. A scorecard percentage without a ledger is fake precision. Stage A keeps existing lab right/wrong hooks as audit text and does not attach a confidence figure.

## Out of scope for this change

Stage B, Stage C, Neon persistence (the prior-capture reader is the seam; #122 wires the rows), `obs none` backfill, cron edits, the stamp job, deliver receipts and idempotency, `repository_dispatch`, secrets, and multi-card Telegram send.
