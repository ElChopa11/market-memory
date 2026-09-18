"""Phase 5b queue hygiene (IMP-010 closed on main as #41)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_009_and_010_done() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-009" in line and "DONE" in line for line in board_lines)
    assert any("IMP-010" in line and "DONE" in line for line in board_lines)
    assert "Polygon" in queue


def test_phase5b_plan_and_runbook_exist() -> None:
    for rel in (
        "ops/plans/IMP-010-phase5b-polygon-hl-structure.md",
        "ops/plans/IMP-011-phase5c-quant-factors.md",
        "docs/runbooks/polygon-hl-structure.md",
        "tests/fixtures/phase5b/polygon_ohlcv.json",
        "tests/fixtures/phase5b/hl_structure.json",
        "packages/ingest/src/mm_ingest/equities/polygon.py",
    ):
        assert (ROOT / rel).is_file(), rel


def test_readme_phase5b_status() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "5b" in readme
    assert "Polygon" in readme
    assert "IMP-010" in readme
