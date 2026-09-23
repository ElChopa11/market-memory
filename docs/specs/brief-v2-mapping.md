# Brief v2 token mapping

Source of record for binding every `{TOKEN}` in [brief-v2-template.md](brief-v2-template.md). The template is format only. This file does not add generators.

One row per distinct token name. Shared names (`{VAL}`, `{ICON}`, `{BAR}`) have one row. A use marked Neon or later in that row stays unbound. No token is computed by judgement or an LLM.

Unavailable fields render ⚪ and the literal word `unavailable` (house glyph: `config/briefing/presentation.yaml` `states.unavailable.icon`). The field is not omitted. `{DATE}` uses the brief stamps already rendered. No second clock. Header health percent is `mm_briefing.health.score_data_health`, not `worst_quality`.

Stage values: `now` | `Neon` | `later`.

| token | source of record | field path | unit | derivation rule | stage (now / Neon / later) | fallback when unavailable |
|---|---|---|---|---|---|---|
| `{3_SENTENCE_SUMMARY}` | `mm_briefing.render.KEY_TAKEAWAY_LINES` | n/a (no generator) | text | `INSUFFICIENT DATA` until a restatement-only generator is coded and tested. Future rule, not implemented: restate rendered values only; no "suggests"; no "indicates"; same provenance as the table; if degraded, name missing feeds only | now | `INSUFFICIENT DATA` |
| `{ASSET}` | Unverified — needs Intel | n/a (Message 6 not wired) | text | no formula | later | ⚪ `unavailable` |
| `{BAR}` | Unverified — needs Intel | n/a (no bar scale in repo) | glyph | no formula. Not `DATA_HEALTH_PCT` | later | ⚪ `unavailable` |
| `{CONDITION}` | Unverified — needs Intel | n/a (no scenario config) | text | no formula | later | `INSUFFICIENT DATA` |
| `{CONDITION_1}` | Unverified — needs Intel | n/a (no scenario config) | text | no formula | later | `INSUFFICIENT DATA` |
| `{CONDITION_2}` | Unverified — needs Intel | n/a (no scenario config) | text | no formula | later | `INSUFFICIENT DATA` |
| `{CONDITION_3}` | Unverified — needs Intel | n/a (no scenario config) | text | no formula | later | `INSUFFICIENT DATA` |
| `{CONF}` | Unverified — needs Intel | n/a (Message 6 not wired) | 1 | no formula. Not `observation.confidence` | later | ⚪ `unavailable` |
| `{CONFIDENCE_OR_"INSUFFICIENT HISTORY"}` | Unverified — needs Intel | n/a (no signal log) | text | no formula. Not a percentage | later | `INSUFFICIENT HISTORY` |
| `{CRYPTO_ICON}` | `config/briefing/presentation.yaml` `domains[id=crypto]` | `mm_briefing.health.score_data_health` → `DomainHealth.state` for symbols BTC, ETH | glyph | `icon = states[worst_health_state(pulse_to_health_state(AssetPrint.data_quality))].icon` | now | ⚪ `unavailable` |
| `{CURLY_BRACES}` | `docs/specs/brief-v2-template.md` intro | n/a (syntax example, not a fill) | n/a | `none` | later | do not bind |
| `{DATA_HEALTH_BAR}` | `mm_briefing.health.HealthReport.pct` | `score_data_health` | glyph | glyph scale Unverified — needs Intel. Input is `{DATA_HEALTH_PCT}` only. Not `worst_quality` | later | `INSUFFICIENT DATA` |
| `{DATA_HEALTH_PCT}` | `mm_briefing.health.score_data_health` | `HealthReport.pct`; weights `config/briefing/presentation.yaml` `states.*.weight` | percent | `round(100 * sum(weight(domain.state) for domain in scored) / count(scored))`. `structural_unavailable` excluded from `scored`. Not `worst_quality` | now | `INSUFFICIENT DATA` |
| `{DATE}` | `mm_briefing.render._date_fill` | `BriefDocument.generated_at` in UTC, `America/New_York`, `Australia/Sydney`; `BriefDocument.as_of_knowledge`. Pre-open also `memory_watermark` when that line is already rendered. `observation.as_of_knowledge = ingested_at` | timestamp | concatenate those stamps. No second clock | now | ⚪ `unavailable` |
| `{DIR}` | Unverified — needs Intel | n/a (Message 6 not wired) | sign | `sign(Δ)` once the series is named. Not an LLM | later | ⚪ `unavailable` |
| `{DOMINANT_DRIVER_OR_"indeterminate"}` | Unverified — needs Intel | n/a (no versioned driver rule in config) | text | versioned config rule only. Not an LLM read of the tape | later | `indeterminate` |
| `{EQ_DIR}` | Unverified — needs Intel | which equity slot (ES vs NQ) is not named | sign | `sign(Δslot)` with `Δ1D = (last - prior_close) / prior_close`. Not an LLM | Neon | ⚪ `unavailable` |
| `{EVENT_LIST_OR_"none scheduled"}` | `config/briefing/calendar.yaml` | `mm_briefing.calendar.relevant_events` → `CalendarEvent.when`, `.name`, `.importance`, `.source` | text | list events in the existing look-ahead window. Not a news scraper | now | `none scheduled` |
| `{FRESHEST_FEED_NAME}` | `mm_briefing.render._freshest_feed_name` | `AssetPrint.symbol` where `AssetPrint.as_of = max(as_of)` on the rendered snapshot rows. FRED as_of is the series observation date (`DGS10` for US10Y) | slot id | `argmax(AssetPrint.as_of)`; ties keep every symbol in render order | now | ⚪ `unavailable` |
| `{ICON}` | `config/briefing/presentation.yaml` `states` | `mm_briefing.health.pulse_to_health_state(AssetPrint.data_quality)` | glyph | `icon = states[state].icon`. Data state only, not a direction. Quadrant icon waits on `{QUADRANT_LABEL}` (Neon) | now | ⚪ `unavailable` |
| `{LABEL}` | Unverified — needs Intel | n/a (no scenario config) | text | no formula | later | `INSUFFICIENT DATA` |
| `{LEADING_CLUSTER_OR_"none"}` | Unverified — needs Intel | n/a (no versioned cluster rule in config) | text | versioned config rule only. Not an LLM read of the tape | later | `none` |
| `{LEVEL}` | Unverified — needs Intel | n/a (Message 6 not wired) | text | no formula | later | ⚪ `unavailable` |
| `{LIQUIDITY_ICON}` | Unverified — needs Intel | n/a (no liquidity domain in `presentation.yaml`) | glyph | `icon = states[state].icon` once a slot is named | later | ⚪ `unavailable` |
| `{MAG}` | Unverified — needs Intel | n/a (Message 6 not wired) | 1 | no formula | later | ⚪ `unavailable` |
| `{MISSING_FEEDS_LIST}` | `mm_briefing.render._missing_feeds_list` | `AssetPrint.symbol` where `pulse_to_health_state(AssetPrint.data_quality) = unavailable`. Includes structural VIX | slot id | every such symbol in render order. Empty list is `none` | now | `none` |
| `{QUADRANT_LABEL}` | `mm_briefing.hl` snapshot only (`mid_px`, `open_interest`); deltas need Neon | `sign(Δprice) × sign(ΔOI)` | label | `quadrant = sign(Δprice) × sign(ΔOI)`. `Δprice = (last - prior_close) / prior_close`. `ΔOI = (oi - oi_prior) / oi_prior`. Not an interpretation | Neon | `INSUFFICIENT DATA` |
| `{RATES_DIR}` | `config/briefing/macro.yaml` `fred.series.US10Y` | `AssetPrint` symbol `US10Y`, `fred_series_id` `DGS10`, `AssetPrint.last` | sign | `sign(Δ1D)` with `Δ1D = (last - prior_close) / prior_close` | Neon | ⚪ `unavailable` |
| `{RATES_ICON}` | `config/briefing/presentation.yaml` `domains[id=rates]` | `DomainHealth.state` for symbol `US10Y` | glyph | `icon = states[pulse_to_health_state(AssetPrint.data_quality)].icon` | now | ⚪ `unavailable` |
| `{REGIME_LABEL}` | Unverified — needs Intel | n/a (no versioned regime rule) | text | no formula. Not risk-on / risk-off | later | `INSUFFICIENT DATA` |
| `{RISK_APPETITE_ICON}` | Unverified — needs Intel | n/a (no risk-appetite domain in `presentation.yaml`) | glyph | `icon = states[state].icon` once a slot is named | later | ⚪ `unavailable` |
| `{RISK_DIR}` | Unverified — needs Intel | n/a (no risk series) | sign | `sign(Δslot)` once the slot is named. Not an LLM | later | ⚪ `unavailable` |
| `{STORY}` | Unverified — needs Intel | n/a (no news scraper) | text | no formula | later | ⚪ `unavailable` |
| `{USD_DIR}` | `config/briefing/macro.yaml` `polygon.symbols.DXY` | `AssetPrint` symbol `DXY`, `quoted_symbol` `UUP`, `AssetPrint.last` | sign | `sign(Δ1D)` with `Δ1D = (last - prior_close) / prior_close` | Neon | ⚪ `unavailable` |
| `{USD_ICON}` | `config/briefing/presentation.yaml` `domains[id=usd]` | `DomainHealth.state` for symbol `DXY` | glyph | `icon = states[pulse_to_health_state(AssetPrint.data_quality)].icon` | now | ⚪ `unavailable` |
| `{VAL}` | Last, where a live slot exists: Polygon `AssetPrint.last` (`ES`/`SPY`, `NQ`/`QQQ`, `DXY`/`UUP`, `CL`/`USO`); FRED `US10Y`/`DGS10` `observations[0].value`; BTC/ETH `HLInstrumentState.metric("mid_px")`. Current HL levels also exist: `open_interest`, `funding`, `basis_mark_oracle`, `liquidation_size_sum`. 2s10s, Gold, Credit, SOL, ZEC, XMR, CB premium, NDX: Unverified — needs Intel | `mm_briefing.models.AssetPrint.last`; `mm_briefing.hl` metrics above | px, or percent when `AssetPrint.unit = "%"` | `Last = AssetPrint.last` (now). Do not fill these until Neon: `Δ1D = (last - prior_close) / prior_close`; `Δ5D`, `Δ20D` from stored prints; `z30d = (x - mean30) / stdev30`; `corr20d(BTC, NDX)`. vs-BTC ratio Unverified — needs Intel | now | ⚪ `unavailable` for Last. `INSUFFICIENT DATA` for Δ, z30d, and corr |
| `{VOLATILITY_ICON}` | `config/briefing/presentation.yaml` `domains[id=vol]` | `DomainHealth.state` for symbol `VIX` (`structural_unavailable`, excluded from the health denominator) | glyph | `icon = states[pulse_to_health_state(AssetPrint.data_quality)].icon` | now | ⚪ `unavailable` |
