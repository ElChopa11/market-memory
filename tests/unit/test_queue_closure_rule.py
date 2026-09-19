"""Principal QUEUE CLOSURE RULE: --no-db is ELIGIBLE, never CLOSED."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import load_queue

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "ops" / "improvement-queue.md"
REPORT = ROOT / "ops" / "reports" / "source-health" / "2026-09-19.md"
SHA = ROOT / "ops" / "reports" / "source-health" / "2026-09-19.sha256"


def test_closure_rule_section_and_fred_eligible_not_closed() -> None:
    queue = QUEUE.read_text(encoding="utf-8")
    assert "## QUEUE CLOSURE RULE (Principal)" in queue
    assert "Close ONLY" in queue or "Close an incident **only**" in queue
    assert "Postgres attached" in queue
    assert "rows landed" in queue
    assert "provenance ids resolvable" in queue
    assert "published artifact" in queue
    assert "`--no-db` / partial → `ELIGIBLE` only, never `CLOSED`." in queue or "ELIGIBLE only, never" in queue
    assert "OPEN` → `ELIGIBLE` → `CLOSED`" in queue or "open → eligible → closed" in queue.lower()
    assert "missing_env" in queue
    assert "http_4xx" in queue or "http_4xx" in queue.lower() or "`http_4xx`" in queue
    assert "Weeks of failure" in queue

    start = queue.index("### SRC-FRED-MISSING-ENV")
    end = queue.index("### IMP-000")
    block = queue[start:end]
    assert "| **Status** | ELIGIBLE |" in block
    assert "| **Status** | CLOSED |" not in block
    assert "| **Status** | DONE |" not in block
    assert "| **Status** | OPEN |" not in block
    assert "2026-09-19" in block
    assert "--no-db" in block
    assert "credentials_present=yes" in block or "credentials yes" in block
    assert "fred≠missing_env" in block or "fred!=missing_env" in block or "≠missing_env" in block

    board = [line for line in queue.splitlines() if line.startswith("| SRC-FRED-MISSING-ENV")]
    assert board
    assert "| ELIGIBLE |" in board[0]
    assert "| CLOSED |" not in board[0]

    for item_id in ("SCHED-001", "BRIEF-TAG-20260918", "SRC-STOOQ-404"):
        assert item_id in queue
    assert "object_store" in queue
    assert "missing_env" in queue


def test_source_health_20260919_attach_exists() -> None:
    assert REPORT.is_file()
    assert SHA.is_file()
    text = REPORT.read_text(encoding="utf-8")
    assert "2026-09-19T10:01:05+10" in text
    assert "lab data source-health" in text
    assert "--no-db" in text
    assert "status=ok" in text or "Status: `ok`" in text
    assert "error_class=none" in text or "Error class: `none`" in text
    assert "credentials_present=yes" in text or "Credentials present: `yes`" in text
    assert "http_404" in text
    assert "object_store" in text
    assert "missing_env" in text
    assert "never CLOSED" in text or "not a CLOSED" in text
    assert "4.21" not in text  # no FRED print


def test_queue_helper_eligible_not_a_slot() -> None:
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ("IMP-033",)
    assert "SRC-FRED-MISSING-ENV" in report.as_public_dict()["eligible_incidents"]
    assert "SRC-FRED-MISSING-ENV" not in report.as_public_dict()["open_incidents"]
    for item_id in ("SCHED-001", "BRIEF-TAG-20260918", "SRC-STOOQ-404"):
        assert item_id in report.as_public_dict()["open_incidents"]
    assert report.auto_merge is False
    assert report.auto_waive is False
