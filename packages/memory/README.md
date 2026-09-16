# mm-memory

Market Memory: Postgres models, Alembic migrations, object-store pointers, and the point-in-time query API.

## Schema (Phase 1–4)

- `source` — feed identity and trust tier
- `observation` — claim + provenance envelope (`published_at`, `ingested_at`, `market_time`, `as_of_knowledge`, `claim_hash`, quality)
- `observation_link` — supports / contradicts / duplicate / updates
- `raw_object` — MinIO/S3 (or filesystem) pointer inventory (checksum + key, never secrets). Empty keys are not stored.
- `thesis` — hypothesis index (`slug`, `status`, `artifact_git_path`, `artifact_content_hash`)
- `thesis_evidence` — thesis ↔ observation id (`supports` / `opposes` / `context`)
- `skeptic_review` — independent verdict (`pass` / `revise` / `reject`) plus artifact hash
- `brief` — optional Market Pulse index
- `research_run` — backtest/scan/manual runs (`params_hash`, artifact paths)
- `paper_trade` — shadow ledger (invalidation + max loss required)

Git artifacts under `research/` remain the human-review source. Postgres stores indexes and hashes. Rejected theses are **not** deleted.

Git artifacts under `research/` remain the human-review source. Postgres stores indexes and hashes. Rejected theses are **not** deleted.

Point-in-time contract: `what_did_we_know(ts)` is observations with `as_of_knowledge <= ts`. Writers set `as_of_knowledge = ingested_at` (enforced by check constraint `observation_as_of_knowledge_eq_ingested_at`). **`published_at` and `market_time` never gate knowledge.** Snapshot polls use `market_time=NULL` and `capture_kind=lab_snapshot`; they are known at T via the knowledge watermark, not via a fake exchange clock. Query theses with `list_theses` (rejected included unless you filter `status`).

All timestamps are `timestamptz` stored in UTC. Australia/Sydney is an ops timezone only.

**Must not:** execute trades or store private keys.

See [../../docs/runbooks/ingest.md](../../docs/runbooks/ingest.md).
