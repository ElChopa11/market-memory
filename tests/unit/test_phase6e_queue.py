"""Phase 6e queue hygiene after 6f: IMP-017 DONE #54, IMP-030 DONE #55, IMP-031 DONE #56."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_017_done_030_done_031_done() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-017" in line and "DONE" in line for line in board_lines)
    assert any("#54" in line for line in board_lines if "IMP-017" in line)
    assert any("IMP-021" in line and "DONE" in line for line in board_lines)
    assert any("IMP-030" in line and "DONE" in line for line in board_lines)
    assert any("#55" in line for line in board_lines if "IMP-030" in line)
    assert any("IMP-031" in line and "DONE" in line for line in board_lines)
    assert any("#56" in line for line in board_lines if "IMP-031" in line)
    assert not any("IMP-017" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-017" in line and "PARKED" in line for line in board_lines)
    assert not any("IMP-017" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-030" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-030" in line and "IN_REVIEW" in line for line in board_lines)
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
    assert "| **Status** | ELIGIBLE |" in queue
    assert "sydney-morning-digest-8am" in queue


def test_phase6e_plan_adr_and_config_exist() -> None:
    for rel in (
        "ops/plans/IMP-030-phase6e-scorecards.md",
        "ops/plans/IMP-031-phase6f-decay-watch.md",
        "ADR/0012-phase6e-scorecards.md",
        "config/scorecards/desk.yaml",
        "config/scorecards/tags.yaml",
        "config/scorecards/decay.yaml",
        "packages/quant/src/mm_quant/scorecard.py",
        "packages/quant/src/mm_quant/decay.py",
        "packages/quant/src/mm_quant/decay_stub.py",
        "packages/desks/src/mm_desks/scorecard.py",
        "packages/desks/src/mm_desks/queue.py",
        "packages/delivery/src/mm_delivery/scorecard.py",
        "docs/runbooks/scorecards.md",
        "docs/runbooks/desks.md",
        "scripts/check_queue.py",
    ):
        assert (ROOT / rel).is_file(), rel
    desks = (ROOT / "docs" / "runbooks" / "desks.md").read_text(encoding="utf-8")
    assert "lab scorecard compare" in desks
    assert "lab deliver scorecard" in desks
    assert "lab queue check" in desks
    spec = (ROOT / "config" / "scorecards" / "desk.yaml").read_text(encoding="utf-8")
    assert "desk: quant" in spec
    assert "promote: false" in spec
    assert "llm: false" in spec
    assert "send: false" in spec
    tags = (ROOT / "config" / "scorecards" / "tags.yaml").read_text(encoding="utf-8")
    assert "BRIEF-TAG-20260918" in tags
    assert "pre_open_90m" in tags
    assert "pre_open_30m" in tags
    decay = (ROOT / "config" / "scorecards" / "decay.yaml").read_text(encoding="utf-8")
    assert "watch_enabled: true" in decay
    assert "IMP-031" in decay
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    tg = (ROOT / "config" / "delivery" / "telegram.yaml").read_text(encoding="utf-8")
    assert "kind: scorecard" in tg
    assert "publisher: ops" in tg
    cadence = (ROOT / "config" / "desks" / "cadence.yaml").read_text(encoding="utf-8")
    assert "desk.scorecard.output" not in cadence
