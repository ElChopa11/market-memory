"""IMP-032: call-card priority language matches Quant SoT 2026-09-18 (#38)."""

from __future__ import annotations

import re
from pathlib import Path

from mm_research_kit.quant_review.language import language_violations
from mm_research_kit.quant_review.locked_membership import (
    DEFERRED_MUST_CUT,
    LOCKED_BOARD_NAMES,
    LOCKED_IN_UNIVERSE,
    LOCKED_WATCH_ONLY,
)

ROOT = Path(__file__).resolve().parents[2]
CARDS = ROOT / "research" / "queue" / "UNIVERSE-20260917-call-cards.md"
BOARD = ROOT / "research" / "quant" / "2026-09-18" / "quant-review-board.md"
QUEUE = ROOT / "ops" / "improvement-queue.md"
UNIVERSE = ROOT / "config" / "universe.yaml"
LIVE = ROOT / "config" / "risk" / "environments" / "live.yaml"

QUANT_SOT: dict[str, str] = {
    "BTC": "DEFER",
    "NVDA": "DEFER",
    "JPM": "DEFER",
    "AAVE": "DEFER",
    "SMH": "DEFER",
    "XLF": "DEFER",
    "ETH": "MONITOR",
    "UNI": "MONITOR",
    "AVGO": "INSUFFICIENT_DATA",
    "MSFT": "INSUFFICIENT_DATA",
    "META": "INSUFFICIENT_DATA",
    "XOM": "INSUFFICIENT_DATA",
}

_SECTION = re.compile(
    r"^## (?P<n>\d+)\. (?P<sym>[A-Z]+) \(.*?\) — (?P<title>.*?)$\n"
    r"(?P<body>.*?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)
_EXPECTATION = re.compile(r"^1\) \*\*Expectation\*\* — (?P<line>.+)$", re.MULTILINE)
_VERDICT = re.compile(r"Quant SoT \*\*(RESEARCH_PRIORITY|MONITOR|DEFER|REJECT|INSUFFICIENT_DATA)\*\*")


def _sections() -> dict[str, dict[str, str]]:
    text = CARDS.read_text(encoding="utf-8")
    found: dict[str, dict[str, str]] = {}
    for match in _SECTION.finditer(text):
        found[match.group("sym")] = {
            "n": match.group("n"),
            "title": match.group("title"),
            "body": match.group("body"),
        }
    return found


def test_locked_universe_unchanged_and_no_new_names() -> None:
    text = CARDS.read_text(encoding="utf-8")
    sections = _sections()
    assert set(sections) == set(LOCKED_BOARD_NAMES) == set(QUANT_SOT)
    assert len(sections) == 12
    for cut in DEFERRED_MUST_CUT:
        assert re.search(rf"^## \d+\. {cut} \(", text, re.MULTILINE) is None
    universe = UNIVERSE.read_text(encoding="utf-8")
    assert re.search(r"^in_universe:", universe, re.MULTILINE)
    assert re.search(r"^active_calls:", universe, re.MULTILINE) is None
    live = LIVE.read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live


def test_each_card_expectation_matches_quant_sot() -> None:
    sections = _sections()
    assert set(sections) == set(QUANT_SOT)
    for symbol, expected in QUANT_SOT.items():
        body = sections[symbol]["body"]
        expect_line = _EXPECTATION.search(body)
        assert expect_line, f"{symbol} missing Expectation line"
        line = expect_line.group("line")
        verdict = _VERDICT.search(line)
        assert verdict, f"{symbol} Expectation does not lead with Quant SoT: {line}"
        assert verdict.group(1) == expected, f"{symbol}: {verdict.group(1)} != {expected}"
        lowered = line.lower()
        # Priority language must not stay "conditional" once Quant SoT is named.
        assert "conditional" not in lowered, f"{symbol} still says conditional: {line}"
        assert "paper only" in lowered
        assert "do not size" in lowered


def test_defer_insufficient_and_monitor_groups() -> None:
    sections = _sections()
    for name in ("BTC", "NVDA", "JPM"):
        assert "DEFER" in sections[name]["title"] or "DEFER" in sections[name]["body"]
        line = _EXPECTATION.search(sections[name]["body"]).group("line")
        assert "DEFER" in line
        assert "INSUFFICIENT_DATA" not in line
        assert "conditional" not in line.lower()
    for name in ("AVGO", "MSFT", "META", "XOM"):
        line = _EXPECTATION.search(sections[name]["body"]).group("line")
        assert "INSUFFICIENT_DATA" in line
        assert "conditional" not in line.lower()
    for name in ("ETH", "UNI"):
        line = _EXPECTATION.search(sections[name]["body"]).group("line")
        assert "MONITOR" in line
    for name in ("AAVE", "SMH", "XLF"):
        line = _EXPECTATION.search(sections[name]["body"]).group("line")
        assert "DEFER" in line
        assert "Quant SoT **MONITOR**" not in line


def test_header_names_quant_board_as_sot_not_post_11_revise() -> None:
    text = CARDS.read_text(encoding="utf-8")
    header = text.split("## 1.", 1)[0]
    assert "research/quant/2026-09-18/quant-review-board.md" in header
    assert "#38" in header
    assert "paper only" in header.lower()
    assert "DO NOT SIZE" in header
    assert "post-#11 revise language as current priority" in header
    assert "**Quant SoT**" in header
    summary = text.split("## Quant SoT summary", 1)[1]
    assert "RESEARCH_PRIORITY" in summary
    assert "**0**" in summary.split("RESEARCH_PRIORITY", 1)[1][:80]


def test_hl_stamps_quarantined_appendix_do_not_size() -> None:
    text = CARDS.read_text(encoding="utf-8")
    body, appendix = text.split("## Appendix — stale HL lab snapshot", 1)
    assert "DO NOT SIZE" in appendix
    assert "DO NOT TREAT AS LIVE" in appendix
    assert "2026-09-17T00:28:03Z" in appendix
    for stamp in ("$3.05B", "$2.90B", "$1.37B", "$2.37B", "$31.2M", "$12.9M"):
        assert stamp in appendix, stamp
        assert stamp not in body, f"{stamp} leaked into card bodies"
    assert "dayNtl" not in body
    assert "dayNtlVlm" in appendix
    # Card bodies may mention OI collapse as an invalidation mechanic, but not live OI$ stamps.
    assert "OI$ ~" not in body
    assert "OI$ declining" in body
    for section in _sections().values():
        assert "see [appendix]" in section["body"] or "DO NOT SIZE" in section["body"]


def test_language_gate_no_active_call_buy_sell() -> None:
    text = CARDS.read_text(encoding="utf-8")
    hits = language_violations(text)
    # Historical filename / IMP-005 rename notes may mention active_calls as a former key.
    # Ban live recommendation phrasing in Expectation lines and summary.
    for section in _sections().values():
        line = _EXPECTATION.search(section["body"]).group("line")
        assert language_violations(line) == [], line
        lowered = line.lower()
        assert "active call" not in lowered
        assert re.search(r"\bbuy\b", lowered) is None
        assert re.search(r"\bsell\b", lowered) is None
        assert "high confidence" not in lowered
    summary = text.split("## Quant SoT summary", 1)[1].split("## Appendix", 1)[0]
    assert "active call" not in summary.lower()
    assert re.search(r"\bbuy\b", summary.lower()) is None
    assert re.search(r"\bsell\b", summary.lower()) is None
    # Full-file gate: allow citing the retired active_calls yaml key in the membership header.
    unexpected = [h for h in hits if h not in {"active-call language"}]
    assert unexpected == [], unexpected
    header = text.split("## 1.", 1)[0]
    assert "former `active_calls`" in header


def test_membership_partitions_not_verdicts() -> None:
    text = CARDS.read_text(encoding="utf-8")
    for name in LOCKED_IN_UNIVERSE:
        assert name in text
    for name in LOCKED_WATCH_ONLY:
        assert name in text
    assert "Membership ≠ Quant verdict" in text or "membership ≠ Quant verdict" in text.lower()
    board = BOARD.read_text(encoding="utf-8")
    assert "**Verdict counts:** DEFER=6, INSUFFICIENT_DATA=4, MONITOR=2" in board


def test_queue_imp031_done_imp032_single_thread_open_incidents() -> None:
    queue = QUEUE.read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-031" in line and "DONE" in line for line in board_lines)
    assert any("#56" in line for line in board_lines if "IMP-031" in line)
    assert any("IMP-032" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-031" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-031" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-032" in line and "IN_PROGRESS" in line for line in board_lines)
    in_progress = re.findall(r"\| \*\*Status\*\* \| IN_PROGRESS \|", queue)
    assert in_progress == []
    assert "`IN_PROGRESS` count: **0**" in queue
    for item_id in ("SCHED-001", "BRIEF-TAG-20260918", "SRC-STOOQ-404", "SRC-FRED-MISSING-ENV"):
        assert item_id in queue
    assert queue.count("| **Status** | OPEN |") >= 4
    assert "sydney-morning-digest-8am" in queue
    assert (ROOT / "ops" / "plans" / "IMP-032-call-card-language-debt.md").is_file()
    live = LIVE.read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
