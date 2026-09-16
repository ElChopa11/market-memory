#!/usr/bin/env bash
# Local Phase 0 bootstrap: Postgres + MinIO, uv workspace, lifecycle check.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to boot Postgres + MinIO" >&2
  exit 1
fi

echo "Starting Postgres 16 + MinIO..."
docker compose up -d

echo "Syncing uv workspace (Python 3.12)..."
if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. See https://docs.astral.sh/uv/" >&2
  exit 1
fi
uv sync --all-packages

echo "Running lifecycle checker..."
bash "${ROOT}/scripts/check-lifecycle.sh"

echo "Phase 0 local environment ready."
echo "  Postgres: postgresql://lab:lab@localhost:5432/market_memory"
echo "  MinIO API: http://localhost:9000  console: http://localhost:9001"
echo "  Live trading: HARD-GATED"
