"""Laptop runbook for Neon migrate and history backfill. No Actions trigger."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "docs" / "runbooks" / "cli-operations.md"
WORKFLOWS = ROOT / ".github" / "workflows"


def _probes() -> list[str]:
    text = RUNBOOK.read_text(encoding="utf-8")
    chunks: list[str] = []
    marker = "uv run python - <<'PY'\n"
    rest = text
    while marker in rest:
        rest = rest.split(marker, 1)[1]
        body, rest = rest.split("\nPY\n", 1)
        chunks.append(body)
    return chunks


def test_runbook_probe_is_valid_python() -> None:
    probes = _probes()
    assert len(probes) == 1
    ast.parse(probes[0])
    probe = probes[0]
    assert "SELECT version_num FROM alembic_version" in probe
    assert "max(o.as_of_knowledge) AS max_as_of_knowledge" in probe
    assert "max(o.market_time) AS max_market_time" in probe
    assert "count(*)::int AS rows" in probe
    assert "('polygon', 'ohlcv_close')" in probe
    assert "('fred', 'fred_observation')" in probe
    assert "('hyperliquid.info', 'candle_close')" in probe
    assert "0012_heartbeat_if_not_exists" in probe
    assert "rows not proven" in probe
    for series in ("SPY", "QQQ", "UUP", "USO", "US10Y", "US2Y", "BTC", "ETH", "UNI", "AAVE"):
        assert series in probe


def test_runbook_commands_match_cli() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "uv run lab migrate" in text
    assert "uv run lab history-backfill" in text
    assert "migrated to 0012_heartbeat_if_not_exists" in text
    assert '"phase": "plan"' in text
    assert '"phase": "fetch"' in text
    assert "history-backfill refused: missing POLYGON_API_KEY, FRED_API_KEY" in text
    assert "Connection refused" in text
    assert "POSTGRES_DSN" in text
    assert "DATABASE_URL" in text
    assert "NEON_API_KEY" in text
    assert ".neon.tech" in text
    assert "-pooler" in text
    assert "sslmode=require" in text
    assert "claim_hash" in text
    assert "ON CONFLICT DO NOTHING" in text
    assert "safe to re-run" in text
    assert "Paper only" in text
    assert "No `workflow_dispatch`" in text
    assert "no `repository_dispatch`" in text
    assert "no `schedule`" in text
    assert "not a gate" in text
    assert "Delete `neon-write`" in text
    assert "Example probe stdout (not a live Neon query)" in text
    assert "Example fetch success" in text
    assert "not a live database apply" in text
    # No credential material. The documented local fallback is the compose DSN.
    assert "postgresql://" not in text.replace(
        "postgresql://lab:lab@localhost:5432/market_memory", ""
    )
    assert "postgres://" not in text
    assert "AKIA" not in text
    assert "npm_" not in text


def test_no_dispatch_workflow_for_migrate_or_backfill() -> None:
    assert not (WORKFLOWS / "migrate-neon.yml").exists()
    assert not (WORKFLOWS / "history-backfill.yml").exists()
    for path in WORKFLOWS.glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        assert "environment: neon-write" not in text
        assert "i_mean_it_migrate" not in text
        assert "i_mean_it_backfill" not in text
        assert "history-backfill" not in text
        assert "lab history-backfill" not in text
