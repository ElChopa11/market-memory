# Neon migrate (one-shot Actions)

Paper only. No live trading. No Telegram. This job applies the Market Memory schema once. History backfill stays shelved (#114). This workflow does not run `lab history-backfill` and does not include #120 prove sets.

Workflow file: `.github/workflows/migrate-neon.yml`

Trigger: `workflow_dispatch` only. No cron. No `repository_dispatch`. Do not call `hybrid-sydney-morning`. No morning PAT.

Secret: the existing Actions secret `POSTGRES_DSN`. No new secret. `DATABASE_URL` and `NEON_API_KEY` are not read. The log must not print the DSN. The job refuses unless the host ends with `.neon.tech`, does not contain `-pooler`, and sets `sslmode=require` (or `verify-full` or `verify-ca`).

Command: `uv run lab migrate` (Alembic `upgrade` to `head`, then print `migrated to <revision>`). Local compose migrate in [ingest.md](ingest.md) is a different path.

## Same sitting

1. Merge the PR that adds this workflow to `main`.
2. GitHub → Actions → **migrate-neon** → **Run workflow**. Branch: `main`.
3. Confirm input `confirm`: paste exactly `i_mean_it_migrate`. Any other value exits non-zero and does not connect.
4. A green run prints `alembic_head=<revision>`, `migrated to <revision>`, and `SUCCESS: lab migrate exited 0`. A red run is a failed apply. On this tree the head is `0012_heartbeat_if_not_exists`.
5. In the Neon SQL editor, `SELECT version_num FROM alembic_version;` matches that revision.
6. Delete `.github/workflows/migrate-neon.yml` in a follow-up commit or revert this change in the same sitting. Leave no workflow a token can dispatch.
