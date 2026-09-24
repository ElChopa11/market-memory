# Phase 1 — read-only ingest + Market Memory

Australia/Sydney is the ops timezone for humans. **Every timestamp in Postgres is `timestamptz` UTC.** Never store naive datetimes.

Point-in-time knowledge uses **exactly one watermark**: `what_did_we_know(T)` = observations where `as_of_knowledge <= T`. Writers set `as_of_knowledge = ingested_at` (lab knowledge time); a database check constraint enforces the lockstep. **`published_at` and `market_time` never gate knowledge.**

This runbook does **not** enable live trading, wallets, or signing.

## Prerequisites

- Docker Compose (Postgres 16 + MinIO)
- [uv](https://docs.astral.sh/uv/) and Python 3.12
- Outbound HTTPS to `https://api.hyperliquid.xyz/info` only if you ingest live public data

Copy `.env.example` to `.env` for local DSN/MinIO overrides. **Never put Hyperliquid keys, Polygon keys, or FRED keys in `.env` committed to git.** Phase 1 does not need Hyperliquid keys. Phase 5b Polygon and FRED ingest need env keys only when you opt into live HTTP; fixtures dry-run without them.

`config/ingest.yaml` records `licence_verdict` next to each adapter (IMP-034). Sources whose terms prohibit redistribution may be used for internal computation but values must never appear in published artifacts. FRED `--no-db` is **ELIGIBLE only** — `SRC-FRED-MISSING-ENV` is CLOSED on persist run_id `fred-fullstack-20260919-101938-aest` (IMP-022). SEC EDGAR is free (no key); `--no-db` is likewise ELIGIBLE only (IMP-024). Lockups are prospectus formulas, not a flat 180 days.

## Raw object store (fail closed)

Real ingest that stores raw payloads **requires a durable backend**. If MinIO/S3 env is incomplete, ingest **refuses to start** — it does not silently keep bytes in process memory while writing `raw_object` rows.

| Mode | How | Durability |
|---|---|---|
| MinIO/S3 (default) | `MINIO_ENDPOINT` + access/secret keys (or `S3_*` / `AWS_*`) | Durable. Default for `lab ingest` without `--no-objects`. |
| Filesystem | `MM_OBJECT_STORE=filesystem` and `MM_OBJECT_STORE_PATH` | Durable local directory. |
| Disabled | `--no-objects`, `store_raw_objects: false`, or `MM_OBJECT_STORE=none` | Observations persist **without** `raw_object` pointers (honest). |
| In-memory (dev only) | `MM_OBJECT_STORE=memory` | **Not durable.** Bytes vanish on process exit. Opt-in only. |

`NullObjectStore` (empty object key) never inserts `raw_object` rows. Do not treat an in-memory pointer as an audit trail after restart.

## Boot, migrate, ingest, query

```bash
# 1. Database of record + object store
docker compose up -d

# 2. Workspace
uv sync --all-packages

# 3. Schema
uv run lab migrate
# equivalent: uv run python -c "from mm_memory.migrate import upgrade_head; upgrade_head()"

# 4a. Fixture window (offline, what CI uses). `--no-objects` skips raw pointers honestly.
uv run lab ingest --fixture tests/fixtures/hl_window.json --no-objects

# 4a-bis. Phase 5b dry-run (no Postgres, no vendor keys):
uv run lab ingest --fixture tests/fixtures/phase5b/polygon_ohlcv.json --no-db
uv run lab ingest --fixture tests/fixtures/phase5b/hl_structure.json --no-db
uv run lab ingest --fixture tests/fixtures/edgar/cbrs_spcx_lockup.json --no-db
# See docs/runbooks/polygon-hl-structure.md


# 4b. One-shot live public info for locked HL perps (BTC, ETH, UNI, AAVE membership; last 7 days).
#     UNI and AAVE stay on the ingest list as watch-only (no thesis priority).
#     Raw JSON goes to MinIO bucket `market-memory` (checksum + key only).
#     Requires durable MinIO/S3 env (see `.env.example`). Incomplete env fails closed.
uv run lab ingest --window 7d
# equivalent worker:
uv run ingest-once --window 7d

# 5. Point-in-time: what did we know at T?
uv run lab what-did-we-know --at 2026-09-10T00:00:00Z
uv run lab what-did-we-know --at 2026-09-10T00:05:00Z --instrument BTC --metric mid_px
```

`what_did_we_know(T)` returns observations with `as_of_knowledge <= T`. A claim with exchange `published_at`/`market_time` at 00:00 but ingested at 00:05 is **unknown** at 00:00. A snapshot ingested at T is known at T via the knowledge watermark; its `market_time` is **not** the operator window clock.

## What is ingested (read-only `/info`)

| Feed | Info type | Metrics |
|---|---|---|
| Mids | `allMids`, `metaAndAssetCtxs` | `mid_px` |
| Mark / oracle | `metaAndAssetCtxs` | `mark_px`, `oracle_px` |
| Funding | `metaAndAssetCtxs` (spot) + `fundingHistory` (window) | `funding` |
| Open interest | `metaAndAssetCtxs` | `open_interest` (no public OI history) |
| Prices (window) | `candleSnapshot` | `candle_close` |
| Liquidations | `recentTrades` when a `liquidation` object is present | `liquidation` |

Instruments come from `config/instruments/perps.yaml` (BTC, ETH, UNI, AAVE — locked ingest membership in `config/universe.yaml`). ETH, UNI, and AAVE remain ingested as **watch-only** (no thesis-priority membership); BTC is the crypto **in-universe** name. Equities on that universe file ingest via the **Polygon** adapter in Phase 5b (`mm_ingest.equities`; default vendor locked). SMH and XLF are watch-only; NVDA, AVGO, MSFT, META, JPM, XOM are in-universe. Membership is Principal language, not a Quant verdict. Settings: `config/ingest.yaml`.

The Hyperliquid client **refuses** user-private types (`clearinghouseState`, `userFills`, `openOrders`, …). There is no `hl_trade` module. Phase 5b adds public `l2Book` to the allowlist.

## History backfill (one-off, CLI only)

Paper only. No live trading. No Telegram on this path.

**CLI-only.** There is no GitHub Actions trigger. No `workflow_dispatch`, no `repository_dispatch`, and no `schedule`. A morning-deliver PAT cannot reach `lab history-backfill`. `hybrid-sydney-morning.yml` is not part of this path.

**DO NOT RUN** until the Principal says so. On a fresh database the sequence is `uv run lab migrate` first, then this command, then recurring ingest-persist (a separate change). This command does not migrate, does not brief, and does not deliver.

### Principal machine

1. Clone or sync this repo on the Principal's machine.
2. Python 3.12.
3. `uv sync --all-packages`.

### Environment

Names only. This file does not contain example secrets.

| Name | Role |
|---|---|
| `POSTGRES_DSN` | Market Memory Postgres. Direct Neon host (`*.neon.tech`, no `-pooler`, `sslmode=require`). |
| `POLYGON_API_KEY` | Polygon daily bars. |
| `FRED_API_KEY` | Full DGS10 and DGS2. |
| `MINIO_ENDPOINT` | Durable object-store endpoint. `S3_ENDPOINT` is the same slot. |
| `MINIO_ACCESS_KEY` | Object-store access key. `MINIO_ROOT_USER` or `AWS_ACCESS_KEY_ID` is the same slot. |
| `MINIO_SECRET_KEY` | Object-store secret. `MINIO_ROOT_PASSWORD` or `AWS_SECRET_ACCESS_KEY` is the same slot. |

Leave `MINIO_BUCKET` unset. The code default bucket name is `market-memory`. `S3_BUCKET` is the same slot if a name is set. For Cloudflare R2, export `S3_REGION=auto`. `s3_region_from_env` also reads `AWS_DEFAULT_REGION` and `AWS_REGION`. Unset means `us-east-1` (local MinIO). No `TELEGRAM_*`. No Hyperliquid key. Candles use public `/info`.

Missing `POLYGON_API_KEY` or `FRED_API_KEY` prints a refuse line and exits 2 before any HTTP call. An incomplete object store exits 2 the same way. A zero-bar response is a fetch error: the command prints JSON and exits 1 without opening Postgres.

### Command

```bash
uv run lab history-backfill
```

The command prints one JSON object with `"phase": "plan"`, then fetches. When that fetch has no errors it persists and prints a second JSON object with `"phase": "fetch"` and a `persist` object (`created`, `duplicates`, `contradicted`).

Exit 0 when there are no fetch errors and every Hyperliquid coin has at least 60 daily sessions. Exit 1 when the fetch records errors, or when any coin is below that minimum after the commit. Exit 2 when a vendor key or the object store is missing, before HTTP and before Postgres.

This command has no `--no-db` flag and no `--fixture` flag.

### Environment `neon-write`

`neon-write` may exist under repository Settings → Environments. It is **not a gate**. Required reviewers are unavailable on this free private plan, so that Environment cannot hold an approval. The earlier line that this repository is public, and that required reviewers are therefore available, was wrong. This repository is private.

Delete `neon-write` so the name does not imply protection. No workflow in this change references it. A soft `i_mean_it_backfill` input is not a security gate and is not used.

What one successful run requests:

| Source | Endpoint | Window | Approx calls | Rate limit |
|---|---|---|---|---|
| Polygon | `GET /v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}` `adjusted=true` `limit=50000` | 730 calendar days. Tickers are the brief tape slots in `config/briefing/macro.yaml` (`live.polygon.symbols`): SPY, QQQ, UUP, USO. VIX is structural and is not called. | 4 (one GET per ticker; no `next_url` follow) | `config/ingest.yaml` is 5 req/min. Four calls fit in one minute. Not multi-minute. A larger ticker list sleeps via `MinutePacer` because `RateLimitBudget` only refuses. `http_get` still backs off on 429. |
| FRED | `GET /fred/series/observations` | Full series for DGS10 and DGS2 (`limit` omitted; API default 100000). The ingest helper's default `limit=5` is unchanged. The live brief fetch stays `limit=2`. | 2 | 20 req/min in config. One page each. |
| Hyperliquid | `POST /info` `candleSnapshot` interval `1d` | 90 calendar days on enabled perps (BTC, ETH, UNI, AAVE). Open time is field `t` (unix ms). `T` is the close time. | 4 (one POST per coin; under the 500-row page) | 60 req/min. Not multi-minute. |

2s10s is DGS10 minus DGS2. This command does not write a spread row. It does not write Δ1D/Δ5D/Δ20D or z30d columns. Those are later reads over the stored daily closes (`ohlcv_close`, `candle_close`) and the two yield series.

Idempotency is a data-integrity fact, not a reason to keep an Actions trigger. A second run with the same values does not insert a second observation. `claim_hash` is SHA-256 of source, instrument, metric, market time, value, and extras. It does not include `ingested_at`. `ObservationRepository.put_observation` selects on `claim_hash` and otherwise inserts `ON CONFLICT DO NOTHING` on `observation_claim_hash_uidx`. `persist_history_envelopes` skips the raw-object put when that claim already exists. A revised print is a new `claim_hash` plus a `contradicts` link, not an in-place update. History is not deleted.

A run that returns zero bars does not open Postgres. A run that stores HL candles but any coin is under 60 sessions exits 1 after the commit so the gap is visible. The log is the JSON from `lab history-backfill`. It is not a `research_run` row.

## Phase 5b feeds

See [polygon-hl-structure.md](polygon-hl-structure.md): Polygon OHLCV + corporate actions (env `POLYGON_API_KEY`); HL basis / L2 / predicted funding; optional CoinGecko/Binance public spot DQ; FRED + fixture calendar. Missing keys → `unavailable` + `error_class`; never invent.

## Provenance

Each row is an observation envelope: source, source URL/id, `published_at`, `ingested_at`, `market_time`, claim, `claim_hash`, confidence, evidence type, data quality, optional raw object pointer.

- Duplicate claims collapse on unique `claim_hash`.
- Same fact slot (identity without value) with a different value is linked as `contradicts`.
- **Lab capture vs exchange event time:** live snapshot polls (`allMids`, `metaAndAssetCtxs`) set `market_time=NULL` and identity extras `capture_kind=lab_snapshot`. `published_at` / `ingested_at` are lab capture/knowledge time — never the operator window `end`. Historical `fundingHistory.time`, candle `t`, and liquidation `time` stay as real Hyperliquid timestamps in `market_time` / `published_at`.
- Snapshot rows whose lab-capture `published_at` is older than `stale_after_seconds` at ingest time are `stale`.
- Missing fields (e.g. null open interest) are `partial`.
- Historical series are not marked stale merely for being in the past.
- Soft-delete is `data_quality=rejected`; rows are never removed.

Raw payloads in MinIO/S3 (or an explicit filesystem root) store **checksum + object key** on `observation` / `raw_object`. Access keys stay in the environment. Incomplete durable-store config fails before any pointer row is written.

## Compose credentials

Local compose uses `lab`/`lab` for Postgres and `minioadmin` for MinIO. Those are **dev conveniences**, not production secrets, and they are not Hyperliquid keys.

## Source health

Standing Data desk report (not a brief): `uv run lab data source-health`. See [source-health.md](source-health.md).

