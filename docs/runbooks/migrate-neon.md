# Neon migrate (dispatch only)

Postgres schema apply for Market Memory. Object storage is out of scope.

**DO NOT RUN** until the Principal says so after the Thursday unattended fire.

## How to dispatch

1. Merge is not required to read this file. The workflow file is `.github/workflows/migrate-neon.yml`.
2. Create Environment `neon-write` first (click path below). A true dispatch before that Environment exists can create it with no reviewers.
3. Actions → **migrate-neon** → **Run workflow**. Select the branch that contains this file.
4. Leave `i_mean_it_migrate` at its default **false** unless the Principal has said to apply.
5. The workflow does not run on push or pull_request. It has no `repository_dispatch` trigger.

## Gate

Two checks. Both must pass before `lab migrate`. The Environment does not replace `i_mean_it_migrate`.

| `i_mean_it_migrate` | Job `skip` | Job `migrate` |
|---|---|---|
| false (default) or absent | Prints `SKIP: i_mean_it_migrate is not true. Not connecting to Postgres. POSTGRES_DSN is not read.` and exits 0. No secrets. No checkout. | Skipped. Its `if` is false, so GitHub does not ask for Environment approval and does not materialise `POSTGRES_DSN`. |
| true | Skipped. | `environment: neon-write`. Status is **Waiting** until a required reviewer approves. Then checkout, sync, the refuse checks, and `uv run lab migrate` (Alembic head). |

`i_mean_it_migrate` is a boolean input, default false. The same pattern as `i_mean_it_deliver`: both the boolean input and the string form `github.event.inputs.i_mean_it_migrate == 'true'` count as affirmed. Anything else takes the skip job.

The two jobs do not `need` each other. On a true dispatch the skip job is skipped; chaining `needs` would also skip the apply job.

## Environment `neon-write` (shared hard gate)

One Environment name for both Neon write workflows: this file's `migrate` job and `history-backfill`'s apply job (`.github/workflows/history-backfill.yml` on draft PR #114). Both write the same database through repository secret `POSTGRES_DSN`. A second name would be a second reviewer list to get wrong. Each run still has its own deployment. Approving a migrate run does not approve a later backfill run.

`neon-write` is a **repository** object under **Settings → Environments**. It is not attached to a pull request, a draft, or a branch. Putting `environment: neon-write` in a workflow file does not create the protection rules.

Draft PR branches **can** reference `environment:` before the workflow is on `main`. Protection applies when that workflow file is dispatched **from that branch**, if the Environment already exists and has required reviewers. Principal can create the Environment **now**, before #111 and #114 merge. Merging first is not required for the gate to exist.

What blocks a leaked `Actions: write` token is the Environment with required reviewers. `i_mean_it_migrate=true` alone is a soft boolean. The token's `workflow_dispatch` must sit **Waiting**, not run.

This change did not create the Environment. On 2026-09-24, `GET /repos/ElChopa11/market-memory/environments` returned an empty list. Required reviewers are set by the repository owner. This agent left that to the Principal click path below.

The repository is public, so required reviewers are available (the private-repository plan limit does not apply).

### Principal click path

Do this before any morning-deliver PAT exists, and before any true dispatch of migrate or backfill.

1. Open [Settings → Environments](https://github.com/ElChopa11/market-memory/settings/environments) on `ElChopa11/market-memory`.
2. **New environment**.
3. Name: `neon-write`. Names are not case-sensitive. Use this spelling so it matches the YAML.
4. **Configure environment**.
5. Select **Required reviewers**. Add GitHub user **ElChopa11** (Principal, repo owner). Up to six reviewers are allowed. Only one must approve. **Save protection rules**.
6. **Deployment branches and tags.** Leave **No restriction**, or use **Selected branches and tags** and add branch rules for `main` and, until those drafts merge, `cursor/neon-migrate-dispatch-5bb5` and `cursor/history-backfill-dispatch-ff1b`. If the dispatched branch is not allowed, the job fails closed and does **not** sit Waiting. Required reviewers are what produce Waiting. A draft-branch dispatch is held only when that branch is allowed to deploy **and** reviewers are required.
7. **Deselect** **Allow administrators to bypass configured protection rules**. That box defaults to allowed. With it cleared, the repo owner cannot force the job past the wait. **Save protection rules**.
8. **Prevent self-review** is a separate choice. If it is checked, the user who triggered the run cannot approve it, even if they are a required reviewer. With only ElChopa11 on the list, a run the Principal triggered (including a leaked PAT acting as the Principal) cannot be approved by the Principal. The job stays Waiting until it is rejected, cancelled, or times out after 30 days, unless a second required reviewer is added. Leave Prevent self-review unchecked if the Principal must approve a run they dispatched. Check it only together with a second reviewer when the goal is that a leaked owner PAT cannot clear its own wait.

Do not add Environment secrets for this gate. The workflow still reads the repository secret `POSTGRES_DSN` on the `migrate` job only. The reviewer rule stops that job before the runner starts, so the secret is not materialised while the job is Waiting or skipped.

A true dispatch while `neon-write` does not exist makes GitHub create an Environment of that name with **no** protection rules and **no** secrets. The job then runs on the soft boolean. A false dispatch does not start the `migrate` job, so it does not take that path. Create and save the reviewers **before** the first true dispatch.

Confirm on the settings page that `neon-write` lists ElChopa11 under Required reviewers. YAML on a draft branch does not show that. The settings page does.

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
