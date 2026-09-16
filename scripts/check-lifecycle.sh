#!/usr/bin/env bash
# Definition-of-done gates between research artifact stages.
# Refuses a thesis without intent (and later-stage predecessor gaps).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
if command -v uv >/dev/null 2>&1; then
  exec uv run python scripts/check_lifecycle.py "$@"
fi
exec python3 scripts/check_lifecycle.py "$@"
