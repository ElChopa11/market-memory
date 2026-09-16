# Integration tests

Postgres-backed migrate + fixture ingest + `what_did_we_know` replay + Market Pulse brief index.

Requires `POSTGRES_DSN` (CI provides a Postgres 16 service). Tests skip if Postgres is unreachable.

```bash
docker compose up -d
export POSTGRES_DSN=postgresql://lab:lab@localhost:5432/market_memory
uv run pytest tests/integration
```
