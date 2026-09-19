"""IMP-024 queue hygiene: IMP-022 FRED DONE; EDGAR single IN_PROGRESS; Stooq OPEN."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import load_queue

ROOT = Path(__file__).resolve().parents[2]
RUN_ID = "fred-fullstack-20260919-101938-aest"


def test_queue_imp022_done_edgar_single_thread_stooq_open() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-022" in line and "DONE" in line for line in board_lines)
    assert any(RUN_ID in line for line in board_lines if "IMP-022" in line)
    assert any("#60" in line for line in board_lines if "IMP-022" in line)
    assert any("IMP-024" in line and "DONE" in line for line in board_lines)
    assert not any("IMP-022" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-024" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1** (IMP-047)" in queue
    for item_id in ("IMP-023", "IMP-035"):
        assert any(item_id in line and "READY" in line for line in board_lines), item_id
        assert not any(item_id in line and "IN_PROGRESS" in line for line in board_lines)
    for item_id in (
        "SCHED-001",
        "BRIEF-TAG-20260918",
        "SRC-STOOQ-404",
        "SRC-FRED-MISSING-ENV",
        "SRC-OBJECT-STORE",
        "TG-UNGATED-PRE-HYBRID",
    ):
        assert item_id in queue
    assert queue.count("| **Status** | OPEN |") == 6
    assert "http_404" in queue
    assert "SRC-STOOQ-404" in queue
    assert RUN_ID in queue
    assert (ROOT / "ops" / "plans" / "IMP-024-edgar-wire.md").is_file()
    assert (ROOT / "ops" / "plans" / "IMP-022-fred-fullstack.md").is_file()
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    report = load_queue(ROOT)
    assert report.ok
    assert report.in_progress == ("IMP-047",)
    assert report.auto_merge is False
    assert report.auto_waive is False
    public = report.as_public_dict()
    assert "SRC-STOOQ-404" in public["open_incidents"]
    assert "SRC-FRED-MISSING-ENV" in public["open_incidents"]
    assert "SRC-OBJECT-STORE" in public["open_incidents"]
    assert "TG-UNGATED-PRE-HYBRID" in public["open_incidents"]
