"""Live macro fetchers degrade when keys/HTTP fail; never require secrets."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from mm_briefing.fetchers import LiveMacroFetcher, empty_snapshot, fetcher_for_mode


AS_OF = datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc)
PRIOR = datetime(2026, 3, 9, 20, 0, tzinfo=timezone.utc)


def test_off_mode_is_unavailable() -> None:
    snap = fetcher_for_mode("off").fetch(AS_OF, prior_us_close=PRIOR)
    assert snap.data_quality == "unavailable"
    assert snap.assets == ()


def test_fred_missing_api_key_degrades() -> None:
    spec = {
        "live": {
            "enabled": True,
            "fred": {"enabled": True, "api_key_env": "FRED_API_KEY", "series": {"US10Y": "DGS10"}},
            "stooq": {"enabled": False},
            "coingecko": {"enabled": False},
        }
    }
    fetcher = LiveMacroFetcher(spec, env={})
    snap = fetcher.fetch(AS_OF, prior_us_close=PRIOR)
    assert snap.data_quality == "unavailable"
    assert any("FRED_API_KEY" in note for note in snap.notes)


def test_stooq_http_error_degrades() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="down")

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    spec = {
        "live": {
            "enabled": True,
            "stooq": {"enabled": True, "symbols": {"ES": "es.f"}},
            "fred": {"enabled": False},
            "coingecko": {"enabled": False},
        }
    }
    snap = LiveMacroFetcher(spec, client=client).fetch(AS_OF, prior_us_close=PRIOR)
    assert snap.data_quality == "unavailable"


def test_empty_snapshot_helper() -> None:
    snap = empty_snapshot(AS_OF, PRIOR, reason="test")
    assert snap.data_quality == "unavailable"
    assert snap.notes == ("test",)
