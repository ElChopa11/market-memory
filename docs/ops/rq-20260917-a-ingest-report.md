# RQ-20260917-A durable ingest report

**Run:** 2026-09-17T00:36:34.348256Z (lab knowledge / `ingested_at`)  
**Git:** `main` after merged PR #6 (`c625ada`, fail-closed raw store + `0005_knowledge_lockstep`)  
**Stores:** compose Postgres 16 `market_memory` (user `lab`) + MinIO bucket `market-memory` (`minioadmin`, host `http://localhost:9000`)  
**Alembic:** `0005_knowledge_lockstep` applied (`observation_as_of_knowledge_eq_ingested_at` present)  
**Ingest:** public Hyperliquid `/info` only. No signing, wallets, `--no-objects`, or `MM_OBJECT_STORE=memory`. Object store backend `s3`. Fail-closed config check passed before any `raw_object` write.

Helper: `uv run python scripts/ops_ingest_durable.py` (429/5xx exponential backoff; persist snapshots before historical series so a later 429 cannot drop already-written rows). Stock `lab ingest --window 7d` is the same allowlist.

**Window (historical series):** 2026-09-10T00:36:34Z → 2026-09-17T00:36:34Z. Candle interval `1h`.

**Totals:** 684 observations, 684 MinIO raw objects (every row has a pointer). Source `hyperliquid.info` (`https://api.hyperliquid.xyz/info`).

## Snapshot observations (`market_time` NULL = `lab_snapshot`)

Premium is **not** a first-class metric in Phase 1 normalize. It is present on `metaAndAssetCtxs` asset ctx (`premium`) and stored in the raw object of those rows. BTC premium **−0.0004052764**; ETH premium **−0.0003296251**. `mid_px` rows collapsed onto `allMids` (same claim identity as `metaAndAssetCtxs` mid); `midPx` remains in the `metaAndAssetCtxs` raw payload on funding / OI / mark / oracle rows.

| observation_id | instrument / metric | claim | source | ingested_at | market_time | data_quality | raw_object |
|---|---|---|---|---|---|---|---|
| `01M2PCPEHQMYK3DXH440Y3EB9F` | BTC / funding | 0.0000101846 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:36:34.348256Z | NULL | ok | Y |
| `01M2PCPEJ0E735F0KXKZ385CVT` | BTC / open_interest | 37944.38514 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:36:34.348256Z | NULL | ok | Y |
| `01M2PCPEH4JWB92GVDA8KM1M4R` | BTC / mark_px | 76459 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:36:34.348256Z | NULL | ok | Y |
| `01M2PCPEHE07ZRBX0CG6NTKNWZ` | BTC / oracle_px | 76491 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:36:34.348256Z | NULL | ok | Y |
| `01M2PCPEG32A3XBJVTN4HYHNK7` | BTC / mid_px | 76459.5 | hyperliquid.info `allMids` | 2026-09-17T00:36:34.348256Z | NULL | ok | Y |
| `01M2PCPEK2ZXFDKPK0TDZZZ5M4` | ETH / funding | 0.0000125 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:36:34.348256Z | NULL | ok | Y |
| `01M2PCPEKBG9ER5VGR28PQRY11` | ETH / open_interest | 982651.991 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:36:34.348256Z | NULL | ok | Y |
| `01M2PCPEJJDY9CCFJ8BZ6YWFAF` | ETH / mark_px | 2426.3 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:36:34.348256Z | NULL | ok | Y |
| `01M2PCPEJVD2FFFPCRX0M4Z5BV` | ETH / oracle_px | 2427 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:36:34.348256Z | NULL | ok | Y |
| `01M2PCPEGH9GHX0VQER7RNQJSW` | ETH / mid_px | 2426.15 | hyperliquid.info `allMids` | 2026-09-17T00:36:34.348256Z | NULL | ok | Y |

BTC snapshot raw object (verified GET from MinIO): `raw/hyperliquid.info/2026/09/17/BTC/open_interest/3799f2a8d01843f5.json` contains `funding`, `openInterest`, `premium`, `midPx`, `markPx`, `oraclePx`.

## Historical series (exchange `market_time`)

All `data_quality=ok`, raw_object **Y**, source `hyperliquid.info`. `ingested_at` for these rows is the same lab capture as the snapshots.

| series | n | market_time range | first observation_id | last observation_id |
|---|---|---|---|---|
| BTC `fundingHistory` | 168 | 2026-09-10T01:00:00.046Z → 2026-09-17T00:00:00.048Z | `01M2PCPESM6KRQTQZYZ0ZXS754` | `01M2PCPG68QRWG6TQJHZXFN9RV` |
| BTC `candleSnapshot` 1h `candle_close` | 169 | 2026-09-10T00:00:00Z → 2026-09-17T00:00:00Z | `01M2PCPGCKT2AH2XYQQQ5M38CV` | `01M2PCPHV5MX4SZ7FMQ0X7QXAQ` |
| ETH `fundingHistory` | 168 | 2026-09-10T01:00:00.046Z → 2026-09-17T00:00:00.048Z | `01M2PCPJ17RY4PZQHSMGT0BQ2S` | `01M2PCPKEAER3DMP3RQ1K5M6C0` |
| ETH `candleSnapshot` 1h `candle_close` | 169 | 2026-09-10T00:00:00Z → 2026-09-17T00:00:00Z | `01M2PCPKMDR0SPKWQ526KDE1TS` | `01M2PCPN3K7RDCPSQRBV0R5A8A` |

Latest BTC hourly funding (claim `0.0000125`): `01M2PCPG68QRWG6TQJHZXFN9RV`. Latest BTC 1h close (`76454`): `01M2PCPHV5MX4SZ7FMQ0X7QXAQ`.

Full ULID inventory is in Postgres (`SELECT id, instrument, metric, market_time FROM observation ORDER BY instrument, metric, market_time NULLS FIRST`). Not inlined here (674 historical rows).

## Remaining gaps

1. **HL 429:** none this run. Retry wrapper was armed; no backoff sleeps were required.
2. **Premium as its own observation metric:** not emitted by `normalize_asset_snapshot`. Value is only in `metaAndAssetCtxs` raw (see snapshot table). Do not treat that as a missing BTC OI/funding row.
3. **Macro / FOMC / news observations:** **not ingested. No observation_ids.** Market Memory ingest only normalizes Hyperliquid `/info` fixtures or live polls. Phase 3 briefing fetchers (FRED/Stooq) write brief assets, not `observation` rows. There is no documented manual/news insert CLI. `FRED_API_KEY` was unset. Attributable public sources that were **not** written to memory:
   - Fed funds target **3.75–4.00%**, IORB **3.90%**, primary credit **4.00%**, effective 2026-09-17 — [Fed implementation note, 2026-09-16](https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a1.htm)
   - Further-tightening / another hike this year — [Reuters, 2026-09-16](https://www.reuters.com/business/fed-forecasts-see-latest-hike-followed-by-another-before-end-year-2026-09-16/)
4. **Compose `minio-init`:** container-to-container probe to `minio:9000` timed out in this environment. Bucket `market-memory` was created from the host against published port 9000; ingest used that path. Postgres healthcheck was green.

## Constraints respected

- Public `/info` allowlist only (`allMids`, `metaAndAssetCtxs`, `fundingHistory`, `candleSnapshot`).
- No `hl_trade`, signing, wallets, or live trading.
- `what_did_we_know` watermark remains `as_of_knowledge = ingested_at`. Snapshot `market_time` is NULL.
