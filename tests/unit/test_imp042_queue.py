"""IMP-042 queue hygiene: miss detector DONE #68; SCHED-001 CLOSED; zero IN_PROGRESS."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import can_start, load_queue

ROOT = Path(__file__).resolve().parents[2]


def test_queue_imp042_single_thread_sched001_closed_imp040_done() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-047" in line and "DONE" in line for line in board_lines)
    assert any("IMP-041" in line and "DONE" in line for line in board_lines)
    assert any("#67" in line for line in board_lines if "IMP-041" in line)
    assert any("IMP-040" in line and "DONE" in line for line in board_lines)
    assert any("#66" in line for line in board_lines if "IMP-040" in line)
    assert any("IMP-039" in line and "READY" in line for line in board_lines)
    assert not any("IMP-040" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-039" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **0**" in queue
    assert "Principal L2 sprint" in queue
    assert "P0 clock" in queue or "P0 clock/heartbeat" in queue or "P0" in queue
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    assert (ROOT / "ops" / "plans" / "IMP-042-scheduler-heartbeat.md").is_file()
    assert (ROOT / "ops" / "reports" / "scheduler" / "2026-09-19-sched-001-root-cause.md").is_file()
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ()
    assert report.auto_merge is False
    assert report.auto_waive is False
    public = report.as_public_dict()
    assert "SCHED-001" not in public["open_incidents"]
    ok, reason = can_start("IMP-039", report)
    assert ok is True
    assert "does not write" in reason


def test_sched001_is_p0_and_closed_with_run_id() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    assert "| **ID** | SCHED-001 |" in queue
    block = queue.split("### SCHED-001", 1)[1].split("### ", 1)[0]
    assert "| **Priority** | P0 |" in block
    assert "| **Status** | CLOSED |" in block
    assert "actions-b1-35727756341" in block
    assert "sydney-morning-digest-8am" in queue or "grok.sydney_morning" in queue
    # Five OPEN incidents remain after SCHED-001 close.
    assert queue.count("| **Status** | OPEN |") == 5
