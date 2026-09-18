"""Adversarial PIT: listings key off as_of_knowledge, never invented prints."""

from __future__ import annotations

from pathlib import Path

from mm_common.time import parse_utc
from mm_desks.listings import run_listings_from_fixture

ROOT = Path(__file__).resolve().parents[2]
LISTING_DAY = ROOT / "tests" / "fixtures" / "phase6d" / "listing_day.json"
WATERMARK = parse_utc("2026-09-18T00:05:00Z")


def test_listings_ignores_future_deal_and_bar() -> None:
    result = run_listings_from_fixture(LISTING_DAY, repo_root=ROOT)
    assert result.as_of_knowledge == WATERMARK
    instruments = {idea.instrument for idea in result.snapshot.ideas}
    assert "FUTUREX" not in instruments
    crcl = next(idea for idea in result.snapshot.ideas if idea.instrument == "CRCL")
    assert crcl.track.day1_close is not None
    assert crcl.track.day1_close < 50
    assert crcl.deal.as_of_knowledge <= WATERMARK
    assert crcl.deal.ingested_at <= WATERMARK
    for event in result.snapshot.index_events:
        assert event.as_of_knowledge <= WATERMARK
        assert event.ingested_at <= WATERMARK
        assert event.instrument != "GHOST"
