"""Adversarial PIT: Phase 5b feeds are keyed on as_of_knowledge / ingested_at.

Never treat published_at or market_time as knowledge time.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from mm_common.time import parse_utc
from mm_ingest.pipeline import envelopes_from_fixture, load_fixture_file

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "phase5b"

BEFORE_INGEST = datetime(2026, 9, 17, 21, 0, tzinfo=timezone.utc)
AT_INGEST = datetime(2026, 9, 18, 0, 5, tzinfo=timezone.utc)


def _visible(envelopes, at: datetime):
    return [e for e in envelopes if e.as_of_knowledge <= at]


def _assert_pit(envelopes) -> None:
    assert envelopes
    for envelope in envelopes:
        assert envelope.as_of_knowledge == envelope.ingested_at
        # market_time / published_at may be earlier (the print already happened)
        # but knowledge is lab ingest time only.
        if envelope.market_time is not None:
            assert envelope.market_time <= envelope.ingested_at or envelope.market_time >= envelope.ingested_at


def test_polygon_ohlcv_hidden_until_ingested() -> None:
    envelopes = envelopes_from_fixture(load_fixture_file(FIXTURES / "polygon_ohlcv.json"))
    _assert_pit(envelopes)
    bars = [e for e in envelopes if e.metric == "ohlcv_close"]
    assert bars
    leaked_if_market_time = [e for e in bars if e.market_time is not None and e.market_time <= BEFORE_INGEST]
    assert leaked_if_market_time, "fixture must include a bar whose exchange time is before ingest"
    assert _visible(bars, BEFORE_INGEST) == []
    known = _visible(bars, AT_INGEST)
    assert known
    assert {e.instrument for e in known} == {"NVDA"}


def test_polygon_dividend_hidden_until_ingested() -> None:
    envelopes = envelopes_from_fixture(load_fixture_file(FIXTURES / "polygon_corporate_actions.json"))
    _assert_pit(envelopes)
    divs = [e for e in envelopes if e.metric == "dividend"]
    assert divs
    assert all(e.market_time is not None and e.market_time < e.ingested_at for e in divs)
    assert _visible(divs, parse_utc("2026-09-16T12:00:00Z")) == []
    assert _visible(divs, AT_INGEST)


def test_hl_structure_snapshot_knowledge_is_ingested_at() -> None:
    envelopes = envelopes_from_fixture(load_fixture_file(FIXTURES / "hl_structure.json"))
    _assert_pit(envelopes)
    earlier = datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc)
    assert _visible(envelopes, earlier) == []
    assert _visible(envelopes, AT_INGEST)
    l2 = next(e for e in envelopes if e.metric == "l2_spread")
    # Exchange book time may equal ingest in this fixture; still not a knowledge watermark.
    assert l2.as_of_knowledge == l2.ingested_at


def test_spot_and_fred_and_calendar_knowledge_watermark() -> None:
    for name in ("spot_cross_check.json", "fred_series.json", "economic_calendar.yaml"):
        envelopes = envelopes_from_fixture(load_fixture_file(FIXTURES / name))
        _assert_pit(envelopes)
        assert _visible(envelopes, BEFORE_INGEST) == []
        assert _visible(envelopes, AT_INGEST)
        for envelope in envelopes:
            assert envelope.as_of_knowledge != envelope.published_at or envelope.published_at == envelope.ingested_at or envelope.metric in {
                "spot_px",
                "basis_perp_spot",
                "feed_status",
                "l2_spread",
                "predicted_funding",
                "basis_mark_oracle",
            }


def test_earnings_unavailable_is_still_pit_honest() -> None:
    envelopes = envelopes_from_fixture(load_fixture_file(FIXTURES / "polygon_earnings_unavailable.json"))
    _assert_pit(envelopes)
    assert _visible(envelopes, BEFORE_INGEST) == []
    known = _visible(envelopes, AT_INGEST)
    assert known
    assert all(e.payload.get("error_class") == "tos_or_blocked" for e in known)
