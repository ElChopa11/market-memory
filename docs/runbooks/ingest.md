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

## History backfill (one-off, dispatch-gated)

**DO NOT RUN** until the Principal says so after the Thursday unattended fire. Sequence is `lab migrate` on the fresh database, then this job, then recurring ingest-persist. This command does not migrate, does not brief, and does not deliver.

Workflow: `.github/workflows/history-backfill.yml`. Trigger is `workflow_dispatch` only. There is no `schedule` and no cron. There is no `repository_dispatch` trigger. `hybrid-sydney-morning.yml` is not part of this path. Its heartbeat and `brief-and-deliver` stay `--no-db`.

| Control | Behaviour |
|---|---|
| Input | `i_mean_it_backfill` (boolean, default **false**). |
| False | Job `skip` prints `SKIP` and exits 0. No Environment, no checkout, no secrets, no Postgres, no Polygon, no FRED, no Hyperliquid. Job `history-backfill` is skipped and does not wait for approval. |
| True | Job `history-backfill` has `environment: neon-write`. It stays **Waiting** until a required reviewer approves. Then `uv run lab history-backfill` with **no** `--no-db` and **no** `--fixture`. |
| Secrets | On the true job only: `POSTGRES_DSN`, `POLYGON_API_KEY`, `FRED_API_KEY`, `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`. Names only. |
| Bucket | `MINIO_BUCKET` is not set. Code default bucket name is `market-memory`. |
| Region | `S3_REGION=auto` is job env (not a secret). |

The two jobs do not depend on each other. On a true dispatch the skip job is skipped; chaining them would also skip the apply.

`i_mean_it_backfill` stays. Environment approval does not replace it. Inside the approved job the script still refuses (exit 1) when the input is not the string `true`, when a required secret is empty, when `MINIO_BUCKET` is set, or when `S3_REGION` is not `auto`.

### Environment `neon-write` (shared hard gate)

One Environment name for both Neon write workflows: this file's `history-backfill` job and `migrate-neon`'s `migrate` job (`.github/workflows/migrate-neon.yml` on draft PR #111). Both write the same database through repository secret `POSTGRES_DSN`. Backfill also calls Polygon, FRED, and Hyperliquid. A second name would be a second reviewer list to get wrong. Each run still has its own deployment. Approving a migrate run does not approve a later backfill run.

`neon-write` is a **repository** object under **Settings → Environments**. It is not attached to a pull request, a draft, or a branch. Putting `environment: neon-write` in a workflow file does not create the protection rules.

Draft PR branches **can** reference `environment:` before the workflow is on `main`. Protection applies when that workflow file is dispatched **from that branch**, if the Environment already exists and has required reviewers. Principal can create the Environment **now**, before #111 and #114 merge. Merging first is not required for the gate to exist.

What blocks a leaked `Actions: write` token is the Environment with required reviewers. `i_mean_it_backfill=true` alone is a soft boolean. The token's `workflow_dispatch` must sit **Waiting**, not run.

This change did not create the Environment. On 2026-09-24, `GET /repos/ElChopa11/market-memory/environments` returned an empty list. Required reviewers are set by the repository owner. This agent left that to the Principal click path below.

The repository is public, so required reviewers are available (the private-repository plan limit does not apply).

#### Principal click path

Do this before any morning-deliver PAT exists, and before any true dispatch of migrate or backfill.

1. Open [Settings → Environments](https://github.com/ElChopa11/market-memory/settings/environments) on `ElChopa11/market-memory`.
2. **New environment**.
3. Name: `neon-write`. Names are not case-sensitive. Use this spelling so it matches the YAML.
4. **Configure environment**.
5. Select **Required reviewers**. Add GitHub user **ElChopa11** (Principal, repo owner). Up to six reviewers are allowed. Only one must approve. **Save protection rules**.
6. **Deployment branches and tags.** Leave **No restriction**, or use **Selected branches and tags** and add branch rules for `main` and, until those drafts merge, `cursor/neon-migrate-dispatch-5bb5` and `cursor/history-backfill-dispatch-ff1b`. If the dispatched branch is not allowed, the job fails closed and does **not** sit Waiting. Required reviewers are what produce Waiting. A draft-branch dispatch is held only when that branch is allowed to deploy **and** reviewers are required.
7. **Deselect** **Allow administrators to bypass configured protection rules**. That box defaults to allowed. With it cleared, the repo owner cannot force the job past the wait. **Save protection rules**.
8. **Prevent self-review** is a separate choice. If it is checked, the user who triggered the run cannot approve it, even if they are a required reviewer. With only ElChopa11 on the list, a run the Principal triggered (including a leaked PAT acting as the Principal) cannot be approved by the Principal. The job stays Waiting until it is rejected, cancelled, or times out after 30 days, unless a second required reviewer is added. Leave Prevent self-review unchecked if the Principal must approve a run they dispatched. Check it only together with a second reviewer when the goal is that a leaked owner PAT cannot clear its own wait.

Do not add Environment secrets for this gate. The workflow still reads repository secrets on the `history-backfill` job only. The reviewer rule stops that job before the runner starts, so those secrets are not materialised while the job is Waiting or skipped.

A true dispatch while `neon-write` does not exist makes GitHub create an Environment of that name with **no** protection rules and **no** secrets. The job then runs on the soft boolean. A false dispatch does not start the `history-backfill` job, so it does not take that path. Create and save the reviewers **before** the first true dispatch.

Confirm on the settings page that `neon-write` lists ElChopa11 under Required reviewers. YAML on a draft branch does not show that. The settings page does. The same click path is in `docs/runbooks/migrate-neon.md` on draft PR #111. Create the Environment once.

What one successful run requests:

| Source | Endpoint | Window | Approx calls | Rate limit |
|---|---|---|---|---|
| Polygon | `GET /v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}` `adjusted=true` `limit=50000` | 730 calendar days. Tickers are the brief tape slots in `config/briefing/macro.yaml` (`live.polygon.symbols`): SPY, QQQ, UUP, USO. VIX is structural and is not called. | 4 (one GET per ticker; no `next_url` follow) | `config/ingest.yaml` is 5 req/min. Four calls fit in one minute. Not multi-minute. A larger ticker list sleeps via `MinutePacer` because `RateLimitBudget` only refuses. `http_get` still backs off on 429. |
| FRED | `GET /fred/series/observations` | Full series for DGS10 and DGS2 (`limit` omitted; API default 100000). The ingest helper's default `limit=5` is unchanged. The live brief fetch stays `limit=2`. | 2 | 20 req/min in config. One page each. |
| Hyperliquid | `POST /info` `candleSnapshot` interval `1d` | 90 calendar days on enabled perps (BTC, ETH, UNI, AAVE). Open time is field `t` (unix ms). `T` is the close time. | 4 (one POST per coin; under the 500-row page) | 60 req/min. Not multi-minute. |

2s10s is DGS10 minus DGS2. This job does not write a spread row. It does not write Δ1D/Δ5D/Δ20D or z30d columns. Those are later reads over the stored daily closes (`ohlcv_close`, `candle_close`) and the two yield series.

Idempotency: a second dispatch with the same values does not insert a second observation. `ObservationRepository.put_observation` dedupes on `claim_hash` (`observation_claim_hash_uidx`). `claim_hash` is source, instrument, metric, market time, value, and extras. It does not include `ingested_at`. This command also skips the raw-object put when that claim already exists. A revised print is a new `claim_hash` plus a `contradicts` link, not an overwrite.

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

