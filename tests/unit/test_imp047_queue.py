"""IMP-047 occupies the single IN_PROGRESS slot; IMP-046 DONE; IMP-048 BACKLOG."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import can_start, load_queue

ROOT = Path(__file__).resolve().parents[2]


def test_queue_imp047_single_thread_046_done_048_backlog() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-047" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-046" in line and "DONE" in line for line in board_lines)
    assert any("#72" in line for line in board_lines if "IMP-046" in line)
    assert any("IMP-048" in line and "BACKLOG" in line for line in board_lines)
    assert "agent authoring" in queue.lower() or "Do not allow agent authoring" in queue
    assert not any("IMP-046" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-048" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-044" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1** (IMP-047)" in queue
    assert (ROOT / "ops" / "plans" / "IMP-047-hybrid-dm-only-send.md").is_file()
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ("IMP-047",)
    assert report.auto_merge is False
    assert report.auto_waive is False
    ok_048, reason_048 = can_start("IMP-048", report)
    assert ok_048 is False
    assert "BACKLOG" in reason_048 or "slot occupied" in reason_048
    ok_046, reason_046 = can_start("IMP-046", report)
    assert ok_046 is False
    assert "DONE" in reason_046
