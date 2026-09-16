# Phase 1 — read-only ingest + Market Memory

Australia/Sydney is the ops timezone for humans. **Every timestamp in Postgres is `timestamptz` UTC.** Never store naive datetimes.

Point-in-time knowledge uses **exactly one watermark**: `what_did_we_know(T)` = observations where `as_of_knowledge <= T`. Writers set `as_of_knowledge = ingested_at` (lab knowledge time); a database check constraint enforces the lockstep. **`published_at` and `market_time` never gate knowledge.**

This runbook does **not** enable live trading, wallets, or signing.

## Prerequisites

- Docker Compose (Postgres 16 + MinIO)
- [uv](https://docs.astral.sh/uv/) and Python 3.12
- Outbound HTTPS to `https://api.hyperliquid.xyz/info` only if you ingest live public data

Copy `.env.example` to `.env` for local DSN/MinIO overrides. **Never put Hyperliquid keys in `.env`.** Phase 1 does not need any.

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

# 4b. One-shot live public info for BTC+ETH perps (last 7 days).
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

Instruments come from `config/instruments/perps.yaml` (BTC, ETH). Settings: `config/ingest.yaml`.

The client **refuses** user-private types (`clearinghouseState`, `userFills`, `openOrders`, …). There is no `hl_trade` module.

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
