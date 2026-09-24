# Phase 3 Market Pulse (US session briefs) — Principal Phase 2 pre-market DoD

Australia/Sydney is the ops timezone for humans. **US session wall-clock is `America/New_York`.** Fire times are converted with `zoneinfo` (DST-correct). Every timestamp stored in Postgres is `timestamptz` UTC. Point-in-time knowledge uses `ingested_at`, never `published_at` alone.

This runbook does **not** enable live trading, wallets, or signing. Briefing is read-only.

Plan: [ops/plans/IMP-002-us-market-pulse.md](../../ops/plans/IMP-002-us-market-pulse.md).

## What it produces

| Mode | Command | Artifact |
|---|---|---|
| US pre-market | `lab brief preopen` | **DoD:** `briefs/YYYY-MM-DD/us-pre-market.md` **and** legacy `briefs/YYYY/MM/DD/preopen.md` (identical bytes) |
| US close | `lab brief close` | `briefs/YYYY/MM/DD/close.md` |
| Intraday alerts | `lab brief alert-check` | `briefs/YYYY/MM/DD/alert.md` **only if a numeric threshold is crossed** |

Alerts **never push** if `config/briefing/alerts.yaml` is missing, `require_threshold_config` is true without numeric thresholds, or no threshold is crossed. There is no free-text commentary path.

## Frozen fixture (deterministic hash)

CI and local tests generate briefs from `tests/fixtures/briefing/frozen_day.json` (session date **2026-03-10**). The pre-open and close SHA-256 hashes are pinned:

```bash
uv run lab brief preopen \
  --fixture tests/fixtures/briefing/frozen_day.json \
  --repo-root . \
  --out /tmp/market-pulse \
  --no-db

# content_hash must match tests/fixtures/briefing/frozen_preopen.sha256
# writes both /tmp/market-pulse/briefs/2026-03-10/us-pre-market.md
# and /tmp/market-pulse/briefs/2026/03/10/preopen.md
```

Same for `lab brief close`. Do not edit the golden markdown/`sha256` files unless the renderer change is intentional; update both together.

## Live / operator path

```bash
docker compose up -d
uv sync --all-packages
uv run lab migrate

# 1. Ingest Hyperliquid public info into Market Memory (preferred HL source of truth)
uv run lab ingest --fixture tests/fixtures/hl_window.json --no-objects
# or: uv run lab ingest --window 7d

# 2. Fixture brief (deterministic)
uv run lab brief preopen --as-of 2026-03-10T12:00:00Z --fixture tests/fixtures/briefing/frozen_day.json --no-db

# 3. Live public slice (Principal Phase 2). Missing keys → unavailable/partial; never invented.
#    Polygon ETF proxies (SPY/QQQ/UUP/USO) + FRED if FRED_API_KEY; crypto SoR = HL mid_px;
#    CoinGecko ALWAYS fetched on --live (secondary DQ). Stooq not primary (SRC-STOOQ-404).
uv run lab brief preopen --live --no-db
```

Without `--fixture` and without `--live`, HL conditions come from `what_did_we_know(as_of)` when Postgres is available. Macro defaults to `mode: off` (`unavailable`) unless you pass `--fixture`, `--live`, or set `config/briefing/macro.yaml` mode.

```bash
uv run lab brief close --as-of 2026-03-10T20:15:00Z
uv run lab brief alert-check --as-of 2026-03-10T14:00:00Z

uv run briefing-worker next --from 2026-03-06T00:00:00Z --days 5
uv run briefing-worker once --kind preopen --fixture tests/fixtures/briefing/frozen_day.json --no-db
```

Schedule (weekdays, `America/New_York` wall clock):

- Pre-open: **08:00**
- Close: **16:15**

Those instants shift by one UTC hour across US DST. Tests cover the 2026-03-08 spring-forward and 2026-11-01 fall-back.

## Macro / calendar sources

- **Fixture** (tests + default deterministic path): JSON/YAML, no network.
- **Live** (`--live` or `config/briefing/macro.yaml` mode: live): **Polygon** stocks-plan ETF proxies for equity/USD/oil Pulse slots (`POLYGON_API_KEY`), FRED (key from `FRED_API_KEY`), **CoinGecko always fetched** when `ids` are configured. Stooq CSV is **not** the primary path (`SRC-STOOQ-404`). **Crypto pulse SoR is Hyperliquid `mid_px`** for BTC/ETH What-moved table slots. Missing keys or HTTP errors set `unavailable`/`partial` and keep going. **Never invent missing prints. Never commit secrets.**
- Calendar is `config/briefing/calendar.yaml` (the approved attributable source). There is no live calendar API; an empty window is printed honestly.

### Crypto pulse source of record (Fix 3)

| Slot | Source of record | Honesty |
|---|---|---|
| BTC / ETH (What-moved / cross-asset **table**) | Hyperliquid `mid_px` | Venue **perp mid**, not CoinGecko spot. Prior close stays `n/a` unless a prior mid exists — never invent a 24h move from a single mid. |
| CoinGecko | Secondary DQ — **always fetched on `--live`** | Values (or `unavailable` notes) are retained in the artifact alongside HL. A source only fetched when primary fails cannot canary. |

**(a) Normal path:** table prints HL mid as SoR. Notes carry CoinGecko spot **and** HL mid/oracle with **both** `source=` tags and **both** `as_of=` stamps, plus divergence in bps.

**(c) Escalation:** if `|divergence| >` the path threshold → DQ event `error_class=source_divergence`, degrade that slot's quality to `partial`. Do **not** silently prefer HL on a large disagreement (mid still printed as SoR; disagreement is explicit).

**Divergence metric (spot vs perp basis):**

| Prefer | Formula | Metric tag | Threshold |
|---|---|---|---|
| HL `oracle_px` available | `|CG_spot − HL_oracle| / HL_oracle` | `metric=cg_vs_hl_oracle` | `crypto_pulse.divergence.max_bps` **100** |
| Oracle missing | `|CG − HL_mid| / HL_mid` | `metric=raw_mid_vs_spot`, `confidence=low`, basis not subtracted | `max_bps_raw_mid_vs_spot` **300** (wider — mid embeds perp basis) |

Default oracle threshold **100 bps** sits above normal BTC mark−oracle basis (~5–50 bps, e.g. ~49.4 on ~86k ≈ 5–6 bps) but catches wrong ticker / stale feed / splice. Raw-mid fallback **must not share 100 bps**: under stress perp basis can widen well past tonight's ~5–6 bps and would false-fire `source_divergence` precisely when confusing. Separate **300 bps** still catches gross wrong-ticker/stale/splice without treating stress basis as a feed failure; escalations tag `confidence=low` and say basis was not subtracted.

Hypothesis (non-binding): CoinGecko public endpoints may be rate-limited or blocked on some operator boxes while HL `/info` works. Always-fetch keeps the failure visible in notes; do not invent figures either way.

Shared GET helper (`mm_common.http`, also used by `lab data source-health` and HL `/info`): default timeout **8s**; **up to 5 attempts** with exponential backoff + jitter (honour `Retry-After`; ceiling several seconds) on `timeout` / `unreachable` / `429` / `5xx`. HTTP **404 is terminal** (no retry, no scrape fallback). Per-source overrides under `config/briefing/macro.yaml` → `live.http` / `live.coingecko` and `config/ingest.yaml` → `rate_limits.*`.

Every market-data section has an as-of timestamp. Pulse display quality is `fresh | stale | partial | unavailable` (`ok` maps to `fresh` in markdown). Snapshot HL fields label capture/`ingested_at`; they do not disguise capture time as exchange `market_time`.

### Observation age → quality (FRED; per-series lag)

**Fetch success is not freshness.** Quality for cadence-gated sources is computed from observation age vs the brief knowledge clock:

| Clock | Meaning |
|---|---|
| Observation date | FRED series observation `date` (stored on `AssetPrint.as_of`) |
| Knowledge clock | Brief `as_of_knowledge` / live capture `as_of` (never `published_at` alone) |
| Age | Calendar days: `knowledge_date − observation_date` |

Config: `config/briefing/macro.yaml` → `freshness.fred`:

| Field | Default | Effect |
|---|---|---|
| `cadence` | `daily` | Source-level default cadence label |
| `max_calendar_lag_days` | `2` | **Daily default.** If age **>** this value → `stale` (display may show `stale (Nd)`). Never `fresh`. Applies to any FRED series **without** a per-series override (e.g. US10Y / DGS10). |
| `series.<SYMBOL>` | — | Per-series override. Set `cadence` + `max_calendar_lag_days` for monthly / low-cadence prints. Optional `fred_series_id` for matching by FRED id. |

**Why per-series:** A global daily lag of 2 would falsely mark monthly FRED (CPI, NFP/payrolls) stale every time — those prints are legitimately 30+ days old relative to a month-start observation stamp. Monthly overrides (default **45** calendar days for CPI / NFP in repo config) keep a ~30–45d print eligible for fresh; only past that series' own threshold → stale.

Principal-reasonable daily default: FRED daily series older than **2 calendar days** behind `as_of_knowledge` cannot be labelled fresh. The 2026-09-22 US Close Brief incident (US10Y as-of 2026-09-18, four days old, shown as fresh / +7.0bp) is the motivating case — a 4-day-old *daily* print must render as stale with age visible, not fresh. A stale print does not yield a change.

Layer: `mm_briefing.freshness` (shared helper; `lag_for(source, symbol, series_id)` for calendar policies) + live FRED fetcher + `complete_cross_asset` gate so all Pulse consumers see the same FRED rule.

Memory ingest of FRED remains `historical=True` (facts about the past are not snapshot-stale in Market Memory). Pulse live display is a separate product surface and applies the calendar lag gate above. FRED Monday (a Friday print with no newer business-day print, still calendar-stale on Monday) is unchanged.

### Gate by default

A freshness gate scoped to the one source that exposed a bug leaves every other enabled source able to render as fresh. The gate is the default. Config load fails if a live source the brief will turn on has no `freshness.<source>.policy`. Polygon is included: `policy` must be `session` (a calendar-day policy is rejected). Static `enabled: false` still counts when the source has a symbol / series / id map, because `--live` turns those maps on. Named exemptions (`policy: exempt` plus a non-empty `exemption`) are allowed and must say why; a missing reason fails load. There is no `_GATED_SOURCES` allow-list. No enabled source in this file uses an exemption.

| Source on the live brief | Policy in `macro.yaml` |
|---|---|
| FRED | `calendar` (daily default 2; CPI/NFP monthly 45) |
| Polygon ETF proxies | `session` (below) |
| CoinGecko | `snapshot` (`max_snapshot_lag_minutes: 20`; endpoint has no vendor timestamp, fetcher stamps capture) |
| Hyperliquid perp mid | `snapshot` (same 20-minute capture lag; `hyperliquid.info /info` matches this rule) |
| Stooq | Not enabled (`symbols` empty). Enabling it without a policy fails load. |

### Polygon session freshness (US equity session)

US equity regular hours, `America/New_York`. Product rule: **has a newer session bar become due that we are not showing?**

| Clock vs 16:00 America/New_York | Print on screen | Quality |
|---|---|---|
| Before today's cash close | Prior session close | fresh |
| After the close, inside `grace_minutes` | Prior session close | fresh, note `pending session` (not stale) |
| After the close + grace | Prior session, newer bar due | stale. No change / Δ |
| Any of the above | The bar for the session that is already due | fresh |

#### Publish lag (how it was read)

The brief calls `GET /v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}`.

On 2026-09-24 the vendor Plan Recency table for that endpoint was fetched from [custom bars](https://massive.com/docs/rest/stocks/aggregates/custom-bars):

| Plan | Recency |
|---|---|
| Stocks Basic | End-of-day (no minute in the table) |
| Stocks Starter | 15-minute delayed |
| Stocks Developer | 15-minute delayed |
| Stocks Advanced | Real-time |
| Stocks Business | Real-time |

`POLYGON_API_KEY` was unset in the environment that wrote this. No request was sent to `api.polygon.io`. This key's first-seen minute was **not** stopwatched. The repo does not name which stocks plan the key is on. Ingest's Polygon budget is 5 requests/minute, which is free-tier shaped and closer to Basic than to a named delayed plan.

`grace_minutes: 20` is that documented **15-minute** Starter/Developer recency plus 5 minutes. A brief at 16:30 America/New_York (primary Sydney-morning cron `20:30 UTC` while the US is on EDT) is past this grace. While the US is on EST that same UTC cron is 15:30 ET, still before the close, so the prior bar is the correct fresh print. If the key is Basic, "End-of-day" still has no clock, and 20 minutes can false-stale a 16:30 ET brief.

A later stopwatch, when a key is present: after 16:00 America/New_York on a regular session, poll `GET /v2/aggs/ticker/SPY/range/1/day/{session}/{session}?adjusted=true` until `results` contains that session date. Record minutes after 16:00. Repeat on several regular sessions. Replace `grace_minutes` from the observed maximum plus a small buffer.

#### Known limitations — the 16:00 calendar does not cover these

Early closes at **13:00 ET** (not in the calendar). Until the hard-coded 16:00, a missing new bar stays fresh and is not yet `pending session`. That is a false-fresh window, not a correct early close:

- Friday after Thanksgiving (13:00 ET)
- Christmas Eve when it is a weekday (13:00 ET)
- July 3 when it is a midweek session (13:00 ET)

Full weekday closures are **false-stale** after 16:00 ET + grace (same honesty class as FRED Monday). The prior bar is marked stale even though no newer session exists. Observed-weekday shifts of these names are uncovered too:

- New Year's Day
- Martin Luther King Jr. Day
- Presidents Day
- Good Friday
- Memorial Day
- Juneteenth
- Independence Day
- Labor Day
- Thanksgiving Day
- Christmas Day

### Hardened failure modes (live)

| Source | Typical class | What operators see | What not to do |
|---|---|---|---|
| Polygon stocks ETF proxies (`SPY`/`QQQ`/`UUP`/`USO`) | `missing_env` if `POLYGON_API_KEY` unset; else `timeout` / `http_5xx` / `rate_limited` / `parse_error` | Slot listed with **proxy** label + source=`polygon`; n/a when fetch fails | Do **not** present ETF last as ES/NQ/CL/DX futures. Do not invent. Key never committed. |
| Polygon / CME futures (true ES, NQ, CL) | structural (not on stocks plan) | Not fetched; ETF proxies used instead | Do not buy/scrape a CME pass-through in this path. |
| Polygon / Cboe VIX | structural (not on stocks plan) | VIX slot **unavailable** with reason (VIXY is not VIX) | Do not scrape Cboe JSON; do not label VIXY as VIX. |
| Stooq CSV `https://stooq.com/q/l/` | `http_404` (`SRC-STOOQ-404`), `timeout`, `http_5xx`, `parse_error` | Optional canary only; Pulse primary is Polygon proxies | Do **not** add HTML scrapers, country mirrors, or Yahoo/investing.com fallbacks (ToS). |
| FRED | `missing_env` if `FRED_API_KEY` unset; else `timeout` / `http_5xx` / `tos_or_blocked` / `parse_error` | Rates slot **unavailable**; note names the env, never the value | Do **not** commit the key. Do not paste it into git, briefs, or tickets. |
| CoinGecko | `timeout` / `http_5xx` / `rate_limited` | Always attempted on `--live`; unavailable note **kept**; when HL mid fills the table, also emit `divergence not computed (coingecko 429)` (or the closed `error_class`) — never silent | Do not invent last/prior. Do not strip CG notes. |
| CoinGecko ↔ HL | `source_divergence` when `|div| >` path threshold | Slot quality → `partial`; DQ event with both stamps; raw path tags `metric=raw_mid_vs_spot` `confidence=low` | Do not silently prefer HL on a large disagreement. |
| Hyperliquid `/info` | allowlist only | Memory first; `--live` fallback still refuses wallet/user types; **crypto pulse SoR** for BTC/ETH mid | No `hl_trade` / signing. Do not invent prior_close from mid alone. |

### Polygon ETF proxies (Fix 2 / SRC-STOOQ-404)

Stooq futures/index CSV (`es.f`, `nq.f`, `dx.f`, `cl.f`, `^vix`) has returned `http_404` since 2026-09-17 (`SRC-STOOQ-404` stays **OPEN**). Pulse live routing prefers Polygon stocks-plan ETFs where the keyed plan covers them:

| Pulse slot | Polygon ticker | Honesty |
|---|---|---|
| ES | SPY | ETF proxy for S&P 500 — **not** ES futures |
| NQ | QQQ | ETF proxy for Nasdaq-100 — **not** NQ futures |
| DXY | UUP | USD ETF proxy — **not** DX futures / DXY |
| CL | USO | WTI oil ETF proxy — **not** CL futures |
| VIX | — | **Structurally unavailable** without Cboe entitlement; VIXY is not VIX |

True CME futures prints need a futures subscription / CME Information License the lab does not have. Config: `config/briefing/macro.yaml` → `live.polygon`. Incident: [ops/improvement-queue.md](../../ops/improvement-queue.md) `SRC-STOOQ-404`.

Live pre-market footer points at `lab data source-health` → `ops/reports/source-health/` (pointer only; the brief does not embed a health report). Fixture briefs omit that line so frozen hashes stay pinned.

### FRED_API_KEY (operators)

1. Request a personal API key from FRED (St. Louis Fed) — the lab does not buy or vendor a shared key in git.
2. **Local:** `export FRED_API_KEY=…` in the shell, or set it in gitignored `.env` (see `.env.example`). Never commit `.env`.
3. **CI:** add a repository secret named `FRED_API_KEY` if a workflow needs live FRED. Current `test.yml` does **not** require it; unit tests mock HTTP and assert missing-env degrades.
4. Confirm with `uv run lab data source-health --no-db` (FRED row `credentials_present=yes`, no key in the markdown) and/or `uv run lab brief preopen --live --no-db` (US10Y listed, not invented).

Standing source-health (Data desk, not this brief): [source-health.md](source-health.md). Plan: [ops/plans/IMP-004-pulse-source-hardening.md](../../ops/plans/IMP-004-pulse-source-hardening.md).

## Config that must stay true

- `config/briefing/alerts.yaml` → `require_threshold_config: true` with numeric thresholds per enabled type.
- `config/schedules/market-pulse.yaml` → timezones `America/New_York` + `Australia/Sydney`.
- No execution, signing, wallets, or risk-service calls from briefing.
- Pre-market footer is informational only (no decision / no order intent).

## Optional DB index

If Postgres is up and you omit `--no-db`, a `brief` row is written (kind, session_date, content_hash, artifact path). Markdown under `briefs/` remains the human artifact. Generated dated files are gitignored except an explicit committed sample on the DoD path.

