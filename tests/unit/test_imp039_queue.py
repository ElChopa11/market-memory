"""IMP-039 queue hygiene: single IN_PROGRESS; IMP-040 INTAKE_ONLY; IMP-034 stays ticker DONE."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import can_start, load_queue

ROOT = Path(__file__).resolve().parents[2]


def test_queue_imp039_single_thread_candidates_intake_only() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-039" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-040" in line and "INTAKE_ONLY" in line for line in board_lines)
    assert any("IMP-034" in line and "DONE" in line for line in board_lines)
    assert any("IMP-024" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-039" in line and "DONE" in line for line in board_lines)
    assert not any("IMP-024" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-034" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-040" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1** (IMP-039)" in queue
    assert "INTAKE_ONLY" in queue
    assert "research/candidates/" in queue
    assert "PR #61" in queue or "#61" in queue
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    assert (ROOT / "ops" / "plans" / "IMP-039-phase1-unconditional-base-rates.md").is_file()
    assert (ROOT / "docs" / "runbooks" / "base-rates.md").is_file()
    assert (ROOT / "ADR" / "0016-unconditional-base-rates.md").is_file()
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ("IMP-039",)
    assert report.auto_merge is False
    assert report.auto_waive is False
    ok, reason = can_start("IMP-040", report)
    assert ok is False
    assert "INTAKE_ONLY" in reason


def test_imp034_on_main_is_ticker_not_candidates() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    assert "Ticker resolutions + licence_verdict schema" in queue
    assert "IMP-034 on main is ticker/licence" in queue
