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
#    Uses Stooq + CoinGecko (no key), FRED if FRED_API_KEY is set, HL public /info allowlist.
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
- **Live** (`--live` or `config/briefing/macro.yaml` mode: live): Stooq public CSV, FRED (key from `FRED_API_KEY`), CoinGecko public price. Missing keys or HTTP errors set `unavailable`/`partial` and keep going. **Never invent missing prints. Never commit secrets.**
- Calendar is `config/briefing/calendar.yaml` (the approved attributable source). There is no live calendar API; an empty window is printed honestly.

Shared GET helper (`mm_common.http`, also used by `lab data source-health`): default timeout **8s**; **one** retry only on `timeout` / `unreachable` / `429` / `5xx`. HTTP **404 is terminal** (no retry, no scrape fallback).

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

Principal-reasonable daily default: FRED daily series older than **2 calendar days** behind `as_of_knowledge` cannot be labelled fresh. The 2026-09-22 US Close Brief incident (US10Y as-of 2026-09-18, four days old, shown as fresh / +7.0bp) is the motivating case — a 4-day-old *daily* print must render as stale with age visible, not fresh.

Layer: `mm_briefing.freshness` (shared helper; `lag_for(source, symbol, series_id)`) + live FRED fetcher + `complete_cross_asset` gate so all Pulse consumers see the same rule. Stooq / CoinGecko cadence thresholds are out of scope for this fix (separate routing work).

Memory ingest of FRED remains `historical=True` (facts about the past are not snapshot-stale in Market Memory). Pulse live display is a separate product surface and applies the calendar lag gate above.

### Hardened failure modes (live)

| Source | Typical class | What operators see | What not to do |
|---|---|---|---|
| Stooq CSV `https://stooq.com/q/l/` | `http_404`, `timeout`, `http_5xx`, `parse_error`, `tos_or_blocked` | Slot stays **unavailable**; note includes `error_class=…`; no Close invented | Do **not** add HTML scrapers, country mirrors, or Yahoo/investing.com fallbacks (ToS). Treat cloud-IP 404 as unavailability. |
| FRED | `missing_env` if `FRED_API_KEY` unset; else `timeout` / `http_5xx` / `tos_or_blocked` / `parse_error` | Rates slot **unavailable**; note names the env, never the value | Do **not** commit the key. Do not paste it into git, briefs, or tickets. |
| CoinGecko | `timeout` / `http_5xx` / `rate_limited` | Crypto slot unavailable if the public price call fails | Do not invent last/prior. |
| Hyperliquid `/info` | allowlist only | Memory first; `--live` fallback still refuses wallet/user types | No `hl_trade` / signing. |

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

