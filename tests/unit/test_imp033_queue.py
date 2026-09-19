"""IMP-033 queue hygiene: IMP-033 DONE #59 after merge; current thread is IMP-024."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import load_queue

ROOT = Path(__file__).resolve().parents[2]


def test_queue_imp032_done_imp033_single_thread_open_incidents() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-032" in line and "DONE" in line for line in board_lines)
    assert any("#57" in line for line in board_lines if "IMP-032" in line)
    assert any("IMP-033" in line and "DONE" in line for line in board_lines)
    assert any("#59" in line for line in board_lines if "IMP-033" in line)
    assert not any("IMP-032" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-033" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1**" in queue
    for item_id in ("SCHED-001", "BRIEF-TAG-20260918", "SRC-STOOQ-404", "SRC-FRED-MISSING-ENV"):
        assert item_id in queue
    assert queue.count("| **Status** | OPEN |") >= 3
    assert (ROOT / "ops" / "plans" / "IMP-033-canonical-watchlist-monitor.md").is_file()
    assert (ROOT / "config" / "watchlist" / "monitor.yaml").is_file()
    assert (ROOT / "ADR" / "0014-canonical-watchlist-monitor.md").is_file()
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    report = load_queue(ROOT)
    assert report.ok
    assert report.in_progress == ("IMP-043",)
    assert report.auto_merge is False
    assert report.auto_waive is False
