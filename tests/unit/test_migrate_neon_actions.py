"""CLI-only Neon migrate. No Actions trigger. Does not connect."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
RUNBOOK = ROOT / "docs" / "runbooks" / "migrate-neon.md"
HYBRID = WORKFLOWS / "hybrid-sydney-morning.yml"
SCHEMA = ROOT / "ops" / "reports" / "persistence" / "2026-09-23-neon-migrate-head-schema.md"
SQL = ROOT / "ops" / "reports" / "persistence" / "2026-09-23-migrate-through-0010.sql"
REV_0011 = (
    ROOT
    / "packages"
    / "memory"
    / "src"
    / "mm_memory"
    / "migrations"
    / "versions"
    / "0011_schedule_heartbeat.py"
)
REV_0012 = (
    ROOT
    / "packages"
    / "memory"
    / "src"
    / "mm_memory"
    / "migrations"
    / "versions"
    / "0012_heartbeat_if_not_exists.py"
)


def test_migrate_neon_has_no_actions_workflow() -> None:
    assert not (WORKFLOWS / "migrate-neon.yml").exists()
    for path in WORKFLOWS.glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        assert "i_mean_it_migrate" not in text
        assert "name: migrate-neon" not in text
        assert "environment: neon-write" not in text


def test_migrate_runbook_is_cli_only() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "CLI-only" in text
    assert "uv run lab migrate" in text
    assert "migrated to" in text
    assert "0012_heartbeat_if_not_exists" in text
    assert "POSTGRES_DSN" in text
    assert "DATABASE_URL" in text
    assert "NEON_API_KEY" in text
    assert ".neon.tech" in text
    assert "-pooler" in text
    assert "sslmode=require" in text
    assert "morning-deliver PAT" in text
    assert "not a gate" in text
    assert "Delete `neon-write`" in text
    assert "This repository is private" in text
    assert "The repository is public" not in text
    assert "workflow_dispatch" in text
    assert "no `workflow_dispatch`" in text
    assert "repository_dispatch" in text
    assert "no `repository_dispatch`" in text
    assert "schedule" in text
    assert "Waiting" not in text
    assert "New environment" not in text
    assert "i_mean_it_migrate" in text


def test_hybrid_sydney_morning_flags_unchanged() -> None:
    """This change must not drop the Sydney morning cron or --no-db."""
    text = HYBRID.read_text(encoding="utf-8")
    assert text.count('cron: "30 20 * * 0-4"') == 1
    assert "--no-db" in text
    assert "i_mean_it_deliver:" in text
    assert "brief-and-deliver:" in text


def test_schema_report_matches_offline_sql_and_revision_files() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    from mm_memory.migrate import MIGRATIONS_DIR, alembic_head

    sql = SQL.read_text(encoding="utf-8")
    md = SCHEMA.read_text(encoding="utf-8")
    assert alembic_head() == "0012_heartbeat_if_not_exists"
    assert "postgresql://" not in sql
    assert "postgres://" not in sql
    assert "127.0.0.1" not in sql
    assert "CREATE EXTENSION" not in sql.upper()
    assert sql.strip().endswith("COMMIT;")
    assert "schedule_heartbeat" not in sql

    tables = re.findall(r"^CREATE TABLE (\w+)", sql, re.M)
    indexes = re.findall(r"^CREATE INDEX (\w+)", sql, re.M)
    uniques = re.findall(r"CONSTRAINT (\w+) UNIQUE", sql)
    assert len(tables) == 19
    assert len(indexes) == 33
    assert len(uniques) == 9
    for name in tables + indexes + uniques:
        assert f"`{name}`" in md
    assert "alembic_version_pkc" in sql
    assert "`alembic_version_pkc`" in md

    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    script = ScriptDirectory.from_config(cfg)
    revisions = list(script.walk_revisions())
    assert [rev.revision for rev in revisions][0] == "0012_heartbeat_if_not_exists"
    assert [rev.revision for rev in reversed(revisions)][0] == "0001_phase1"
    for rev in revisions:
        assert f"`{rev.revision}`" in md

    src11 = REV_0011.read_text(encoding="utf-8")
    src12 = REV_0012.read_text(encoding="utf-8")
    for needle in (
        'op.create_index("schedule_heartbeat_as_of_idx", TABLE, ["as_of_knowledge"])',
        'op.create_index("schedule_heartbeat_routine_idx", TABLE, ["routine_id"])',
        'name="schedule_heartbeat_routine_anchor_uidx"',
        "status IN ('ok','late','missed','skipped')",
        'name="schedule_heartbeat_status_check"',
    ):
        assert needle in src11
        assert needle in md
    for needle in (
        "CREATE TABLE IF NOT EXISTS {TABLE} (",
        "CREATE INDEX IF NOT EXISTS schedule_heartbeat_as_of_idx ON {TABLE} (as_of_knowledge)",
        "CREATE INDEX IF NOT EXISTS schedule_heartbeat_routine_idx ON {TABLE} (routine_id)",
        "ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {STATUS_CHECK}",
        "ALTER TABLE {TABLE} ADD CONSTRAINT {STATUS_CHECK} CHECK (status IN {NEW_STATUSES})",
        "('ok','late','missed','skipped','wrong_anchor')",
    ):
        assert needle in src12
        assert needle in md
    assert "CREATE EXTENSION" not in src11.upper()
    assert "CREATE EXTENSION" not in src12.upper()
