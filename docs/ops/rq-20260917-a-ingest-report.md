# RQ-20260917-A durable ingest report

**Stores:** compose Postgres 16 `market_memory` + MinIO bucket `market-memory` (host `http://localhost:9000`, `minioadmin`).  
**Alembic:** `0005_knowledge_lockstep` (`as_of_knowledge = ingested_at`).  
**Constraint:** public HTTP only. No signing, wallets, `--no-objects`, or `MM_OBJECT_STORE=memory`. Object store backend `s3`; fail-closed check passed before writes.

**Helpers:** `scripts/ops_ingest_durable.py` (HL `/info`, 429 backoff, partial persist); `scripts/ops_ingest_public_docs.py` (Fed HTML + Reuters extract via `ObservationEnvelope` + repository).

**Totals:** **700** observations, **700** MinIO raw pointers. Full inventory: [`rq-20260917-a-observation-ids.tsv`](rq-20260917-a-observation-ids.tsv).

Two HL lab captures: `2026-09-17T00:36:34.348256Z` then `2026-09-17T00:40:19.321319Z` (values moved; later rows linked `contradicts` the earlier same slot). Macro ingest `2026-09-17T00:40:18.318271Z`.

## Latest BTC / ETH lab snapshots (`market_time` NULL)

Premium is in `metaAndAssetCtxs` raw (`premium`), not a first-class metric. `mid_px` stored from `allMids` (claim-hash collapse with ctx mid). ETH funding value was unchanged on the second poll (first-poll row still `ok`).

| observation_id | instrument / metric | claim | source | ingested_at | market_time | data_quality | raw_object |
|---|---|---|---|---|---|---|---|
| `01M2PCXAFASC2V0WCGWR0E8MZT` | BTC / funding | 0.0000103797 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:40:19.321319Z | NULL | contradicted | Y |
| `01M2PCXAFMC3792Y1PQ3H2ACVQ` | BTC / open_interest | 37931.21208 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:40:19.321319Z | NULL | contradicted | Y |
| `01M2PCXAEE4BRXTPMV56SYN56V` | BTC / mark_px | 76446 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:40:19.321319Z | NULL | contradicted | Y |
| `01M2PCXAEY18W6290P82NECSM7` | BTC / oracle_px | 76480 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:40:19.321319Z | NULL | contradicted | Y |
| `01M2PCXACWWCDJRR2GJ20RV7D4` | BTC / mid_px | 76442.5 | hyperliquid.info `allMids` | 2026-09-17T00:40:19.321319Z | NULL | contradicted | Y |
| `01M2PCPEK2ZXFDKPK0TDZZZ5M4` | ETH / funding | 0.0000125 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:36:34.348256Z | NULL | ok | Y |
| `01M2PCXAGW9T101R7NX9AZK9K0` | ETH / open_interest | 982492.2606 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:40:19.321319Z | NULL | contradicted | Y |
| `01M2PCXAG2BA0X80WQZAZYZXJK` | ETH / mark_px | 2425.3 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:40:19.321319Z | NULL | contradicted | Y |
| `01M2PCXAGETNM0FPKGPYCMXHCH` | ETH / oracle_px | 2426 | hyperliquid.info `metaAndAssetCtxs` | 2026-09-17T00:40:19.321319Z | NULL | contradicted | Y |
| `01M2PCXADESR5R4REWZCJR0BQZ` | ETH / mid_px | 2425.25 | hyperliquid.info `allMids` | 2026-09-17T00:40:19.321319Z | NULL | contradicted | Y |

BTC ctx premium on the later OI raw object: **−0.0004837866**. First-poll BTC funding/OI remain queryable: `01M2PCPEHQMYK3DXH440Y3EB9F` / `01M2PCPEJ0E735F0KXKZ385CVT`.

## Macro / news (durable, attributable)

Fed HTML GET 200; raw bytes verified in MinIO (IORB object 79160 bytes contains `3.90 percent`). Calendar dates only on Fed pages → `market_time` is midnight UTC for the stated day (`date_precision=calendar_day`). Reuters origin GET returned **401**; extract stored with `data_quality=partial` (no invented origin HTML).

| observation_id | instrument / metric or claim | source | ingested_at | market_time | data_quality | raw_object |
|---|---|---|---|---|---|---|
| `01M2PCX8ZJZCKC52NQ03PHNZWE` | USD / fed_funds_target_range **3.75–4.00%** effective 2026-09-17 | federalreserve.gov [implementation note](https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a1.htm) | 2026-09-17T00:40:18.318271Z | 2026-09-17T00:00:00Z | ok | Y |
| `01M2PCX9005R4S8GRPQJP96CRP` | USD / iorb **3.90%** effective 2026-09-17 | federalreserve.gov implementation note | 2026-09-17T00:40:18.318271Z | 2026-09-17T00:00:00Z | ok | Y |
| `01M2PCX90C2J9RPG17CSZDTV3Q` | USD / primary_credit **4.00%** effective 2026-09-17 | federalreserve.gov implementation note | 2026-09-17T00:40:18.318271Z | 2026-09-17T00:00:00Z | ok | Y |
| `01M2PCX90PQAP96J62RR6EWQ35` | USD / fomc_ff_hike_bp **25** (12–0) | federalreserve.gov [FOMC statement](https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm) | 2026-09-17T00:40:18.318271Z | 2026-09-16T00:00:00Z | ok | Y |
| `01M2PCX91243QK9V8HCCWQFASY` | USD / further_tightening **one more hike in 2026** | reuters.com [forecasts article](https://www.reuters.com/business/fed-forecasts-see-latest-hike-followed-by-another-before-end-year-2026-09-16/) | 2026-09-17T00:40:18.318271Z | 2026-09-16T18:05:00Z | partial | Y |

## Historical HL series (7d, 1h candles)

| series | n | market_time range | first observation_id | last observation_id |
|---|---|---|---|---|
| BTC `fundingHistory` | 168 | 2026-09-10T01:00:00.046Z → 2026-09-17T00:00:00.048Z | `01M2PCPESM6KRQTQZYZ0ZXS754` | `01M2PCPG68QRWG6TQJHZXFN9RV` |
| BTC `candleSnapshot` 1h | 170 | 2026-09-10T00:00:00Z → 2026-09-17T00:00:00Z | `01M2PCPGCKT2AH2XYQQQ5M38CV` | `01M2PCXDQD10TBA7DZFZ1HPGFJ` (later close `76443`, `contradicted` vs first-poll close) |
| ETH `fundingHistory` | 168 | 2026-09-10T01:00:00.046Z → 2026-09-17T00:00:00.048Z | `01M2PCPJ17RY4PZQHSMGT0BQ2S` | `01M2PCPKEAER3DMP3RQ1K5M6C0` |
| ETH `candleSnapshot` 1h | 170 | 2026-09-10T00:00:00Z → 2026-09-17T00:00:00Z | `01M2PCPKMDR0SPKWQ526KDE1TS` | `01M2PCXHFD0XKS8RRE7R04FNFZ` |

All historical rows have raw_object **Y**. First-poll latest BTC 1h close: `01M2PCPHV5MX4SZ7FMQ0X7QXAQ`.

## Remaining gaps

1. **HL 429:** none. Retry wrapper armed; no backoff sleeps.
2. **Premium metric:** still only in `metaAndAssetCtxs` raw, not its own observation.
3. **Reuters origin HTML:** HTTP **401** from this lab. Observation `01M2PCX91243QK9V8HCCWQFASY` is a lab extract (`partial`), not a durable copy of reuters.com HTML.
4. **Compose `minio-init`:** docker DNS to `minio:9000` timed out; bucket created from host port 9000. Ingest used that path.

## Constraints respected

- HL allowlist only for exchange rows (`allMids`, `metaAndAssetCtxs`, `fundingHistory`, `candleSnapshot`).
- Fed/Reuters: public GET of press HTML / news URL. No wallets, no `hl_trade`.
- `what_did_we_know` remains `as_of_knowledge = ingested_at`. Snapshot `market_time` is NULL.
