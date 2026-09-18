"""Phase 6c-5 queue hygiene: IMP-020 DONE #52, IMP-021 this PR, 6d parked, OPEN incidents stay OPEN."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_020_done_021_in_review_017_parked() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-016" in line and "DONE" in line for line in board_lines)
    assert any("IMP-018" in line and "DONE" in line for line in board_lines)
    assert any("IMP-019" in line and "DONE" in line for line in board_lines)
    assert any("#51" in line for line in board_lines if "IMP-019" in line)
    assert any("IMP-020" in line and "DONE" in line for line in board_lines)
    assert any("#52" in line for line in board_lines if "IMP-020" in line)
    assert any("IMP-021" in line and "IN_REVIEW" in line for line in board_lines)
    assert any("IMP-017" in line and "PARKED" in line for line in board_lines)
    assert not any("IMP-020" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-020" in line and "PARKED" in line for line in board_lines)
    assert not any("IMP-021" in line and "PARKED" in line for line in board_lines)
    assert not any("IMP-021" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-017" in line and "IN_PROGRESS" in line for line in board_lines)
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
    assert "sydney-morning-digest-8am" in queue


def test_phase6c5_plan_adr_and_delivery_config_exist() -> None:
    for rel in (
        "ops/plans/IMP-021-phase6c5-delivery.md",
        "ADR/0010-phase6c5-delivery.md",
        "config/delivery/telegram.yaml",
        "packages/delivery/src/mm_delivery/watchlist.py",
        "packages/delivery/src/mm_delivery/matrix.py",
        "docs/runbooks/telegram.md",
        "docs/runbooks/watchlist.md",
        "docs/runbooks/desks.md",
    ):
        assert (ROOT / rel).is_file(), rel
    tg = (ROOT / "config" / "delivery" / "telegram.yaml").read_text(encoding="utf-8")
    assert "publisher: ops" in tg
    assert "owner: ops" in tg
    assert "coordinator: orchestration_only" in tg
    assert "kind: watchlist" in tg
    assert "TELEGRAM_CHAT_ID_RESEARCH" in tg
    assert "TELEGRAM_CHAT_ID_CRYPTO" not in tg
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    desks = (ROOT / "docs" / "runbooks" / "desks.md").read_text(encoding="utf-8")
    assert "lab deliver watchlist" in desks
    telegram = (ROOT / "docs" / "runbooks" / "telegram.md").read_text(encoding="utf-8")
    assert "Ops-owned" in telegram or "Ops publishes" in telegram
    assert "Coordinator is not the publisher" in telegram or "Coord is not the publisher" in telegram
    watch = (ROOT / "docs" / "runbooks" / "watchlist.md").read_text(encoding="utf-8")
    assert "lab deliver watchlist" in watch
