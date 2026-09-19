"""IMP-034 + IMP-022 queue hygiene: IMP-033 DONE #59, FRED full-stack single IN_PROGRESS."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import load_queue

ROOT = Path(__file__).resolve().parents[2]


def test_queue_imp033_done_fred_single_thread_open_incidents() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-033" in line and "DONE" in line for line in board_lines)
    assert any("#59" in line for line in board_lines if "IMP-033" in line)
    assert any("IMP-034" in line and "DONE" in line for line in board_lines)
    assert any("IMP-022" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-033" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-034" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1**" in queue
    for item_id in ("IMP-023", "IMP-024", "IMP-035"):
        assert any(item_id in line and "READY" in line for line in board_lines), item_id
        assert not any(item_id in line and "IN_PROGRESS" in line for line in board_lines)
    for item_id in ("IMP-036", "IMP-037", "IMP-038"):
        assert any(item_id in line and "BACKLOG" in line for line in board_lines), item_id
    for item_id in ("SCHED-001", "BRIEF-TAG-20260918", "SRC-STOOQ-404", "SRC-FRED-MISSING-ENV"):
        assert item_id in queue
    assert queue.count("| **Status** | OPEN |") >= 4
    assert "http_404" in queue
    assert "--no-db" in queue
    assert "ELIGIBLE" in queue
    assert (ROOT / "ops" / "plans" / "IMP-034-ticker-licence-verdict.md").is_file()
    assert (ROOT / "ops" / "plans" / "IMP-022-fred-fullstack.md").is_file()
    assert (ROOT / "ADR" / "0015-licence-verdict-standing-rule.md").is_file()
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    report = load_queue(ROOT)
    assert report.ok
    assert report.in_progress == ("IMP-022",)
    assert report.auto_merge is False
    assert report.auto_waive is False
    assert "SRC-STOOQ-404" in report.as_public_dict()["open_incidents"]
    assert "SRC-FRED-MISSING-ENV" in report.as_public_dict()["open_incidents"]
