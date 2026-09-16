#!/usr/bin/env bash
# Apply Market Memory Alembic migrations (Postgres).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
uv run python -c "from mm_memory.migrate import upgrade_head, current_revision; upgrade_head(); print(current_revision())"
