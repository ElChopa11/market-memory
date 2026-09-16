#!/usr/bin/env bash
# Local Phase 2 bootstrap: Postgres + MinIO, uv workspace, migrate, lifecycle check.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to boot Postgres + MinIO" >&2
  exit 1
fi

echo "Starting Postgres 16 + MinIO..."
docker compose up -d

echo "Waiting for Postgres..."
for i in $(seq 1 30); do
  if docker compose exec -T postgres pg_isready -U lab -d market_memory >/dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Postgres did not become ready" >&2
    exit 1
  fi
  sleep 1
done

echo "Syncing uv workspace (Python 3.12)..."
if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. See https://docs.astral.sh/uv/" >&2
  exit 1
fi
uv sync --all-packages

echo "Applying Market Memory migrations..."
bash "${ROOT}/scripts/migrate.sh"

echo "Running lifecycle checker..."
bash "${ROOT}/scripts/check-lifecycle.sh"

echo "Phase 2 local environment ready."
echo "  Postgres: postgresql://lab:lab@localhost:5432/market_memory"
echo "  MinIO API: http://localhost:9000  console: http://localhost:9001"
echo "  Migrate + ingest: uv run lab migrate && uv run lab ingest --window 7d"
echo "  Thesis from intent: uv run lab thesis new --goal '…' --owner Research"
echo "  Point-in-time: uv run lab what-did-we-know --at <UTC-ISO>"
echo "  Live trading: HARD-GATED"
echo "  Timestamps: timestamptz UTC (ops timezone Australia/Sydney)"
