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

## Actions persist (gated; ingest only)

GitHub Actions does not ingest on the Sydney morning cron. `.github/workflows/hybrid-sydney-morning.yml` stays `--no-db` on the heartbeat and on `brief-and-deliver`. Persistence is a separate workflow: `.github/workflows/ingest-persist.yml`.

**DO NOT RUN** until `lab migrate` has been applied to the target database and the Principal has said OK.

| Control | Behaviour |
|---|---|
| Trigger | `workflow_dispatch` only. No `schedule`. No cron. Thursday cannot fire it. |
| Input | `i_mean_it_persist` (boolean, default **false**). The job does not run unless it is true. |
| Command | `uv run lab ingest --window 7d` with **no** `--no-db` and **no** `--no-objects`. |
| Secrets | `POSTGRES_DSN`, `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`. Names only. |
| Bucket | `MINIO_BUCKET` is not set. Code default bucket name is `market-memory`. |
| Region | `S3_REGION=auto` is job env (not a secret) so the R2 client signs with region `auto`. |

`brief-and-deliver` does not `need` this job and still passes `--no-db`, so a failed ingest write cannot fail the Thursday brief or the Principal DM.

`lab ingest --window 7d` (no `--fixture`) is Hyperliquid only (`ingest_from_client`). **(a)** `fundingHistory` and `candleSnapshot` (interval `1h` from `config/ingest.yaml`) use the 7-day window. Timestamp fields are `time` and `t`. Snapshot types (`allMids`, `metaAndAssetCtxs`, `recentTrades`, `l2Book`, `predictedFundings`) are one call-time row; the window does not multiply them. Polygon and FRED are not called, so this command writes no equity history and no FRED series. It does not write Δ1D/Δ5D/Δ20D. Seven days of hourly `candle_close` is not 20 daily sessions, and the brief still passes `--no-db`, so day-one brief Δ columns stay unavailable. Detail is on the ingest-persist PR.

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

Instruments come from `config/instruments/perps.yaml` (BTC, ETH, UNI, AAVE — locked ingest membership in `config/universe.yaml`). ETH, UNI, and AAVE remain ingested as **watch-only** (no thesis-priority membership); BTC is the crypto **in-universe** name. Equities on that universe file have a **Polygon** adapter in Phase 5b (`mm_ingest.equities`; default vendor locked). The live `lab ingest` command without `--fixture` does not call it. SMH and XLF are watch-only; NVDA, AVGO, MSFT, META, JPM, XOM are in-universe. Membership is Principal language, not a Quant verdict. Settings: `config/ingest.yaml`.

The Hyperliquid client **refuses** user-private types (`clearinghouseState`, `userFills`, `openOrders`, …). There is no `hl_trade` module. Phase 5b adds public `l2Book` to the allowlist.

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

