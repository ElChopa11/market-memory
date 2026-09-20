"""IMP-056 occupies the single IN_PROGRESS slot; IMP-047 DONE; IMP-057 BACKLOG."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import can_start, load_queue

ROOT = Path(__file__).resolve().parents[2]


def test_queue_imp056_single_thread_047_done_057_backlog() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-056" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-047" in line and "DONE" in line for line in board_lines)
    assert any("IMP-042" in line and "DONE" in line for line in board_lines)
    assert any("IMP-046" in line and "DONE" in line for line in board_lines)
    assert any("IMP-057" in line and "BACKLOG" in line for line in board_lines)
    assert not any("IMP-057" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1** (IMP-056)" in queue
    assert "known-missed" in queue
    assert "wrong_anchor" in queue or "wrong-anchor" in queue or "slot/anchor" in queue
    assert "from-markdown" in queue
    assert (ROOT / "ops" / "plans" / "IMP-056-scheduler-chain-defects.md").is_file()
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ("IMP-056",)
    assert report.auto_merge is False
    assert report.auto_waive is False
    ok_057, reason_057 = can_start("IMP-057", report)
    assert ok_057 is False
    assert "BACKLOG" in reason_057 or "slot occupied" in reason_057
    ok_047, reason_047 = can_start("IMP-047", report)
    assert ok_047 is False
    assert "DONE" in reason_047
