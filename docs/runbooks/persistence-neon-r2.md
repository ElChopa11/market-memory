# Neon + R2 persistence (prepare only)

Paper only. No live trading. No signing. No Telegram send.

**Status:** prepare-only (Principal day order 2026-09-23). This runbook names the env vars, the Actions secrets, and the migrate dry plan. It does **not** put credentials in git, does **not** point the Sydney morning job at Neon, and does **not** close `SRC-OBJECT-STORE`.

ADR: [ADR/0019-grok-clock-actions-execution.md](../../ADR/0019-grok-clock-actions-execution.md). Dry-run packet: [ops/reports/persistence/2026-09-23-neon-r2-prepare.md](../../ops/reports/persistence/2026-09-23-neon-r2-prepare.md).

## Who holds the secrets

Actions is the execution host that writes. The bot box is interactive desk work, not a production host. Neon and R2 values, when Principal supplies them, are **GitHub Actions repository secrets**. They do not go on the box, in `.env`, or on the Grok Secrets card.

| Writer | What it writes | Where | Today |
|---|---|---|---|
| `lab ingest` / `ingest-once` without `--no-db` | Observation rows (`observation`, `raw_object`, `source`) | Postgres via `POSTGRES_DSN` | `persist_envelopes` in `packages/ingest/src/mm_ingest/pipeline.py` calls `ObservationRepository.put_observation` in `packages/memory/src/mm_memory/repository.py`. `apps/ingest-worker` opens `session_scope`. |
| Same path, durable raw bytes | Object bytes | S3-compatible API (`endpoint_url` from env) | `object_store_from_env` in `packages/memory/src/mm_memory/object_store.py`. |
| `lab schedule heartbeat` | Completion JSON | Disk `ops/reports/scheduler/completions/` always | `packages/desks/src/mm_desks/completions.py` (`write_completion`). |
| Same command **without** `--no-db` | Optional `schedule_heartbeat` row | Postgres | `persist_db=not args.no_db` in `apps/lab-cli/src/mm_lab_cli/schedule.py`, then `persist_heartbeat` in `packages/memory/src/mm_memory/heartbeat_repository.py`. Disk stays the primary log if the table write fails. |
| `hybrid-sydney-morning` | Completion JSON committed to the branch | Disk only | `.github/workflows/hybrid-sydney-morning.yml` passes `--no-db`. **This prepare does not edit that file.** |

Grok routines stay a pure clock (degrade-to-dry, `--no-db`). They are not the Neon writer.

## Env names the code reads

Postgres (`packages/memory/src/mm_memory/db.py`, `dsn_from_env`):

| Name | Required | Notes |
|---|---|---|
| `POSTGRES_DSN` | Yes, for any live DB | Only name read. There is no `DATABASE_URL` alias. `postgres://` and `postgresql://` are rewritten to `postgresql+psycopg://`. Query parameters (`sslmode`, `channel_binding`) are kept. Unset falls back to the local compose DSN `postgresql://lab:lab@localhost:5432/market_memory`, which is a connection to localhost, not to Neon. |

Object store (`packages/memory/src/mm_memory/object_store.py`). First name in each row wins.

| Role | Names the code reads | Actions secret? |
|---|---|---|
| Endpoint (`endpoint_url`) | `MINIO_ENDPOINT`, else `S3_ENDPOINT` | Yes. One of them. |
| Bucket | `MINIO_BUCKET`, else `S3_BUCKET` | Yes if the bucket is not the default `market-memory`. |
| Access key | `MINIO_ACCESS_KEY`, else `MINIO_ROOT_USER`, else `AWS_ACCESS_KEY_ID` | Yes. One of them. `MINIO_ROOT_USER` is the local compose alias. |
| Secret key | `MINIO_SECRET_KEY`, else `MINIO_ROOT_PASSWORD`, else `AWS_SECRET_ACCESS_KEY` | Yes. One of them. |
| Region | `S3_REGION`, else `MINIO_REGION`, else `AWS_DEFAULT_REGION` | **No.** Unset defaults to `us-east-1` so local MinIO keeps working. R2 needs `S3_REGION=auto`. |
| Backend switch | `MM_OBJECT_STORE` | No. Default `s3`. |
| Filesystem root | `MM_OBJECT_STORE_PATH` | No. Only when `MM_OBJECT_STORE=filesystem`. |

`lab env preflight` treats object-store env as missing when endpoint, access, and secret are all absent (`packages/common/src/mm_common/env.py`, `object_store_missing_names`). It does not require `S3_REGION` or the bucket (the bucket has a default).

## S3 client is not MinIO-only

`S3ObjectStore` builds a boto3 client with `endpoint_url=` set from the env value above. The host is not hardcoded. Path-style addressing is set explicitly (MinIO and R2 both accept it). Request checksums are `when_required` so boto3 does not attach the default CRC32 trailer that R2 rejects. Region comes from `s3_region_from_env()`.

Incomplete endpoint/access/secret still **fails closed** before any `raw_object` pointer is written.

## Actions secret checklist

Create these GitHub Actions repository secrets when Principal has the values. Do not create them empty. Do not copy them to the box.

| Secret name | Value Principal supplies |
|---|---|
| `POSTGRES_DSN` | Neon **direct** connection string. Hostname must not contain `-pooler`. Include `sslmode=require` (console strings often also include `channel_binding=require`). URL-encode the password. |
| `MINIO_ENDPOINT` | R2 S3 API endpoint, `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`. (`S3_ENDPOINT` is an accepted alias if you set that name instead.) |
| `MINIO_ACCESS_KEY` | R2 access key id. (`AWS_ACCESS_KEY_ID` is an accepted alias.) |
| `MINIO_SECRET_KEY` | R2 secret access key. (`AWS_SECRET_ACCESS_KEY` is an accepted alias.) |
| `MINIO_BUCKET` | R2 bucket name. Omit only if the bucket is exactly `market-memory`. |

Workflow env (not a secret), set only on the job that will write objects:

| Name | Value |
|---|---|
| `S3_REGION` | `auto` |

`hybrid-sydney-morning.yml` does not reference any of these. Leave it that way until a later change explicitly turns writes on. A missing secret must not become a live write that fails mid-job.

Canonical tuple in code: `ACTIONS_SECRET_NAMES` in `packages/memory/src/mm_memory/persistence_env.py`.

## Migrate

```bash
# Offline plan. Does not connect. Ignores POSTGRES_DSN.
uv run lab migrate --sql
uv run lab migrate --sql-out ops/reports/persistence/2026-09-23-migrate-head.sql

# Online apply. Requires a direct Postgres DSN. Refuses sqlite and a Neon pooler host
# before opening a socket. The error text does not include the DSN.
uv run lab migrate
```

`lab migrate` refuses:

- a sqlite DSN (migrations are Postgres `JSONB` / `timestamptz`)
- a host containing `-pooler` or `.pooler.` (Neon transaction pooler breaks DDL)

For a `*.neon.tech` host, the engine sets `prepare_threshold=None` and `pool_pre_ping` (`engine_kwargs_for_dsn` in `packages/memory/src/mm_memory/db.py`). Local compose and CI Postgres are unchanged.

Head revision `0012_heartbeat_if_not_exists` is 28 characters. Alembic `version_num` is `varchar(32)`.

## What breaks first

Order, when a Neon DSN is introduced. Details and the captured sqlite / offline errors are in the [2026-09-23 packet](../../ops/reports/persistence/2026-09-23-neon-r2-prepare.md).

1. **Unset `POSTGRES_DSN`.** The code uses the localhost compose DSN. The first symptom is a connection to `localhost:5432`, not to Neon.
2. **Pooler hostname.** `lab migrate` refuses before connect. Without that guard, the first Neon error is a prepared-statement or session-state failure inside Alembic, not a bad table.
3. **Password characters that are not URL-encoded** (`@`, `#`, `/`) break the URL before authentication.
4. **Schema on real Postgres is not the first break.** Revisions `0001`–`0010` are ordinary DDL (`JSONB`, `timestamptz`) and already apply on Postgres 16 in `.github/workflows/test.yml` (`uv run lab migrate`). Neon is Postgres. SQLite dies earlier: `CompileError` on `observation.payload_json` JSONB, after `source` and `raw_object` exist.
5. **Offline preview used to die at `0011`.** `inspect(bind)` raises `NoInspectionAvailable` on Alembic's mock connection, so a `--sql` dump never reached the heartbeat table. `0011` and `0012` now emit `CREATE TABLE IF NOT EXISTS` via `op.execute`, which renders with no connection. Online idempotence is unchanged.
6. **R2 `put_object` is a separate first break from Postgres.** boto3 1.43 defaults checksums to `when_supported` (R2 rejects the CRC32 trailer) and the old client always signed with `us-east-1`. The client now sends checksums only when required and reads `S3_REGION` (default stays `us-east-1` for MinIO). This was not executed against live R2.
7. **`LISTEN`/`NOTIFY`** (`packages/memory/src/mm_memory/notify.py`, desk mesh) does not work through a Neon transaction pooler. Use the direct endpoint. This is not the migrate path.
8. **Sydney morning stays `--no-db`.** Setting `POSTGRES_DSN` on that workflow is a later change. Completions remain the committed JSON files.

## Blocked on Principal

Only Principal can supply:

1. Neon direct DSN (user, URL-encoded password, direct host, database, `sslmode=require`) for Actions secret `POSTGRES_DSN`.
2. R2 endpoint URL (includes the account id) for `MINIO_ENDPOINT`.
3. R2 access key id for `MINIO_ACCESS_KEY`.
4. R2 secret access key for `MINIO_SECRET_KEY`.
5. R2 bucket name for `MINIO_BUCKET`, if it is not `market-memory`.
6. The decision to set `S3_REGION=auto` and to drop `--no-db` on an Actions job. Not done here.
7. A separate Actions Telegram bot, if Stage 2 send is ever built. Not this runbook. Hive group stays `SEND_FROZEN`.

Until those exist, `SRC-OBJECT-STORE` stays **OPEN**. Do not close it by starting MinIO on the box or by pasting `MINIO_*` onto the box.
