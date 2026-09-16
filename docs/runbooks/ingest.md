# Phase 1 — read-only ingest + Market Memory

Australia/Sydney is the ops timezone for humans. **Every timestamp in Postgres is `timestamptz` UTC.** Never store naive datetimes. Point-in-time knowledge uses `ingested_at`, not `published_at` alone.

This runbook does **not** enable live trading, wallets, or signing.

## Prerequisites

- Docker Compose (Postgres 16 + MinIO)
- [uv](https://docs.astral.sh/uv/) and Python 3.12
- Outbound HTTPS to `https://api.hyperliquid.xyz/info` only if you ingest live public data

Copy `.env.example` to `.env` for local DSN/MinIO overrides. **Never put Hyperliquid keys in `.env`.** Phase 1 does not need any.

## Boot, migrate, ingest, query

```bash
# 1. Database of record + object store
docker compose up -d

# 2. Workspace
uv sync --all-packages

# 3. Schema
uv run lab migrate
# equivalent: uv run python -c "from mm_memory.migrate import upgrade_head; upgrade_head()"

# 4a. Fixture window (offline, what CI uses)
uv run lab ingest --fixture tests/fixtures/hl_window.json --no-objects

# 4b. One-shot live public info for BTC+ETH perps (last 7 days)
#     Optional raw JSON goes to MinIO bucket `market-memory` (checksum + key only).
uv run lab ingest --window 7d
# equivalent worker:
uv run ingest-once --window 7d

# 5. Point-in-time: what did we know at T?
uv run lab what-did-we-know --at 2026-09-10T00:00:00Z
uv run lab what-did-we-know --at 2026-09-10T00:05:00Z --instrument BTC --metric mid_px
```

`what_did_we_know(T)` returns observations with `ingested_at <= T`. A claim published at 00:00 but ingested at 00:05 is **unknown** at 00:00.

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
- Snapshot rows older than `stale_after_seconds` at ingest time are `stale`.
- Missing fields (e.g. null open interest) are `partial`.
- Historical series are not marked stale merely for being in the past.
- Soft-delete is `data_quality=rejected`; rows are never removed.

Raw payloads in MinIO/S3 store **checksum + object key** on `observation` / `raw_object`. Access keys stay in the environment.

## Compose credentials

Local compose uses `lab`/`lab` for Postgres and `minioadmin` for MinIO. Those are **dev conveniences**, not production secrets, and they are not Hyperliquid keys.
