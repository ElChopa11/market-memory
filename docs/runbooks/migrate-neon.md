# Neon migrate (dispatch only)

Postgres schema apply for Market Memory. Object storage is out of scope.

**DO NOT RUN** until the Principal says so after the Thursday unattended fire.

## How to dispatch

1. Merge is not required to read this file. The workflow file is `.github/workflows/migrate-neon.yml`.
2. Actions → **migrate-neon** → **Run workflow**.
3. Leave `i_mean_it_migrate` at its default **false** unless the Principal has said to apply.
4. The workflow has no cron. It does not run on push or pull_request.

## Gate

| `i_mean_it_migrate` | What happens |
|---|---|
| false (default) or absent | The skip step prints `SKIP: i_mean_it_migrate is not true. Not connecting to Postgres. POSTGRES_DSN is not read.` and exits 0. Checkout, `uv sync`, and `lab migrate` do not run. |
| true | Checkout, sync, then `uv run lab migrate` (Alembic head). |

`i_mean_it_migrate` is a boolean input, default false. The same pattern as `i_mean_it_deliver`: both the boolean input and the string form `github.event.inputs.i_mean_it_migrate == 'true'` count as affirmed. Anything else skips.

Before connecting, the affirmed job also refuses (exit 1, no migrate) when:

- `mm_memory.migrate.alembic_head()` is not `0012_heartbeat_if_not_exists`
- repository secret `POSTGRES_DSN` is empty (so the CLI cannot fall through to the localhost compose DSN)
- `DATABASE_URL` or `NEON_API_KEY` is set in the job environment
- the host does not end with `.neon.tech`, or the host contains `-pooler`
- `sslmode` is not `require`, `verify-full`, or `verify-ca`

The DSN and host are not printed.

## Secret

Repository secret **`POSTGRES_DSN`** only. Direct Neon host. Include `sslmode=require`. URL-encode the password. Do not put a pooler host in the secret. This workflow does not read `DATABASE_URL` or `NEON_API_KEY`.

## What the command does

`uv run lab migrate` calls `upgrade_head` in `packages/memory/src/mm_memory/migrate.py`, which is Alembic `upgrade` to `head`. On this branch that head is `0012_heartbeat_if_not_exists`.

Schema created on an empty database, quoted from the revision files and from an offline render through `0010_unconditional_base_rates`: [ops/reports/persistence/2026-09-23-neon-migrate-head-schema.md](../../ops/reports/persistence/2026-09-23-neon-migrate-head-schema.md).

`lab migrate` on this branch has no `--sql` flag. `0011` calls `inspect(bind)`, so a full offline render of head is not available. The open prepare PR that adds `--sql-out` also rewrites `0011` and `0012`; its SQL is not the SQL this workflow applies.
