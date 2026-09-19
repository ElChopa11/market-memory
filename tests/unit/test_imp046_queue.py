"""IMP-046 is DONE (#72); IMP-047 holds the single IN_PROGRESS slot."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import can_start, load_queue

ROOT = Path(__file__).resolve().parents[2]


def test_queue_imp046_done_047_holds_slot() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-046" in line and "DONE" in line for line in board_lines)
    assert any("IMP-047" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-043" in line and "DONE" in line for line in board_lines)
    assert any("IMP-044" in line and "BACKLOG" in line for line in board_lines)
    assert any("IMP-045" in line and "BACKLOG" in line for line in board_lines)
    assert not any("IMP-046" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-044" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-045" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1** (IMP-047)" in queue
    assert (ROOT / "ops" / "plans" / "IMP-046-hybrid-cli-completions.md").is_file()
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ("IMP-047",)
    assert report.auto_merge is False
    assert report.auto_waive is False
    ok_044, reason_044 = can_start("IMP-044", report)
    assert ok_044 is False
    assert "BACKLOG" in reason_044 or "slot occupied" in reason_044
    ok_046, reason_046 = can_start("IMP-046", report)
    assert ok_046 is False
    assert "DONE" in reason_046
