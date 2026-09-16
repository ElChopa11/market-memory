# mm-memory

Market Memory: Postgres models, Alembic migrations, object-store pointers, and the point-in-time query API.

## Schema (Phase 1)

- `source` — feed identity and trust tier
- `observation` — claim + provenance envelope (`published_at`, `ingested_at`, `market_time`, `claim_hash`, quality)
- `observation_link` — supports / contradicts / duplicate / updates
- `raw_object` — MinIO/S3 pointer inventory (checksum + key, never secrets)

Point-in-time contract: `what_did_we_know(ts)` is observations with `ingested_at <= ts`. Never use `published_at` alone.

All timestamps are `timestamptz` stored in UTC. Australia/Sydney is an ops timezone only.

**Must not:** execute trades or store private keys.

See [../../docs/runbooks/ingest.md](../../docs/runbooks/ingest.md).
