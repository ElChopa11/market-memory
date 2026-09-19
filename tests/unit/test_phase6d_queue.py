"""Phase 6d queue hygiene: IMP-021 DONE #53, IMP-017 this PR, OPEN incidents stay OPEN."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_021_done_017_in_review() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-016" in line and "DONE" in line for line in board_lines)
    assert any("IMP-018" in line and "DONE" in line for line in board_lines)
    assert any("IMP-019" in line and "DONE" in line for line in board_lines)
    assert any("IMP-020" in line and "DONE" in line for line in board_lines)
    assert any("#52" in line for line in board_lines if "IMP-020" in line)
    assert any("IMP-021" in line and "DONE" in line for line in board_lines)
    assert any("#53" in line for line in board_lines if "IMP-021" in line)
    assert any("IMP-017" in line and "DONE" in line for line in board_lines)
    assert any("#54" in line for line in board_lines if "IMP-017" in line)
    assert not any("IMP-021" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-021" in line and "PARKED" in line for line in board_lines)
    assert not any("IMP-017" in line and "PARKED" in line for line in board_lines)
    assert not any("IMP-017" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-017" in line and "IN_REVIEW" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1**" in queue
    assert any("IMP-033" in line and "IN_PROGRESS" in line for line in board_lines)
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
    assert "| **Status** | ELIGIBLE |" in queue
    assert "sydney-morning-digest-8am" in queue


def test_phase6d_plan_adr_and_config_exist() -> None:
    for rel in (
        "ops/plans/IMP-017-phase6d-listings-ipo.md",
        "ADR/0011-phase6d-listings.md",
        "config/listings/desk.yaml",
        "config/listings/calendar.yaml",
        "config/listings/index_events.yaml",
        "packages/listings/src/mm_listings/engine.py",
        "packages/desks/src/mm_desks/listings.py",
        "packages/delivery/src/mm_delivery/listings.py",
        "docs/runbooks/listings.md",
        "docs/runbooks/desks.md",
        "packages/memory/src/mm_memory/migrations/versions/0009_phase6d_listings.py",
    ):
        assert (ROOT / rel).is_file(), rel
    desks = (ROOT / "docs" / "runbooks" / "desks.md").read_text(encoding="utf-8")
    assert "lab listings scan" in desks
    assert "lab deliver listings" in desks
    spec = (ROOT / "config" / "listings" / "desk.yaml").read_text(encoding="utf-8")
    assert "desk: research" in spec
    assert "promote: false" in spec
    assert "llm: false" in spec
    assert "send: false" in spec
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    tg = (ROOT / "config" / "delivery" / "telegram.yaml").read_text(encoding="utf-8")
    assert "kind: listings" in tg
    assert "publisher: ops" in tg
    cadence = (ROOT / "config" / "desks" / "cadence.yaml").read_text(encoding="utf-8")
    assert "desk.listings.output" not in cadence
