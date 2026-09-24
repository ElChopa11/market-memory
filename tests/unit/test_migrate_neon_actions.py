"""Runbook and hybrid flags after the one-shot Neon migrate workflow was deleted.

`.github/workflows/migrate-neon.yml` was removed the same sitting the
migrate succeeded. These tests read the runbook and
`hybrid-sydney-morning.yml` only. They do not require the workflow file.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HYBRID = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
RUNBOOK = ROOT / "docs" / "runbooks" / "migrate-neon.md"
INGEST = ROOT / "docs" / "runbooks" / "ingest.md"

CONFIRM = "i_mean_it_migrate"


def test_hybrid_sydney_morning_flags_unchanged() -> None:
    """Sydney morning cron and --no-db stay. The migrate confirm string does not."""
    text = HYBRID.read_text(encoding="utf-8")
    assert text.count('cron: "30 20 * * 0-4"') == 1
    assert text.count('cron: "30 22 * * 0-4"') == 1
    assert "--no-db" in text
    assert "i_mean_it_deliver:" in text
    assert "brief-and-deliver:" in text
    assert CONFIRM not in text


def test_runbook_is_the_same_sitting_delete_path() -> None:
    from mm_memory.migrate import alembic_head

    text = RUNBOOK.read_text(encoding="utf-8")
    head = alembic_head()
    assert head in text
    assert ".github/workflows/migrate-neon.yml" in text
    assert "workflow_dispatch" in text
    assert "repository_dispatch" in text
    assert CONFIRM in text
    assert "confirm" in text
    assert "POSTGRES_DSN" in text
    assert "DATABASE_URL" in text
    assert "uv run lab migrate" in text
    assert "migrated to" in text
    assert "SUCCESS: lab migrate exited 0" in text
    assert "SELECT version_num FROM alembic_version" in text
    assert "Delete `.github/workflows/migrate-neon.yml`" in text
    assert "same sitting" in text
    assert "#114" in text
    assert "shelved" in text
    assert "history-backfill" in text
    assert "#120" in text
    assert "hybrid-sydney-morning" in text
    assert "No cron" in text
    assert "Paper only" in text
    assert "No Telegram" in text
    assert "winget" not in text.lower()
    assert "Windows" not in text
    ingest = INGEST.read_text(encoding="utf-8")
    assert "docs/runbooks/migrate-neon.md" in ingest
