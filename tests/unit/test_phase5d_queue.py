"""Phase 5d queue hygiene: IMP-012 DONE after #43; 5e follows."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_011_done_012_in_review_013_parked() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-011" in line and "DONE" in line for line in board_lines)
    assert any("IMP-012" in line and "DONE" in line for line in board_lines)
    assert any("IMP-013" in line and "IN_REVIEW" in line for line in board_lines)
    assert "IMP-012" in queue
    assert "desk" in queue.lower()


def test_phase5d_plan_runbook_and_fixtures_exist() -> None:
    for rel in (
        "ops/plans/IMP-012-phase5d-desk-runners.md",
        "ops/plans/IMP-013-phase5e-telegram.md",
        "docs/runbooks/desks.md",
        "tests/fixtures/phase5d/frozen_day.json",
        "tests/fixtures/phase5d/missing_feed.json",
        "tests/fixtures/phase5d/skeptic_fail.json",
        "tests/fixtures/phase5d/risk_block.json",
        "packages/desks/src/mm_desks/orchestrator.py",
        "packages/desks/src/mm_desks/protocol.py",
        "packages/risk/src/mm_risk/engine.py",
        "packages/delivery/src/mm_delivery/payload.py",
    ):
        assert (ROOT / rel).is_file(), rel


def test_readme_phase5d_status() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "5d" in readme
    assert "IMP-012" in readme
    assert "desk" in readme.lower()
    assert "Telegram" in readme
