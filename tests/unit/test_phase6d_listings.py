"""Phase 6d listings / IPO screen: Research sleeve, PIT, closed verdicts, no sixth desk."""

from __future__ import annotations

from pathlib import Path

import pytest

from mm_common.naming import LISTINGS, PUBLISHING_DESKS, RESEARCH, UnknownNameError, desk_display, require_publishing_desk, sleeve_display
from mm_desks.listings import ENGINE_VERSION, NO_INVENTED_MATH, run_listings_from_fixture
from mm_listings.config import load_listings_config
from mm_research_kit.quant_review.language import language_violations

ROOT = Path(__file__).resolve().parents[2]
LISTING_DAY = ROOT / "tests" / "fixtures" / "phase6d" / "listing_day.json"
NO_LISTING = ROOT / "tests" / "fixtures" / "phase6d" / "no_listing.json"
MISSING = ROOT / "tests" / "fixtures" / "phase6d" / "missing_feed.json"


def test_listings_is_research_sleeve_not_a_sixth_desk() -> None:
    assert PUBLISHING_DESKS == ("intel", "research", "quant", "ic_risk", "ops")
    with pytest.raises(UnknownNameError):
        require_publishing_desk("listings")
    assert sleeve_display(LISTINGS).startswith("Research")
    cfg = load_listings_config(ROOT)
    assert cfg.desk == RESEARCH
    assert cfg.promote is False
    assert cfg.llm is False
    assert cfg.send is False


def test_listing_day_is_deterministic_and_research_envelope() -> None:
    first = run_listings_from_fixture(LISTING_DAY, repo_root=ROOT)
    second = run_listings_from_fixture(LISTING_DAY, repo_root=ROOT)
    assert first.content_hash == second.content_hash
    assert first.run_id == second.run_id
    assert len(first.content_hash) == 64
    assert first.output.slug == RESEARCH
    assert first.output.desk == desk_display(RESEARCH)
    assert first.output.op == "observation"
    assert first.envelopes[0].desk == RESEARCH
    assert first.envelopes[0].channel == "desk.research.output"
    assert first.engine_version == ENGINE_VERSION
    assert first.llm_calls == 0


def test_listing_day_hides_lookahead_and_never_invents() -> None:
    result = run_listings_from_fixture(LISTING_DAY, repo_root=ROOT)
    instruments = {idea.instrument for idea in result.snapshot.ideas}
    assert "CRCL" in instruments
    assert "NEWCO" in instruments
    assert "FUTUREX" not in instruments
    index_names = {row.instrument for row in result.snapshot.index_events}
    assert "NEWCO" in index_names
    assert "GHOST" not in index_names
    crcl = next(idea for idea in result.snapshot.ideas if idea.instrument == "CRCL")
    assert crcl.quant_verdict in {"DEFER", "MONITOR", "INSUFFICIENT_DATA", "REJECT", "RESEARCH_PRIORITY"}
    assert crcl.trade_math_hash == "inherited-from-quant-crcl-fixture-hash"
    assert crcl.deal.offer_price == 20.0
    lookahead_print = 99.5
    assert crcl.track.day1_close != lookahead_print
    newco = next(idea for idea in result.snapshot.ideas if idea.instrument == "NEWCO")
    assert newco.quant_verdict == "INSUFFICIENT_DATA"
    assert newco.track.offer_price is None
    assert "offer_price" in newco.track.gaps
    assert result.snapshot.base_rates.claimed is False
    assert result.snapshot.base_rates.n < result.snapshot.base_rates.n_min
    assert "unavailable" in result.markdown
    assert language_violations(result.markdown) == []
    lowered = result.markdown.lower()
    assert "buy" not in lowered
    assert "sell" not in lowered
    assert "active call" not in lowered


def test_no_listing_day_is_complete_with_zero_llm() -> None:
    result = run_listings_from_fixture(NO_LISTING, repo_root=ROOT)
    assert result.snapshot.ideas == ()
    assert result.snapshot.index_events == ()
    assert result.status == "OK"
    assert result.completeness == 100.0
    assert result.llm_calls == 0
    assert result.as_public_dict()["n_llm_calls"] == 0
    assert "no listing day" in result.markdown.lower() or "no listing" in " ".join(result.notes).lower()


def test_missing_feed_degrades_and_does_not_invent() -> None:
    result = run_listings_from_fixture(MISSING, repo_root=ROOT)
    assert result.snapshot.ideas == ()
    assert "listings_feed" in result.gaps
    assert result.status == "DEGRADED"
    assert result.completeness == 0.0
    assert "unavailable" in result.markdown.lower()


def test_ic_gates_required_and_math_not_invented() -> None:
    result = run_listings_from_fixture(LISTING_DAY, repo_root=ROOT)
    payload = result.output.payload
    assert payload["ic_gates"]["skeptic_required"] is True
    assert payload["ic_gates"]["risk_required"] is True
    assert payload["ic_gates"]["self_approve"] is False
    assert payload["ic_gates"]["paper_open"] is False
    assert payload["promote"] is False
    assert payload["llm"] is False
    newco = next(idea for idea in result.snapshot.ideas if idea.instrument == "NEWCO")
    assert newco.trade_math_hash is None
    assert NO_INVENTED_MATH in result.markdown or any(NO_INVENTED_MATH in n for n in result.notes)
    assert "R_target" not in result.markdown
    assert "size_pct" not in result.markdown
    assert result.output.universe == "screen_only"
