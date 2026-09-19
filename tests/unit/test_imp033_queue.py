"""IMP-033 queue intake: canonical watchlist monitor.yaml Principal lock.

Paper only. Does not reopen IMP-020. OPEN incidents stay OPEN.
"""

from __future__ import annotations

import re
from pathlib import Path

from mm_desks.queue import check_queue, load_queue

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "ops" / "improvement-queue.md"
PLAN = ROOT / "ops" / "plans" / "IMP-033-watchlist-monitor-yaml.md"
LIVE = ROOT / "config" / "risk" / "environments" / "live.yaml"
UNIVERSE = ROOT / "config" / "universe.yaml"
OPEN_INCIDENTS = (
    "SCHED-001",
    "BRIEF-TAG-20260918",
    "SRC-STOOQ-404",
)
ELIGIBLE_INCIDENTS = ("SRC-FRED-MISSING-ENV",)


def test_queue_imp032_done_imp033_single_thread_open_incidents() -> None:
    queue = QUEUE.read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-032" in line and "DONE" in line for line in board_lines)
    assert any("#57" in line for line in board_lines if "IMP-032" in line)
    assert not any("IMP-032" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-032" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-033" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any(
        "IMP-033" in line and "#59" in line and "cursor/canonical-watchlist-monitor-5515" in line
        for line in board_lines
    )
    assert any("IMP-020" in line and "DONE" in line for line in board_lines)
    assert any("#52" in line for line in board_lines if "IMP-020" in line)
    in_progress = re.findall(r"\| \*\*Status\*\* \| IN_PROGRESS \|", queue)
    assert in_progress == ["| **Status** | IN_PROGRESS |"]
    assert "`IN_PROGRESS` count: **1**" in queue
    for item_id in OPEN_INCIDENTS:
        assert item_id in queue
    for item_id in ELIGIBLE_INCIDENTS:
        assert item_id in queue
    assert queue.count("| **Status** | OPEN |") >= 3
    assert "| **Status** | ELIGIBLE |" in queue
    assert "sydney-morning-digest-8am" in queue
    assert PLAN.is_file()
    live = LIVE.read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live


def test_imp033_required_fields_and_lock() -> None:
    queue = QUEUE.read_text(encoding="utf-8")
    start = queue.index("### IMP-033 — Canonical watchlist monitor.yaml (Principal lock)")
    end = queue.index("## Status board")
    block = queue[start:end]
    for field in (
        "ID",
        "Priority",
        "Type",
        "Desk",
        "Owner",
        "Problem",
        "Evidence",
        "Proposed outcome",
        "Definition of done",
        "Non-goals",
        "Dependencies",
        "Risk level",
        "Status",
        "PR",
        "Lesson learned",
    ):
        assert f"| **{field}** |" in block, field
    assert "| **Priority** | P1 |" in block
    assert "| **Type** | config/desk product |" in block
    assert "Ops + Research" in block
    assert "Ops/Don" in block
    assert "| **Status** | IN_PROGRESS |" in block
    assert "config/watchlist/monitor.yaml" in block
    assert "tiers/clusters" in block
    assert "crypto then base" in block
    assert "membership is not a call" in block.lower()
    assert "no universe expand" in block.lower() or "No universe expand" in block
    assert "Do not reopen IMP-020" in block
    assert "Ops does not publish until config-backed" in block
    assert "paper only" in block.lower()
    assert "| **Status** | IN_PROGRESS |" in block
    assert "NASDAQ:SPCX" in block
    assert "Space Exploration Technologies Corp" in block
    assert "NOT SPAC ETF" in block
    assert "cluster `idio`" in block
    assert "NASDAQ:CBRS" in block
    assert "Cerebras Systems Inc" in block
    assert "semis_ai" in block
    assert "MOVED from idio" in block
    assert "HL:CHIP" in block
    assert "display CHIPIUSD" in block
    assert "HL:VVV" in block
    assert "HL:PURR" in block
    assert "Still unresolved (out of ideas until Principal paste):** SAMSUN, KOSDA." in block
    assert "PURR, VVVUSD, CHIPIUSD" not in block
    assert "until Principal paste" in block
    assert "NEW_LISTING" in block
    assert "n/a (insufficient history:" in block
    assert 'never "?"' in block
    assert "UNTRADEABLE_AT_SIZE" in block
    assert "LOCKUP WATCH" in block or "EDGAR confirm" in block
    assert "do not assume 180d" in block
    assert "gate 5 blackout" in block
    assert "bc-3c465873" in block
    assert "https://github.com/ElChopa11/market-memory/pull/59" in block
    assert "cursor/canonical-watchlist-monitor-5515" in block
    assert "PR when linked" not in block
    for item_id in OPEN_INCIDENTS:
        assert item_id in block
    assert "SRC-FRED-MISSING-ENV" in block
    assert "ELIGIBLE" in block
    universe = UNIVERSE.read_text(encoding="utf-8")
    assert "in_universe:" in universe
    assert "watch_only:" in universe
    assert "deferred_must_cut:" in universe
    assert "BTC" in universe
    for name in ("NVDA", "AVGO", "MSFT", "META", "JPM", "XOM"):
        assert name in universe
    for name in ("ETH", "UNI", "AAVE", "SMH", "XLF"):
        assert name in universe
    # Paper intake does not invent or expand membership.
    for invented in ("SPCX", "CBRS", "SAMSUN", "KOSDA", "PURR", "VVVUSD", "CHIPIUSD"):
        assert invented not in universe


def test_imp033_plan_points_at_imp020_and_sister() -> None:
    plan = PLAN.read_text(encoding="utf-8")
    assert "Do not reopen IMP-020" in plan
    assert "IMP-020-phase6c4-watchlist.md" in plan
    assert "0009-phase6c4-watchlist.md" in plan
    assert "docs/runbooks/watchlist.md" in plan
    assert "config/watchlist/monitor.yaml" in plan
    assert "Canonical watchlist monitor.yaml Principal lock" in plan
    assert "bc-3c465873" in plan
    assert "https://github.com/ElChopa11/market-memory/pull/59" in plan
    assert "cursor/canonical-watchlist-monitor-5515" in plan
    assert "Do not merge" in plan
    assert "PR when linked" not in plan
    assert "live_trading_enabled: false" in plan
    assert "No send" in plan or "no send" in plan.lower() or "holds Telegram" in plan
    assert "OPEN incidents untouched" in plan
    assert "NASDAQ:SPCX" in plan
    assert "NASDAQ:CBRS" in plan
    assert "semis_ai" in plan
    assert "HL:CHIP" in plan and "HL:VVV" in plan and "HL:PURR" in plan
    assert "SAMSUN" in plan and "KOSDA" in plan
    assert "Still unresolved" in plan and "SAMSUN, KOSDA." in plan
    assert "PURR, VVVUSD, CHIPIUSD" not in plan
    assert "Do not invent" in plan or "do not invent" in plan.lower()
    assert "NEW_LISTING" in plan
    assert "n/a (insufficient history:" in plan
    assert "EDGAR confirm" in plan
    assert "do not assume 180d" in plan
    assert "gate 5 blackout" in plan


def test_queue_helper_single_in_progress_no_auto_merge() -> None:
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ("IMP-033",)
    assert report.auto_merge is False
    assert report.auto_waive is False
    open_ids = {item.item_id for item in report.items if item.kind == "incident" and item.status == "OPEN"}
    eligible_ids = {item.item_id for item in report.items if item.kind == "incident" and item.status == "ELIGIBLE"}
    assert set(OPEN_INCIDENTS) <= open_ids
    assert set(ELIGIBLE_INCIDENTS) <= eligible_ids
    assert "SRC-FRED-MISSING-ENV" not in open_ids
    parsed = check_queue(QUEUE.read_text(encoding="utf-8"))
    assert parsed.in_progress == ("IMP-033",)
    assert not parsed.errors
