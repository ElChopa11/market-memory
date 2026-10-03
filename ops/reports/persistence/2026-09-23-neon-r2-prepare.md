# Neon + R2 prepare — migrate dry run (2026-09-23)

Paper only. No credentials were present or written. No call to Neon. No call to R2. `.github/workflows/hybrid-sydney-morning.yml` was not modified.

Runbook: [docs/runbooks/persistence-neon-r2.md](../../../docs/runbooks/persistence-neon-r2.md).

## Commands

Offline plan (this environment has no Postgres server, so online `lab migrate` was not applied here). CI still applies the same revisions online: `.github/workflows/test.yml` runs `uv run lab migrate` against Postgres 16.

```bash
uv run lab migrate --sql-out ops/reports/persistence/2026-09-23-migrate-head.sql
```

Result:

- Exit 0.
- Message: `wrote offline upgrade SQL to ops/reports/persistence/2026-09-23-migrate-head.sql (497 lines; no connection; POSTGRES_DSN not read)`.
- Head revision: `0012_heartbeat_if_not_exists` (28 characters; Alembic `version_num` is `varchar(32)`).
- SQL is 497 lines. It starts with `BEGIN;` / `CREATE TABLE alembic_version` and ends with `UPDATE alembic_version SET version_num='0012_heartbeat_if_not_exists' ...` then `COMMIT;`.
- The file contains `JSONB` and `schedule_heartbeat`. It does not contain a DSN, a password, or the offline placeholder host `192.0.2.1`.
- A unit test asserts the committed file equals `render_upgrade_sql()` so the packet cannot drift from the renderer.

Full SQL: [2026-09-23-migrate-head.sql](2026-09-23-migrate-head.sql).

## What the dry run found

### SQLite is not a stand-in (captured before the refusal guard)

`upgrade_head("sqlite:////tmp/mm-sqlite-dry/market_memory.db")` on the pre-change code:

- Exception: `sqlalchemy.exc.CompileError`
- Message: `(in table 'observation', column 'payload_json'): Compiler <sqlalchemy.dialects.sqlite.base.SQLiteTypeCompiler ...> can't render element of type JSONB`
- `0001_phase1` creates `source` and `raw_object`, then fails on `observation.payload_json`.
- So the first schema break on sqlite is JSONB in revision `0001`, not a later heartbeat change.

`lab migrate` now refuses a sqlite scheme before that compile, and tells the operator to use `--sql`. The refusal does not open a database.

### Offline `--sql` used to stop at revision 0011

Before this change, `command.upgrade(..., sql=True)` rendered `0001`–`0010` and then raised:

`sqlalchemy.exc.NoInspectionAvailable: No inspection system is available for object of type <class 'sqlalchemy.engine.mock.MockConnection'>`

at `0011_schedule_heartbeat.py` `inspector = inspect(bind)`. That was the first failure of a dry plan. `0011` and `0012` now use `op.execute` with `CREATE TABLE IF NOT EXISTS` (same columns as before). Offline render reaches head. Online `IF NOT EXISTS` still covers a retry after a partial apply. `0012` still replaces the status check so `wrong_anchor` is allowed in the CHECK (the product path does not write that status).

### When a real Neon Postgres DSN appears

1. If `POSTGRES_DSN` is unset, `dsn_from_env` in `packages/memory/src/mm_memory/db.py` uses `postgresql://lab:lab@localhost:5432/market_memory`. The first symptom is localhost, not Neon.
2. A Neon **pooler** host (`-pooler` in the hostname) is refused before connect. DDL on the transaction pooler fails on prepared statements / session state; that would otherwise be the first error after TCP auth succeeds.
3. A password that is not URL-encoded breaks the URL before authentication.
4. `sslmode=require` and `channel_binding=require` pass through `normalize_dsn`. psycopg in this workspace is 3.3, which accepts `channel_binding`.
5. Revisions `0001`–`0010` are ordinary Postgres DDL already applied by CI. They are not the first Neon break. Neon is Postgres.
6. `*.neon.tech` engines set `prepare_threshold=None` and `pool_pre_ping`. Localhost CI engines do not.
7. R2 is independent of migrate. The first object write against R2 would have been boto3's default checksum trailer and region `us-east-1`. The client now takes `endpoint_url` from `MINIO_ENDPOINT` or `S3_ENDPOINT`, region from `S3_REGION` (default `us-east-1`), path-style addressing, and checksums `when_required`. Not executed against live R2.

## Not done

- No Actions secrets created.
- No edit to `.github/workflows/hybrid-sydney-morning.yml` (cron, guard, or `--no-db`).
- No Telegram / Stage 2 send.
- `SRC-OBJECT-STORE` stays OPEN.
