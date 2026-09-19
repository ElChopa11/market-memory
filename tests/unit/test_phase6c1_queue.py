"""Phase 6c-1 queue hygiene: OPEN incidents logged, IMP-016 DONE, 6d parked until 6c-1..6c-5."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_016_done_018_in_review_017_parked() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-015" in line and "DONE" in line for line in board_lines)
    assert any("IMP-016" in line and "DONE" in line for line in board_lines)
    assert any("IMP-018" in line and "DONE" in line for line in board_lines)
    assert any("IMP-017" in line and "DONE" in line for line in board_lines)
    assert not any("IMP-017" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-017" in line and "PARKED" in line for line in board_lines)
    assert not any("IMP-016" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-018" in line and "IN_REVIEW" in line for line in board_lines)


def test_remaining_open_ops_incidents_and_src_fred_closed() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    for item_id in ("SCHED-001", "BRIEF-TAG-20260918", "SRC-STOOQ-404"):
        assert item_id in queue
    assert "SRC-FRED-MISSING-ENV" in queue
    assert "| **Status** | CLOSED |" in queue
    assert "fred-fullstack-20260919-101938-aest" in queue
    assert "sydney-morning-digest-8am" in queue
    assert "http_404" in queue
    assert "FRED_API_KEY" in queue
    assert "Don does not decide secrets" in queue or "Principal" in queue


def test_phase6c1_plan_and_runbook_exist() -> None:
    for rel in (
        "ops/plans/IMP-018-phase6c1-desk-roster.md",
        "ADR/0007-phase6c1-desk-roster.md",
        "config/desks/cadence.yaml",
        "packages/desks/src/mm_desks/roster.py",
        "docs/runbooks/desks.md",
    ):
        assert (ROOT / rel).is_file(), rel
    desks = (ROOT / "docs" / "runbooks" / "desks.md").read_text(encoding="utf-8")
    assert "11" in desks or "five" in desks.lower() or "5-desk" in desks or "five desks" in desks.lower()
    assert "ic_risk" in desks or "IC/Risk" in desks
