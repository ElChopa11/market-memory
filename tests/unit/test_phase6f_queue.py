"""Phase 6f queue hygiene: IMP-030 DONE #55, IMP-031 DONE #56, OPEN incidents stay OPEN."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_030_done_031_done_open_incidents() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-030" in line and "DONE" in line for line in board_lines)
    assert any("#55" in line for line in board_lines if "IMP-030" in line)
    assert any("IMP-031" in line and "DONE" in line for line in board_lines)
    assert any("#56" in line for line in board_lines if "IMP-031" in line)
    assert not any("IMP-030" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-030" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-031" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-031" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-031" in line and "PARKED" in line for line in board_lines)
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
    assert "sydney-morning-digest-8am" in queue


def test_phase6f_plan_adr_and_config_exist() -> None:
    for rel in (
        "ops/plans/IMP-030-phase6e-scorecards.md",
        "ops/plans/IMP-031-phase6f-decay-watch.md",
        "ADR/0012-phase6e-scorecards.md",
        "ADR/0013-phase6f-decay-watch.md",
        "config/scorecards/decay.yaml",
        "packages/quant/src/mm_quant/decay.py",
        "packages/quant/src/mm_quant/decay_stub.py",
        "packages/desks/src/mm_desks/decay.py",
        "packages/delivery/src/mm_delivery/decay.py",
        "docs/runbooks/decay.md",
        "docs/runbooks/desks.md",
    ):
        assert (ROOT / rel).is_file(), rel
    desks = (ROOT / "docs" / "runbooks" / "desks.md").read_text(encoding="utf-8")
    assert "lab decay watch" in desks
    assert "lab deliver decay" in desks
    decay = (ROOT / "config" / "scorecards" / "decay.yaml").read_text(encoding="utf-8")
    assert "watch_enabled: true" in decay
    assert "IMP-031" in decay
    assert "auto_disable: false" in decay
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    tg = (ROOT / "config" / "delivery" / "telegram.yaml").read_text(encoding="utf-8")
    assert "kind: decay" in tg
    assert "publisher: ops" in tg
    cadence = (ROOT / "config" / "desks" / "cadence.yaml").read_text(encoding="utf-8")
    assert "desk.decay.output" not in cadence
