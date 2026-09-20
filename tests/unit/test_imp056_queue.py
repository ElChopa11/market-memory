"""IMP-056 Chart OPTION A is BACKLOG docs-only; does not occupy IN_PROGRESS or retire render_png."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import can_start, load_queue

ROOT = Path(__file__).resolve().parents[2]


def test_queue_imp056_option_a_backlog_behind_monday_fire() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-056" in line and "BACKLOG" in line for line in board_lines)
    assert not any("IMP-056" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-047" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1** (IMP-047)" in queue
    for token in (
        "OPTION A",
        "render_png",
        "tv_snapshot_url",
        "librarian",
        "not renderer",
        "not retriever",
        "Monday 2026-09-21 unattended Sydney Morning",
        "config/watchlist/monitor.yaml",
        "CASHCAT",
        "BLOCKED",
        "briefs/",
        "lab deliver",
        "ambiguous",
        "No Telegram",
        "No C-00x",
        "never constructed",
        "mplfinance",
        "HL:ZEC",
        "linked_thesis_id",
        "content_hash",
    ):
        assert token in queue, token
    assert "| **Status** | BACKLOG |" in queue
    assert "this PR (docs/queue only; does not retire `render_png`)" in queue
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ("IMP-047",)
    assert report.auto_merge is False
    assert report.auto_waive is False
    ok, reason = can_start("IMP-056", report)
    assert ok is False
    assert "BACKLOG" in reason or "slot occupied" in reason


def test_charter_chart_sleeve_is_librarian_not_renderer_not_retriever() -> None:
    charters = (ROOT / "ops" / "desk-charters.md").read_text(encoding="utf-8")
    assert "librarian, not renderer, not retriever" in charters
    assert "### Chart sleeve (librarian — not renderer, not retriever)" in charters
    for token in (
        "OPTION A",
        "tv_snapshot_url",
        "does **not** retrieve, browse, log in, or capture",
        "Chart never publishes",
        "structured fields not pixels",
        "config/watchlist/monitor.yaml",
        "CASHCAT",
        "BLOCKED",
        "lab deliver",
        "IMP-056",
        "render_png",
        "No Telegram",
        "No C-00x",
    ):
        assert token in charters, token
    assert "sixth publishing desk" in charters.lower() or "not a sixth publishing desk" in charters


def test_house_lesson_2026_09_20_chart_option_a() -> None:
    lessons = (ROOT / "config" / "knowledge" / "house-lessons.md").read_text(encoding="utf-8")
    assert "2026-09-20" in lessons
    assert "Chart is librarian, not renderer, not retriever (OPTION A)" in lessons
    for token in (
        "OPTION A",
        "tv_snapshot_url",
        "markup only",
        "CASHCAT",
        "render_png",
        "Monday 2026-09-21 unattended Sydney Morning",
        "IMP-056 BACKLOG",
        "never constructed",
        "lab deliver",
        "config/watchlist/monitor.yaml",
        "retrieval framing",
        "option B",
    ):
        assert token in lessons, token


def test_render_png_still_exists_this_pr_does_not_retire_it() -> None:
    chart = (ROOT / "packages" / "desks" / "src" / "mm_desks" / "chart.py").read_text(encoding="utf-8")
    assert "def render_png(" in chart
    playbook = (ROOT / "packages" / "desks" / "src" / "mm_desks" / "playbook.py").read_text(encoding="utf-8")
    assert "render_png" in playbook
