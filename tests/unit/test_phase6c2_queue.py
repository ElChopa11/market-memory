"""Phase 6c-2 queue hygiene: IMP-018 DONE #49, IMP-019 DONE #51 (hygiene on IMP-020)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_018_done_019_done_parked_followons() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-016" in line and "DONE" in line for line in board_lines)
    assert any("IMP-018" in line and "DONE" in line for line in board_lines)
    assert any("#49" in line for line in board_lines if "IMP-018" in line)
    assert any("IMP-019" in line and "DONE" in line for line in board_lines)
    assert any("#51" in line for line in board_lines if "IMP-019" in line)
    assert any("IMP-017" in line and "DONE" in line for line in board_lines)
    assert not any("IMP-018" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-019" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-019" in line and "PARKED" in line for line in board_lines)
    assert not any("IMP-017" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-017" in line and "PARKED" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1**" in queue
    assert any("IMP-033" in line and "DONE" in line for line in board_lines)
    assert any("IMP-022" in line and "DONE" in line for line in board_lines)
    assert any("IMP-042" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-040" in line and "DONE" in line for line in board_lines)
    assert any("IMP-024" in line and "DONE" in line for line in board_lines)
    assert not any("IMP-024" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-022" in line and "IN_PROGRESS" in line for line in board_lines)
    for item_id in (
        "IMP-025",
        "IMP-026",
        "IMP-027",
        "IMP-028",
        "IMP-029",
    ):
        assert any(item_id in line and "BACKLOG" in line for line in board_lines), item_id
        assert not any(item_id in line and "IN_PROGRESS" in line for line in board_lines)
    assert (ROOT / "ops" / "reports" / "source-evaluation" / "2026-09-18.md").is_file()
    assert (ROOT / "ops" / "reports" / "source-evaluation" / "README.md").is_file()


def test_phase6c2_plan_adr_and_naming_config_exist() -> None:
    for rel in (
        "ops/plans/IMP-019-phase6c2-naming.md",
        "ADR/0008-phase6c2-naming.md",
        "config/desks/naming.yaml",
        "packages/common/src/mm_common/naming.py",
        "packages/desks/src/mm_desks/naming.py",
        "docs/runbooks/desks.md",
    ):
        assert (ROOT / rel).is_file(), rel
    desks = (ROOT / "docs" / "runbooks" / "desks.md").read_text(encoding="utf-8")
    assert "naming.yaml" in desks
    assert "ic_risk" in desks or "IC/Risk" in desks
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
