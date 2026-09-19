# Polygon equities + Hyperliquid structure (Phase 5b / IMP-010)

Read-only ingest into Market Memory. **No orders, no signing, no Telegram, no `live.yaml`.** Equities default vendor is **Polygon** (Principal lock; Ask is N/A).

## Dry-run without live keys (CI / laptop)

Fixtures are the operator path when `POLYGON_API_KEY` / `FRED_API_KEY` are unset. `--no-db` skips Postgres and object store:

```bash
# Polygon OHLCV (daily + 5m) from fixture
uv run lab ingest --fixture tests/fixtures/phase5b/polygon_ohlcv.json --no-db

# HL funding/OI already in Phase 1 window; structure (basis, l2, predicted funding)
uv run lab ingest --fixture tests/fixtures/phase5b/hl_structure.json --no-db

# Spot cross-check + DQ divergence (Binance side unavailable in this fixture)
uv run lab ingest --fixture tests/fixtures/phase5b/spot_cross_check.json --no-db

# FRED series / missing key / economic calendar
uv run lab ingest --fixture tests/fixtures/phase5b/fred_series.json --no-db
uv run lab ingest --fixture tests/fixtures/phase5b/fred_missing_key.json --no-db
uv run lab ingest --fixture tests/fixtures/phase5b/economic_calendar.yaml --no-db

# SEC EDGAR CBRS/SPCX lockup (IMP-024; --no-db = ELIGIBLE only)
uv run lab ingest --fixture tests/fixtures/edgar/cbrs_spcx_lockup.json --no-db

# Persist a fixture window when Postgres + `--no-objects` (existing Phase 1 path)
uv run lab ingest --fixture tests/fixtures/hl_window.json --no-objects
```

Missing `POLYGON_API_KEY` or `FRED_API_KEY` **never invents** prints. Live adapters and `lab data source-health` mark the feed `unavailable` with `error_class=missing_env`.

## Polygon (default equities adapter)

| | |
|---|---|
| Package | `mm_ingest.equities` (`packages/ingest`) — Intel, not `mm_desks` |
| Vendor | `polygon` (swappable interface; default locked) |
| Secret | `POLYGON_API_KEY` env only. Update `.env.example`; never commit `.env` |
| Tape | Daily OHLCV; 5-minute intraday when the plan allows (403/429 → unavailable) |
| Corporate actions | Dividends + splits (`/v3/reference/...`) when the plan returns rows |
| Earnings | Documented ticker-events path. Free/starter often 403 → `tos_or_blocked`; **not invented** |
| Rate limit | `config/ingest.yaml` → `rate_limits.polygon` (free-tier default 5 req/min) |
| Retry | Shared `mm_common.http` GET: one retry on timeout/429/5xx; 404/401/403 terminal |

Live (optional, needs env key + durable object store unless `--no-objects`):

```bash
# Not required for CI. Degrades without the key.
export POLYGON_API_KEY=...   # gitignored .env or CI secret
uv run lab ingest --fixture tests/fixtures/phase5b/polygon_ohlcv.json --no-objects
```

There is no live “pull all universe equities” default in CI. Universe ticker set is unchanged (`config/universe.yaml`).

## Hyperliquid structure (public `/info` only)

Allowlist adds `l2Book`. Still refused: `clearinghouseState`, `openOrders`, `userFills`, … Bounded retry on the existing POST client (idempotent read-only).

| Metric | Source | Notes |
|---|---|---|
| `funding` / `open_interest` | `metaAndAssetCtxs` + `fundingHistory` | Phase 1; unchanged |
| `basis_mark_oracle` | derived `(mark-oracle)/oracle` | Missing side → partial, not invented |
| `l2_spread` | `l2Book` snapshot | Compact BBO; sizes not invented |
| `predicted_funding` | `predictedFundings` | Already allowlisted |
| `basis_perp_spot` | HL mid vs CoinGecko/Binance public | DQ divergence event; **not executable-arb** |

Spot providers are public GET only (CoinGecko `simple/price`, Binance `ticker/price`). Rate-limit / missing → `unavailable` + `error_class`. Divergence above `crypto.spot_cross_check.divergence_bps` (default 50) sets `data_quality=contradicted` and `not_executable_arb: true`.

## Macro

FRED path stays env-only (`FRED_API_KEY`). Missing key → `unavailable` / `missing_env` (Pulse + source-health + ingest). Economic calendar remains **fixture-friendly** (`config/briefing/calendar.yaml` and `tests/fixtures/phase5b/economic_calendar.yaml`). No live calendar API in 5b.

## Source health

New inventory rows (always listed): `hyperliquid.structure`, `binance.public`, `polygon`. Degrade classes match Pulse (`missing_env`, `rate_limited`, `http_404`, `tos_or_blocked`, …). The report still copies **no** prints.

```bash
uv run lab data source-health --no-db
```

## Point-in-time

`what_did_we_know(T)` uses `as_of_knowledge <= T` lockstep with `ingested_at`. A Polygon bar or FRED observation whose exchange/`date` is before T but ingested after T is **unknown** at T. Adversarial tests: `tests/adversarial/test_phase5b_point_in_time.py`.

## Not in this phase

Quant factor library is **5c** ([quant-desk.md](quant-desk.md)). Desk runners (5d), Telegram (5e), Redis, paid data beyond the Polygon env key, `mm_execution` imports, order endpoints, `live.yaml` stay out of ingest.
