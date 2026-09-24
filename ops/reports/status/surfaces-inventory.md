# Surfaces inventory

as_of: 2026-09-24 (Principal addendum on the thin `repository_dispatch` draft)

rule: names and paths only. This file holds no secret values. A row says where a standing credential lives and what actually constrains it.

No surfaces inventory was present under `ops/reports/`, `docs/runbooks/`, or `config/knowledge/` before this seed.

House lesson: [config/knowledge/house-lessons.md](../../../config/knowledge/house-lessons.md) (2026-09-24). Caller contract: [docs/runbooks/scheduler.md](../../../docs/runbooks/scheduler.md).

## `github-sm-dispatch.pat`

| Field | Record |
|---|---|
| Path | `/home/box/agent-data/infra/github-sm-dispatch.pat` (name only) |
| Host | Standing credential on the shared multi-agent box (browser sessions, screenshot history, six agents) |
| Enforcement | File mode `0600` plus an instruction. Not capability isolation. A deliberate same-user read is still possible. |
| Blast radius | One `repository_dispatch` event type: `sydney-morning-deliver` (thin morning deliver). That single trigger is why the standing file is tolerable. Migrate and backfill are CLI-only and have no token-reachable Actions trigger. |
| Intended consumer | Grok Sydney Morning routine only. No other desk, routine, or process may read it. |
| Rotation | Any one of these rotates the PAT immediately: any box incident; any screenshot of a terminal that might show the path or the value; any agent found reading paths under `agent-data/`. |
| Status | Principal writes the file when path (a) is merged and ready. The file must not exist until then. |

## Other standing surfaces (names only)

Pointers. This seed does not audit every host.

| Surface | Name only | Where the name is recorded |
|---|---|---|
| Box delivery token | `/home/box/agent-data/delivery/telegram.env` | [docs/runbooks/telegram.md](../../../docs/runbooks/telegram.md). Same class as this PAT: mode `0600` on the shared box is not capability isolation (house lesson 2026-09-19, Grok Secrets card). Isolation remains IMP-044 backlog. |
| Actions secrets read by the Sydney morning workflow | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID_PRINCIPAL_DM`, `POLYGON_API_KEY`, `FRED_API_KEY` | `.github/workflows/hybrid-sydney-morning.yml`. GitHub Actions secret store, not a box file. This inventory does not record whether a value is stored. |
| Neon DSN in Actions | No secret name is mapped in `.github/workflows/` on this branch | ADR 0019 and the 2026-09-22 house lesson record the destination as an Actions secret, not a box file. Wiring is parked. This row does not invent a name. CI `POSTGRES_DSN` in `.github/workflows/test.yml` is the local lab database, not Neon. |
