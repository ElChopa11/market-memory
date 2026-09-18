"""IMP-007: dedicated crypto / equities thesis cards."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from mm_research_kit.markdown import get_field
from mm_research_kit.quant_review.language import language_violations
from mm_research_kit.quant_review.models import VERDICT_VALUES
from mm_research_kit.thesis_cards import (
    CRYPTO_CARD,
    CRYPTO_PERPS,
    DEFERRED_CRYPTO,
    DEFERRED_EQUITIES,
    EQUITIES,
    EQUITIES_CARD,
    IN_UNIVERSE_CRYPTO,
    IN_UNIVERSE_EQUITIES,
    LOCKED_UNIVERSE_VERSION,
    WATCH_ONLY_CRYPTO,
    WATCH_ONLY_EQUITIES,
    attach_desk_thesis_card,
    membership_for,
    plan_desk_card,
)
from mm_research_kit.workspace import ThesisSpec, create_thesis_from_intent

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates"

REQUIRED_CARD_FIELDS = (
    "Thesis id",
    "Status / version",
    "Desk",
    "Author role",
    "Instrument",
    "Principal membership",
    "Working Quant verdict",
    "Knowledge watermark (as_of_knowledge)",
    "Independent Skeptic review required",
    "Independent Skeptic verdict",
)

REQUIRED_SECTIONS = (
    "Non-goals",
    "Hypothesis",
    "Evidence",
    "Single invalidation",
    "Independent Skeptic stub",
)


def test_queue_hygiene_imp007_templates_closed() -> None:
    text = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    assert "| **ID** | IMP-007 |" in text
    assert re.search(r"### IMP-007.*?(?:\| \*\*Status\*\* \| DONE \|)", text, re.S)
    assert "| Dedicated crypto / equity thesis-card templates |" not in text
    for item in ("IMP-004", "IMP-005", "IMP-006", "IMP-007"):
        assert re.search(rf"### {item} ", text)
    assert re.search(r"### IMP-007.*?(?:\| \*\*Status\*\* \| DONE \|)", text, re.S)


def test_locked_membership_pin_matches_universe_yaml() -> None:
    universe = yaml.safe_load((ROOT / "config" / "universe.yaml").read_text(encoding="utf-8"))
    assert universe["version"] == LOCKED_UNIVERSE_VERSION
    assert tuple(universe["crypto_perps"]) == CRYPTO_PERPS
    assert tuple(universe["equities"]) == EQUITIES
    assert tuple(universe["in_universe"]["crypto_perps"]) == IN_UNIVERSE_CRYPTO
    assert tuple(universe["in_universe"]["equities"]) == IN_UNIVERSE_EQUITIES
    assert tuple(universe["watch_only"]["crypto_perps"]) == WATCH_ONLY_CRYPTO
    assert tuple(universe["watch_only"]["equities"]) == WATCH_ONLY_EQUITIES
    assert tuple(universe["deferred_must_cut"]["crypto"]) == DEFERRED_CRYPTO
    assert tuple(universe["deferred_must_cut"]["equities"]) == DEFERRED_EQUITIES
    assert "active_calls" not in universe


def test_desk_card_templates_exist_and_are_language_clean() -> None:
    for name in (CRYPTO_CARD, EQUITIES_CARD):
        path = TEMPLATES / name
        text = path.read_text(encoding="utf-8")
        assert language_violations(text) == []
        for field in REQUIRED_CARD_FIELDS:
            assert get_field(text, field) is not None, f"{name} missing {field}"
        for heading in REQUIRED_SECTIONS:
            assert f"## {heading}" in text, f"{name} missing ## {heading}"
        for verdict in VERDICT_VALUES:
            assert verdict in text
        assert "`in_universe`" in text
        assert "`watch_only`" in text
        assert "as_of_knowledge" in text
        assert "No sizing." in text
        assert "No execution" in text
        assert "no investment-call language" in text.lower() or "No investment-call language." in text
        assert "Not a trade instruction" in text
        assert "pending (not claimed as pass)" in text
        assert "published_at" in text
        assert "market_time" in text


def test_membership_lookup_uses_imp005_keys() -> None:
    assert membership_for("BTC") == "in_universe"
    assert membership_for("ETH") == "watch_only"
    assert membership_for("NVDA") == "in_universe"
    assert membership_for("SMH") == "watch_only"
    assert membership_for("HYPE") == "deferred_must_cut"
    assert membership_for("GLD") == "deferred_must_cut"
    assert membership_for("UNKNOWN") == "not_in_membership"
    crypto = plan_desk_card("btc")
    assert crypto is not None and crypto.template == CRYPTO_CARD
    equity = plan_desk_card("NVDA")
    assert equity is not None and equity.template == EQUITIES_CARD
    assert plan_desk_card("QQQ") is None


def test_create_thesis_copies_crypto_card(tmp_path: Path) -> None:
    created = create_thesis_from_intent(
        research_root=tmp_path / "research",
        templates_root=TEMPLATES,
        spec=ThesisSpec(goal="BTC funding fade after crowding", owner="Research", instrument="BTC"),
        repo_root=tmp_path,
    )
    card = created.path / CRYPTO_CARD
    assert card.is_file()
    assert not (created.path / EQUITIES_CARD).is_file()
    text = card.read_text(encoding="utf-8")
    assert get_field(text, "Principal membership") == "in_universe"
    assert get_field(text, "Desk") == "Research (Investment Research) / crypto sleeve"
    assert get_field(text, "Instrument") == "BTC"
    assert get_field(text, "Working Quant verdict") == "unset"
    assert language_violations(text) == []


def test_create_thesis_copies_equities_card_for_watch_only(tmp_path: Path) -> None:
    created = create_thesis_from_intent(
        research_root=tmp_path / "research",
        templates_root=TEMPLATES,
        spec=ThesisSpec(goal="SMH overlap vs NVDA+AVGO", owner="Research", instrument="SMH"),
        repo_root=tmp_path,
    )
    card = created.path / EQUITIES_CARD
    assert card.is_file()
    assert not (created.path / CRYPTO_CARD).is_file()
    text = card.read_text(encoding="utf-8")
    assert get_field(text, "Principal membership") == "watch_only"
    assert get_field(text, "Desk") == "Research (Investment Research) / equities sleeve"
    assert "lab equities reclaim-screen" in text
    assert language_violations(text) == []


def test_unknown_instrument_does_not_invent_a_desk_card(tmp_path: Path) -> None:
    created = create_thesis_from_intent(
        research_root=tmp_path / "research",
        templates_root=TEMPLATES,
        spec=ThesisSpec(goal="outside locked membership", owner="Research", instrument="QQQ"),
        repo_root=tmp_path,
    )
    assert (created.path / "thesis.md").is_file()
    assert not (created.path / CRYPTO_CARD).is_file()
    assert not (created.path / EQUITIES_CARD).is_file()
    assert (
        attach_desk_thesis_card(
            workspace=created.path,
            templates_root=TEMPLATES,
            instrument="QQQ",
            slug=created.slug,
            status="in_research",
            author_role="Research",
        )
        is None
    )
