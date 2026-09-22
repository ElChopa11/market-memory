"""Principal FIX ORDER after IC #79: Attack 5+A8, A9 close, queued remainder."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import load_queue

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "research" / "base-rates"
PHASE1 = BASE / "phase1-2026-09-19.md"
FOLLOW = BASE / "phase1-2026-09-19-ic-follow-up.md"
ATTACK = BASE / "phase1-2026-09-19-ic-attack.md"
ACTIONS = BASE / "phase1-2026-09-19-principal-actions.md"


def test_phase1_banner_quotes_ic_distinction_and_keeps_fail() -> None:
    text = PHASE1.read_text(encoding="utf-8")
    assert "IC Gate 1" in text
    assert "FAIL" in text
    assert "descriptive coin-flip mixture" in text
    assert "PROVISIONAL" in text
    assert "**NOT** a strategy hurdle" in text or "NOT a strategy hurdle" in text
    assert "must beat this after costs" not in text.lower()
    assert "median headline" in text
    assert "1-bar median" in text
    assert "10-bar median" in text
    assert "| ticker | n | median | mean |" in text
    assert "| ticker | n | mean | median |" not in text
    # SOL/DOGE/MSTR: means positive, medians ≤0 in the committed dump.
    assert "SOLUSD 1-bar median -0.015% (mean 0.338%)" in text
    assert "DOGEUSD 1-bar median -0.075% (mean 0.439%)" in text
    assert "MSTR 1-bar median -0.343% (mean 0.157%)" in text


def test_ic_a9_closed_stale_vs_81_fail_intact() -> None:
    attack = ATTACK.read_text(encoding="utf-8")
    follow = FOLLOW.read_text(encoding="utf-8")
    actions = ACTIONS.read_text(encoding="utf-8")
    assert "## Verdict: **FAIL**" in attack
    assert "CLOSED stale" in attack
    assert "#81" in attack
    assert "Do not soften FAIL" in follow or "do not soften FAIL" in follow.lower()
    assert "descriptive coin-flip mixture" in follow
    assert "NOT** a strategy hurdle" in follow or "NOT a strategy hurdle" in follow
    assert "Attack A9 CLOSED stale" in actions or "A9 CLOSED stale" in actions
    assert "#81" in actions
    assert "FAIL" in actions


def test_queue_ic_attacks_backlog_not_in_progress() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    for item_id in ("IMP-052", "IMP-053", "IMP-054", "IMP-055"):
        assert any(item_id in line and "BACKLOG" in line for line in board_lines), item_id
        assert not any(item_id in line and "IN_PROGRESS" in line for line in board_lines), item_id
    assert "`IN_PROGRESS` count: **0**" in queue
    assert "Intel depth" in queue
    assert "research sprint" in queue
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ()
