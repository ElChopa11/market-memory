"""IMP-008: locked-membership Quant RESEARCH_PRIORITY pass (2026-09-18)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from mm_research_kit.quant_review.language import assert_language_clean, language_violations
from mm_research_kit.quant_review.locked_membership import (
    DEFERRED_MUST_CUT,
    LOCKED_BOARD_NAMES,
    LOCKED_IN_UNIVERSE,
    LOCKED_UNIVERSE_CONFIG,
    LOCKED_WATCH_ONLY,
    REVIEW_DATE,
    assert_locked_universe_pins,
    build_locked_membership_board,
    build_locked_membership_cards,
    expected_counts,
)
from mm_research_kit.quant_review.models import QuantReasonCode, QuantVerdict
from mm_research_kit.quant_review.universe import universe_from_mapping

ROOT = Path(__file__).resolve().parents[2]
BOARD = ROOT / "research" / "quant" / REVIEW_DATE / "quant-review-board.md"
META = ROOT / "research" / "quant" / REVIEW_DATE / "run_meta.json"
CARDS = ROOT / "research" / "quant" / REVIEW_DATE / "cards"


def test_locked_review_universe_matches_membership_and_excludes_must_cuts() -> None:
    assert_locked_universe_pins(ROOT)
    membership = yaml.safe_load((ROOT / "config" / "universe.yaml").read_text())
    locked = universe_from_mapping(yaml.safe_load((ROOT / LOCKED_UNIVERSE_CONFIG).read_text()))
    assert tuple(spec.symbol for spec in locked.instruments) == LOCKED_BOARD_NAMES
    assert locked.kind == "quant_review_locked_membership"
    assert locked.status == "locked_membership"
    deferred = set(membership["deferred_must_cut"]["crypto"]) | set(membership["deferred_must_cut"]["equities"])
    assert deferred == set(DEFERRED_MUST_CUT)
    assert set(spec.symbol for spec in locked.instruments).isdisjoint(deferred)
    assert set(LOCKED_IN_UNIVERSE) == set(membership["in_universe"]["crypto_perps"]) | set(
        membership["in_universe"]["equities"]
    )
    assert set(LOCKED_WATCH_ONLY) == set(membership["watch_only"]["crypto_perps"]) | set(
        membership["watch_only"]["equities"]
    )


def test_committed_board_covers_locked_names_only() -> None:
    text = BOARD.read_text(encoding="utf-8")
    meta = json.loads(META.read_text(encoding="utf-8"))
    cards = build_locked_membership_cards()
    assert meta["review_date"] == REVIEW_DATE
    assert set(meta["verdicts"]) == set(LOCKED_BOARD_NAMES)
    assert set(meta["verdicts"]).isdisjoint(set(DEFERRED_MUST_CUT))
    assert {p.stem for p in CARDS.glob("*.md")} == set(LOCKED_BOARD_NAMES)
    for name in DEFERRED_MUST_CUT:
        assert (CARDS / f"{name}.md").is_file() is False
        assert f"| {name} |" not in text
    for name in LOCKED_BOARD_NAMES:
        assert (CARDS / f"{name}.md").is_file()
        assert f"| {name} |" in text
    for card in cards:
        assert meta["verdicts"][card.instrument]["verdict"] == card.verdict
        committed = (CARDS / f"{card.instrument}.md").read_text(encoding="utf-8")
        assert f"**Verdict:** {card.verdict}" in committed
        assert "Independent Skeptic verdict:** pending" in committed


def test_zero_research_priority_and_expected_counts() -> None:
    cards = build_locked_membership_cards()
    counts = expected_counts(cards)
    assert counts.get("RESEARCH_PRIORITY", 0) == 0
    assert counts == {"MONITOR": 2, "DEFER": 6, "INSUFFICIENT_DATA": 4}
    by_name = {card.instrument: card.verdict for card in cards}
    assert by_name["ETH"] == QuantVerdict.MONITOR.value
    assert by_name["UNI"] == QuantVerdict.MONITOR.value
    assert by_name["AAVE"] == QuantVerdict.DEFER.value
    assert by_name["BTC"] == QuantVerdict.DEFER.value
    assert by_name["NVDA"] == QuantVerdict.DEFER.value
    assert by_name["JPM"] == QuantVerdict.DEFER.value
    assert by_name["SMH"] == QuantVerdict.DEFER.value
    assert by_name["XLF"] == QuantVerdict.DEFER.value
    assert by_name["AVGO"] == QuantVerdict.INSUFFICIENT_DATA.value
    assert by_name["MSFT"] == QuantVerdict.INSUFFICIENT_DATA.value
    assert by_name["META"] == QuantVerdict.INSUFFICIENT_DATA.value
    assert by_name["XOM"] == QuantVerdict.INSUFFICIENT_DATA.value
    text = BOARD.read_text(encoding="utf-8")
    assert "RESEARCH_PRIORITY (≤3; 0 this review)" in text
    assert "none this review" in text
    meta = json.loads(META.read_text(encoding="utf-8"))
    assert meta["desk_pass"]["research_priority_names"] == []
    assert meta["desk_pass"]["counts"]["MONITOR"] == 2


def test_uni_monitor_is_not_a_narrative_upgrade() -> None:
    uni = (CARDS / "UNI.md").read_text(encoding="utf-8")
    aave = (CARDS / "AAVE.md").read_text(encoding="utf-8")
    assert "**Verdict:** MONITOR" in uni
    assert "SEC PR 2026-90" in uni
    assert "permissioned" in uni.lower()
    assert "90-day fishing" in uni
    assert "**Verdict:** DEFER" in aave
    assert "utilization baseline" in aave.lower()
    assert QuantReasonCode.EVENT_RISK.value in uni
    board = build_locked_membership_board()
    uni_card = next(c for c in board.cards if c.instrument == "UNI")
    assert uni_card.verdict == QuantVerdict.MONITOR.value
    assert uni_card.promotion.all_met is False
    assert "not claimed as pass" in uni


def test_committed_artifacts_match_builder_and_are_language_clean() -> None:
    result = build_locked_membership_board()
    committed = BOARD.read_text(encoding="utf-8")
    assert committed == result.board_markdown
    blob = committed + "\n" + "\n".join((CARDS / f"{name}.md").read_text(encoding="utf-8") for name in LOCKED_BOARD_NAMES)
    assert language_violations(blob) == []
    assert_language_clean(blob)
    lowered = blob.lower()
    assert "active call" not in lowered
    assert re.search(r"\bbuy\b", lowered) is None
    assert re.search(r"\bsell\b", lowered) is None
    assert re.search(r"\bmake\b", lowered) is None
    assert "high confidence" not in lowered
    assert "position size" not in lowered


def test_queue_hygiene_imp007_done_imp008_single_thread() -> None:
    text = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    assert "| **ID** | IMP-007 |" in text
    assert "| **ID** | IMP-008 |" in text
    assert "do not merge" not in text.lower()
    in_progress = re.findall(r"\| \*\*Status\*\* \| IN_PROGRESS \|", text)
    assert in_progress == []
    # IMP-007 and IMP-008 blocks are DONE; no implementation item is IN_PROGRESS.
    assert re.search(r"### IMP-007.*?(?:\| \*\*Status\*\* \| DONE \|)", text, re.S)
    assert re.search(r"### IMP-008.*?(?:\| \*\*Status\*\* \| DONE \|)", text, re.S)
    assert "IMP-000–IMP-008 are `DONE`" in text
