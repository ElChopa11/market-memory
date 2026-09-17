"""Live macro fetchers degrade when keys/HTTP fail; never require secrets."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import httpx

from mm_briefing.fetchers import LiveMacroFetcher, empty_snapshot, fetcher_for_mode
from mm_briefing.render import SOURCE_HEALTH_POINTER, _no_decision_footer


AS_OF = datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc)
PRIOR = datetime(2026, 3, 9, 20, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[2]
STOOQ_CSV = "Symbol,Date,Time,Open,High,Low,Close,Volume\nes.f,2026-03-09,18:00:00,1,1,1,5750.25,1\n"


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
    blob = " ".join(snap.notes)
    assert "FRED_API_KEY" in blob
    assert "missing_env" in blob
    assert "never commit" in blob
    assert "sk-" not in blob


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
    snap = LiveMacroFetcher(spec, client=client, sleep=lambda _: None).fetch(AS_OF, prior_us_close=PRIOR)
    assert snap.data_quality == "unavailable"
    assert any("http_5xx" in note for note in snap.notes)
    assert any("no scrape fallback" in note for note in snap.notes)


def test_stooq_404_is_terminal_classified() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(404, text="no")

    spec = {
        "live": {
            "enabled": True,
            "stooq": {"enabled": True, "symbols": {"ES": "es.f", "NQ": "nq.f"}},
            "fred": {"enabled": False},
            "coingecko": {"enabled": False},
        }
    }
    client = httpx.Client(transport=httpx.MockTransport(handler))
    snap = LiveMacroFetcher(spec, client=client, sleep=lambda _: None).fetch(AS_OF, prior_us_close=PRIOR)
    assert snap.data_quality == "unavailable"
    assert calls["n"] == 2  # one GET per symbol, no retry
    blob = " ".join(snap.notes)
    assert "http_404" in blob
    assert "ES" in blob and "NQ" in blob
    assert "source-health" in blob


def test_stooq_retries_5xx_then_parses() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, text="down")
        return httpx.Response(200, text=STOOQ_CSV)

    spec = {
        "live": {
            "enabled": True,
            "stooq": {"enabled": True, "symbols": {"ES": "es.f"}},
            "fred": {"enabled": False},
            "coingecko": {"enabled": False},
        }
    }
    client = httpx.Client(transport=httpx.MockTransport(handler))
    snap = LiveMacroFetcher(spec, client=client, sleep=lambda _: None).fetch(AS_OF, prior_us_close=PRIOR)
    assert calls["n"] == 2
    assert snap.assets[0].last == 5750.25
    assert snap.assets[0].data_quality in {"ok", "stale"}


def test_empty_snapshot_helper() -> None:
    snap = empty_snapshot(AS_OF, PRIOR, reason="test")
    assert snap.data_quality == "unavailable"
    assert snap.notes == ("test",)


def test_live_footer_points_at_source_health_fixture_does_not() -> None:
    assert SOURCE_HEALTH_POINTER not in _no_decision_footer(live_macro=False)
    live = _no_decision_footer(live_macro=True)
    assert SOURCE_HEALTH_POINTER in live
    assert "lab data source-health" in SOURCE_HEALTH_POINTER
    assert "ops/reports/source-health/" in SOURCE_HEALTH_POINTER


def test_no_stooq_scrape_workarounds_in_clients() -> None:
    blobs = [
        (ROOT / "packages" / "briefing" / "src" / "mm_briefing" / "fetchers.py").read_text(encoding="utf-8"),
        (ROOT / "packages" / "source_health" / "src" / "mm_source_health" / "probes.py").read_text(encoding="utf-8"),
        (ROOT / "packages" / "common" / "src" / "mm_common" / "http.py").read_text(encoding="utf-8"),
    ]
    joined = "\n".join(blobs).lower()
    forbidden = (
        "stooq.pl",
        "yahoo.com",
        "investing.com",
        "beautifulsoup",
        "html.parser",
        "/q/d/l/",
        "l.stooq.com",
    )
    for snippet in forbidden:
        assert snippet not in joined, snippet
    assert "stooq.com/q/l/" in blobs[0]
