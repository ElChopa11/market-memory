"""IMP-024 queue hygiene: IMP-022 DONE #60; EDGAR is the single IN_PROGRESS."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import load_queue

ROOT = Path(__file__).resolve().parents[2]


def test_queue_imp022_done_edgar_single_thread_open_incidents() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-022" in line and "DONE" in line for line in board_lines)
    assert any("#60" in line for line in board_lines if "IMP-022" in line)
    assert any("IMP-024" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-022" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-023" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-025" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-035" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1**" in queue
    for item_id in ("IMP-023", "IMP-035"):
        assert any(item_id in line and "READY" in line for line in board_lines), item_id
    for item_id in ("SCHED-001", "BRIEF-TAG-20260918", "SRC-STOOQ-404", "SRC-FRED-MISSING-ENV"):
        assert item_id in queue
    assert queue.count("| **Status** | OPEN |") >= 4
    assert "Treasury.gov is IMP-035" in queue or "IMP-035" in queue
    assert (ROOT / "ops" / "plans" / "IMP-024-edgar.md").is_file()
    assert (ROOT / "docs" / "runbooks" / "edgar.md").is_file()
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    report = load_queue(ROOT)
    assert report.ok
    assert report.in_progress == ("IMP-024",)
    assert report.auto_merge is False
    assert report.auto_waive is False
    assert "SRC-STOOQ-404" in report.as_public_dict()["open_incidents"]
    assert "SRC-FRED-MISSING-ENV" in report.as_public_dict()["open_incidents"]
