"""IMP-059 PARKED with plan file; zero IN_PROGRESS; cards stay INTAKE_ONLY."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import can_start, load_queue

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "ops" / "plans" / "IMP-059-c00x-instance-autotrack-detectors.md"


def test_queue_imp059_parked_plan_present_slot_clear() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-059" in line and "PARKED" in line for line in board_lines)
    assert not any("IMP-059" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-056" in line and "DONE" in line for line in board_lines)
    assert any("#85" in line for line in board_lines if "IMP-056" in line)
    assert "`IN_PROGRESS` count: **0**" in queue
    assert "instance auto-track" in queue.lower() or "auto-track" in queue.lower()
    assert "INSUFFICIENT SAMPLE" in queue
    assert "IC Gate 1 FAIL" in queue or "IC Gate 1" in queue
    assert PLAN.is_file()
    plan = PLAN.read_text(encoding="utf-8")
    assert "PARKED" in plan
    assert "fixture" in plan.lower()
    assert "--no-db" in plan
    assert "per-instrument" in plan.lower()
    assert "INSUFFICIENT SAMPLE" in plan
    assert "do not build" in plan.lower() or "not build" in plan.lower()
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ()
    assert report.auto_merge is False
    assert report.auto_waive is False
    ok_059, reason_059 = can_start("IMP-059", report)
    assert ok_059 is False
    assert "PARKED" in reason_059
    # Candidate intake stays READY / cards INTAKE_ONLY — do not flip.
    assert any("IMP-039" in line and "READY" in line for line in board_lines)
    assert "INTAKE_ONLY" in queue
