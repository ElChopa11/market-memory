"""Phase 6c-4 queue hygiene: IMP-019 DONE #51, IMP-020 DONE #52 (hygiene on IMP-021)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_019_done_020_done_021_this_pr() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-016" in line and "DONE" in line for line in board_lines)
    assert any("IMP-018" in line and "DONE" in line for line in board_lines)
    assert any("IMP-019" in line and "DONE" in line for line in board_lines)
    assert any("#51" in line for line in board_lines if "IMP-019" in line)
    assert any("IMP-020" in line and "DONE" in line for line in board_lines)
    assert any("#52" in line for line in board_lines if "IMP-020" in line)
    assert any("IMP-021" in line and "DONE" in line for line in board_lines)
    assert any("#53" in line for line in board_lines if "IMP-021" in line)
    assert any("IMP-017" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-019" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-020" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-020" in line and "PARKED" in line for line in board_lines)
    assert not any("IMP-017" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-017" in line and "PARKED" in line for line in board_lines)
    assert not any("IMP-021" in line and "PARKED" in line for line in board_lines)
    assert not any("IMP-021" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-021" in line and "IN_REVIEW" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **0**" in queue
    for item_id in (
        "IMP-022",
        "IMP-023",
        "IMP-024",
        "IMP-025",
        "IMP-026",
        "IMP-027",
        "IMP-028",
        "IMP-029",
    ):
        assert any(item_id in line and "BACKLOG" in line for line in board_lines), item_id
        assert not any(item_id in line and "IN_PROGRESS" in line for line in board_lines)
    for item_id in ("SCHED-001", "BRIEF-TAG-20260918", "SRC-STOOQ-404", "SRC-FRED-MISSING-ENV"):
        assert item_id in queue
    assert "| **Status** | OPEN |" in queue or "**Status** | OPEN" in queue


def test_phase6c4_plan_adr_and_config_exist() -> None:
    for rel in (
        "ops/plans/IMP-020-phase6c4-watchlist.md",
        "ADR/0009-phase6c4-watchlist.md",
        "config/desks/watchlist.yaml",
        "packages/desks/src/mm_desks/watchlist.py",
        "docs/runbooks/watchlist.md",
        "docs/runbooks/desks.md",
    ):
        assert (ROOT / rel).is_file(), rel
    desks = (ROOT / "docs" / "runbooks" / "desks.md").read_text(encoding="utf-8")
    assert "watchlist" in desks
    assert "lab watchlist scan" in desks
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    spec = (ROOT / "config" / "desks" / "watchlist.yaml").read_text(encoding="utf-8")
    assert "promote: false" in spec
    assert "llm: false" in spec
    assert "send: false" in spec
    assert "deferred_must_cut" in spec
