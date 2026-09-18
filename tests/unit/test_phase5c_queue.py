"""Phase 5c queue hygiene: IMP-010 DONE, IMP-011 this PR, IMP-012 parked."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_010_done_011_in_review_012_parked() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-010" in line and "DONE" in line for line in board_lines)
    assert any("IMP-011" in line and "IN_REVIEW" in line for line in board_lines)
    assert any("IMP-012" in line and ("READY" in line or "PARKED" in line) for line in board_lines)
    assert not any("IMP-012" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "IMP-011" in queue
    assert "quant" in queue.lower()


def test_phase5c_plan_runbook_config_and_fixtures_exist() -> None:
    for rel in (
        "ops/plans/IMP-011-phase5c-quant-factors.md",
        "ops/plans/IMP-012-phase5d-desk-runners.md",
        "docs/runbooks/quant-desk.md",
        "config/quant/factors.yaml",
        "config/quant/regime.yaml",
        "templates/quant-factor-card.md",
        "tests/fixtures/phase5c/panel.json",
        "tests/fixtures/phase5c/lookahead_trap.json",
        "tests/fixtures/phase5c/missing_feeds.json",
        "packages/quant/src/mm_quant/factors.py",
        "packages/quant/src/mm_quant/regime.py",
        "packages/quant/src/mm_quant/stats.py",
        "packages/quant/src/mm_quant/sizing.py",
    ):
        assert (ROOT / rel).is_file(), rel


def test_readme_phase5c_status() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "5c" in readme
    assert "IMP-011" in readme
    assert "quant" in readme.lower()
