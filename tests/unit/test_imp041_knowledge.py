"""IMP-041: Principal-locked desk knowledge base exists and parses as markdown."""

from __future__ import annotations

from pathlib import Path

from mm_desks.queue import can_start, load_queue

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "config" / "knowledge"


def _markdown_headings(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    assert text.strip(), path
    headings = [line.lstrip("#").strip() for line in text.splitlines() if line.startswith("#")]
    assert headings, f"{path} has no markdown headings"
    return headings


def test_knowledge_files_exist_and_parse_as_markdown() -> None:
    readme = KNOWLEDGE / "README.md"
    priors = KNOWLEDGE / "priors.md"
    failures = KNOWLEDGE / "failure-modes.md"
    lessons = KNOWLEDGE / "house-lessons.md"
    for path in (readme, priors, failures, lessons):
        assert path.is_file(), path

    prior_heads = _markdown_headings(priors)
    assert "Priors" in prior_heads
    assert "Strong" in prior_heads
    assert "Moderate" in prior_heads
    assert "No comparable evidence" in prior_heads
    prior_text = priors.read_text(encoding="utf-8")
    for token in (
        "momentum",
        "PEAD",
        "Index inclusion",
        "IPO lockup",
        "Short-term reversal",
        "Carry",
        "Value / quality",
        "Vol clustering",
        "Seasonality",
        "Overnight / intraday",
        "FVG",
        "Supply–demand",
        "Indicator combos",
        "Raises prior probability",
        "MORE evidence",
    ):
        assert token in prior_text, token
    assert "Not a trigger" in prior_text
    assert "Not a size" in prior_text

    fail_text = failures.read_text(encoding="utf-8")
    fail_heads = _markdown_headings(failures)
    assert "Failure modes" in fail_heads
    for mode in (
        "Look-ahead",
        "Survivorship",
        "Multiple testing",
        "Regime-fitting",
        "Cost omission",
        "Overlap",
        "Sample manufacture",
        "Metric substitution",
        "Narrative fit",
    ):
        assert any(mode in h for h in fail_heads), mode
        assert mode.lower().split()[0] in fail_text.lower()
    assert "What it looks like" in fail_text
    assert "Which test catches it" in fail_text
    assert fail_text.count("none yet — fill from a dated post-mortem + run_id") >= 9

    lesson_text = lessons.read_text(encoding="utf-8")
    for token in (
        "2026-09-12",
        "R divergence",
        "ETF flow invalidator",
        "0W–1L stand-down",
        "2026-09-18",
        "FRED 10Y invented",
        "2026-09-19",
        "never-fired",
        "miss detector",
        "secret-request",
        "Secrets card",
        "second",
        "credential-handling path",
        "not by an external breach",
        "no agent process handles it",
        "BotFather",
        "Principal clipboard",
        "No card",
        "no widget secret field",
        "no chat paste",
        "no secret-request",
        "getChat",
        "supergroup",
        "Controls on a path that never executes are not controls",
        "Absence of output is not evidence of absence of windows",
        "Instrumentation that records only successes cannot detect silence",
        "server-kept",
        "not diffable",
        "uncontrolled surface",
        "Step 3",
        "panel read-back",
        "write API",
        "Control boundary around own code misses other publishers",
        "membership / credential / webhook",
        "Hybrid single-exit",
        "Desk bots must not be Telegram members",
        "compounds from post-mortems",
    ):
        assert token in lesson_text, token

    usage = readme.read_text(encoding="utf-8")
    assert "Cached prompt prefix" in usage
    assert "never triggers or sizes" in usage
    assert "must label it" in usage
    assert "house lesson wins over a prior" in usage
    assert "date + `run_id`" in usage


def test_queue_imp041_done_does_not_take_implementation_slot() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-041" in line and "DONE" in line for line in board_lines)
    assert not any("IMP-041" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-047" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-040" in line and "DONE" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1** (IMP-047)" in queue
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    assert (ROOT / "ops" / "plans" / "IMP-041-desk-knowledge-base.md").is_file()
    report = load_queue(ROOT)
    assert report.ok, report.errors
    assert report.in_progress == ("IMP-047",)
    assert report.auto_merge is False
    assert report.auto_waive is False
    ok, reason = can_start("IMP-041", report)
    assert ok is False
    assert "DONE" in reason
