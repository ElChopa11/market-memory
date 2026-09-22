"""IMP-040 DONE #66; IMP-056 DONE #85; zero IN_PROGRESS; IMP-039 READY."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import can_start, load_queue

ROOT = Path(__file__).resolve().parents[2]


def test_queue_imp040_single_thread_candidates_ready() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-047" in line and "DONE" in line for line in board_lines)
    assert any("IMP-040" in line and "DONE" in line for line in board_lines)
    assert any("IMP-039" in line and "READY" in line for line in board_lines)
    assert any("IMP-034" in line and "DONE" in line for line in board_lines)
    assert any("IMP-024" in line and "DONE" in line for line in board_lines)
    assert not any("IMP-040" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-039" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-024" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-034" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **0**" in queue
    assert "INTAKE_ONLY" in queue
    assert "research/candidates/" in queue
    assert "PR #61" in queue or "#61" in queue
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    assert (ROOT / "ops" / "plans" / "IMP-040-phase1-unconditional-base-rates.md").is_file()
    assert (ROOT / "ops" / "plans" / "IMP-039-candidate-strategy-intake.md").is_file()
    assert (ROOT / "docs" / "runbooks" / "base-rates.md").is_file()
    assert (ROOT / "ADR" / "0017-unconditional-base-rates.md").is_file()
    assert (ROOT / "ADR" / "0016-edgar-adapter.md").is_file()
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ()
    assert report.auto_merge is False
    assert report.auto_waive is False
    ok, reason = can_start("IMP-039", report)
    assert ok is True
    assert "does not write" in reason


def test_imp034_on_main_is_ticker_not_candidates() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    assert "Ticker resolutions + licence_verdict schema" in queue
    assert "IMP-034 on main is ticker/licence" in queue
