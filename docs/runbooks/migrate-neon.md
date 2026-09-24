# Neon migrate (CLI only)

Postgres schema apply for Market Memory. Paper only. No live trading. No Telegram. Object storage is out of scope.

**CLI-only.** There is no GitHub Actions trigger for this command. No `workflow_dispatch`, no `repository_dispatch`, and no `schedule`. A morning-deliver PAT cannot reach `lab migrate`.

**DO NOT RUN** until the Principal says so. On a fresh database the sequence is this command, then `uv run lab history-backfill`, then recurring ingest-persist (a separate change).

## Principal machine

1. Clone or sync this repo on the Principal's machine.
2. Python 3.12.
3. `uv sync --all-packages`.

## Environment

Export **`POSTGRES_DSN` only**. The value is a direct Neon host:

- the hostname ends with `.neon.tech`
- the hostname does not contain `-pooler`
- the query includes `sslmode=require`

`uv run lab migrate` reads that name through `dsn_from_env` in `packages/memory/src/mm_memory/db.py`. **`DATABASE_URL` and `NEON_API_KEY` are not used.** Setting either does not select a database and does not authenticate. This file does not contain example secrets. Do not print the DSN.

If `POSTGRES_DSN` is unset, the CLI falls back to the local compose DSN `postgresql://lab:lab@localhost:5432/market_memory`. That is not Neon. Export `POSTGRES_DSN` before this apply.

## Command

```bash
uv run lab migrate
```

Success prints `migrated to <revision>`. On this branch Alembic head is `0012_heartbeat_if_not_exists` (`packages/memory/src/mm_memory/migrations/versions/0012_heartbeat_if_not_exists.py`, 28 characters). `cmd_migrate` calls `upgrade_head` (Alembic `upgrade` to `head`) and then `current_revision`, which is what that line prints.

Schema created on an empty database, quoted from the revision files and from an offline render through `0010_unconditional_base_rates`: [ops/reports/persistence/2026-09-23-neon-migrate-head-schema.md](../../ops/reports/persistence/2026-09-23-neon-migrate-head-schema.md).

`lab migrate` on this branch has no `--sql` flag. `0011` calls `inspect(bind)`, so a full offline render of head is not available.

## Environment `neon-write`

`neon-write` may exist under repository Settings → Environments. It is **not a gate**. Required reviewers are unavailable on this free private plan, so that Environment cannot hold an approval. The earlier line that this repository is public, and that required reviewers are therefore available, was wrong. This repository is private.

Delete `neon-write` so the name does not imply protection. No workflow in this change references it. A soft `i_mean_it_migrate` input is not a security gate and is not used.
