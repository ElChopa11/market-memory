"""Live macro fetchers degrade when keys/HTTP fail; never require secrets."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

from mm_briefing.fetchers import (
    SLOT_SOURCE,
    LiveMacroFetcher,
    empty_snapshot,
    fetcher_for_mode,
    live_macro_spec,
)
from mm_briefing.render import SOURCE_HEALTH_POINTER, _no_decision_footer


AS_OF = datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc)
PRIOR = datetime(2026, 3, 9, 20, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[2]
STOOQ_CSV = "Symbol,Date,Time,Open,High,Low,Close,Volume\nes.f,2026-03-09,18:00:00,1,1,1,5750.25,1\n"
# Two daily bars: prior close 500, last 510 (ms timestamps around 2026-03-09/10 UTC).
POLYGON_AGGS = {
    "SPY": {
        "status": "OK",
        "ticker": "SPY",
        "results": [
            {"o": 498.0, "c": 500.0, "h": 501.0, "l": 497.0, "v": 1, "t": 1773014400000, "n": 1},
            {"o": 500.0, "c": 510.0, "h": 511.0, "l": 499.0, "v": 1, "t": 1773100800000, "n": 1},
        ],
    },
    "QQQ": {
        "status": "OK",
        "ticker": "QQQ",
        "results": [
            {"o": 400.0, "c": 401.0, "h": 402.0, "l": 399.0, "v": 1, "t": 1773014400000, "n": 1},
            {"o": 401.0, "c": 405.0, "h": 406.0, "l": 400.0, "v": 1, "t": 1773100800000, "n": 1},
        ],
    },
    "UUP": {
        "status": "OK",
        "ticker": "UUP",
        "results": [
            {"o": 28.0, "c": 28.1, "h": 28.2, "l": 27.9, "v": 1, "t": 1773014400000, "n": 1},
            {"o": 28.1, "c": 28.3, "h": 28.4, "l": 28.0, "v": 1, "t": 1773100800000, "n": 1},
        ],
    },
    "USO": {
        "status": "OK",
        "ticker": "USO",
        "results": [
            {"o": 70.0, "c": 71.0, "h": 72.0, "l": 69.0, "v": 1, "t": 1773014400000, "n": 1},
            {"o": 71.0, "c": 72.5, "h": 73.0, "l": 70.5, "v": 1, "t": 1773100800000, "n": 1},
        ],
    },
}


def _polygon_live_spec() -> dict:
    return {
        "live": {
            "enabled": True,
            "polygon": {
                "enabled": True,
                "api_key_env": "POLYGON_API_KEY",
                "base_url": "https://api.polygon.io",
                "symbols": {
                    "ES": {"ticker": "SPY", "label": "SPY ETF (proxy for S&P 500; not ES futures)"},
                    "NQ": {"ticker": "QQQ", "label": "QQQ ETF (proxy for Nasdaq-100; not NQ futures)"},
                    "DXY": {"ticker": "UUP", "label": "UUP ETF (USD proxy; not DX futures / DXY)"},
                    "CL": {"ticker": "USO", "label": "USO ETF (WTI oil proxy; not CL futures)"},
                },
                "structural_unavailable": {
                    "VIX": {
                        "reason": (
                            "true VIX/VX needs Cboe entitlement not on Polygon stocks plan; "
                            "VIXY ETF is not VIX (SRC-STOOQ-404)"
                        )
                    }
                },
            },
            "stooq": {"enabled": False},
            "fred": {"enabled": False},
            "coingecko": {"enabled": False},
        }
    }


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
            "polygon": {"enabled": False},
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
            "polygon": {"enabled": False},
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
            "polygon": {"enabled": False},
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
            "polygon": {"enabled": False},
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


def test_slot_source_prefers_polygon_not_stooq() -> None:
    for symbol in ("ES", "NQ", "DXY", "CL", "VIX"):
        assert SLOT_SOURCE[symbol] == "polygon"
    assert SLOT_SOURCE["US10Y"] == "fred"
    assert SLOT_SOURCE["BTC"] == "hyperliquid"
    assert SLOT_SOURCE["ETH"] == "hyperliquid"


def test_macro_yaml_routes_proxies_to_polygon() -> None:
    raw = yaml.safe_load((ROOT / "config" / "briefing" / "macro.yaml").read_text(encoding="utf-8"))
    live = raw["live"]
    assert live["stooq"]["symbols"] == {} or live["stooq"]["symbols"] is None
    poly = live["polygon"]
    assert poly["symbols"]["ES"]["ticker"] == "SPY"
    assert poly["symbols"]["NQ"]["ticker"] == "QQQ"
    assert poly["symbols"]["DXY"]["ticker"] == "UUP"
    assert poly["symbols"]["CL"]["ticker"] == "USO"
    assert "VIX" not in poly["symbols"]
    assert "VIX" in poly["structural_unavailable"]
    assert "SRC-STOOQ-404" in poly["structural_unavailable"]["VIX"]["reason"]
    for _slot, meta in poly["symbols"].items():
        assert "proxy" in meta["label"].lower()
        assert "not" in meta["label"].lower()


def test_live_macro_spec_enables_polygon() -> None:
    raw = yaml.safe_load((ROOT / "config" / "briefing" / "macro.yaml").read_text(encoding="utf-8"))
    spec = live_macro_spec(raw)
    assert spec["live"]["polygon"]["enabled"] is True
    assert spec["live"]["enabled"] is True


def test_polygon_missing_api_key_lists_slots_unavailable() -> None:
    snap = LiveMacroFetcher(_polygon_live_spec(), env={}).fetch(AS_OF, prior_us_close=PRIOR)
    by = {row.symbol: row for row in snap.assets}
    assert by["ES"].data_quality == "unavailable"
    assert by["ES"].source == "polygon"
    assert "proxy" in by["ES"].name.lower()
    assert by["VIX"].data_quality == "unavailable"
    assert by["VIX"].last is None
    blob = " ".join(snap.notes)
    assert "POLYGON_API_KEY" in blob
    assert "missing_env" in blob
    assert "structural unavailable" in blob.lower() or "VIX" in blob


def test_polygon_etf_proxies_parse_with_honest_labels() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        for ticker, body in POLYGON_AGGS.items():
            if f"/ticker/{ticker}/" in path:
                return httpx.Response(200, json=body)
        return httpx.Response(404, json={"status": "NOT_FOUND"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    snap = LiveMacroFetcher(
        _polygon_live_spec(),
        client=client,
        env={"POLYGON_API_KEY": "test-key"},
        sleep=lambda _: None,
    ).fetch(AS_OF, prior_us_close=PRIOR)
    by = {row.symbol: row for row in snap.assets}
    assert by["ES"].last == 510.0
    assert by["ES"].prior_close == 500.0
    assert by["ES"].source == "polygon"
    assert "not ES futures" in by["ES"].name
    assert by["NQ"].last == 405.0
    assert "not NQ futures" in by["NQ"].name
    assert by["DXY"].last == 28.3
    assert "not DX" in by["DXY"].name
    assert by["CL"].last == 72.5
    assert "not CL futures" in by["CL"].name
    assert by["VIX"].last is None
    assert by["VIX"].data_quality == "unavailable"
    assert any("structural unavailable" in note.lower() for note in snap.notes)
    assert any("SRC-STOOQ-404" in note for note in snap.notes)
    # Never invent a futures print disguised as ES last.
    assert by["ES"].unit == "usd"


def test_polygon_overwrites_stooq_same_slot_when_both_enabled() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "stooq.com" in url:
            return httpx.Response(200, text=STOOQ_CSV)
        if "/ticker/SPY/" in request.url.path:
            return httpx.Response(200, json=POLYGON_AGGS["SPY"])
        return httpx.Response(404, text="no")

    spec = {
        "live": {
            "enabled": True,
            "stooq": {"enabled": True, "symbols": {"ES": "es.f"}},
            "polygon": {
                "enabled": True,
                "api_key_env": "POLYGON_API_KEY",
                "symbols": {"ES": {"ticker": "SPY", "label": "SPY ETF (proxy for S&P 500; not ES futures)"}},
            },
            "fred": {"enabled": False},
            "coingecko": {"enabled": False},
        }
    }
    client = httpx.Client(transport=httpx.MockTransport(handler))
    snap = LiveMacroFetcher(
        spec,
        client=client,
        env={"POLYGON_API_KEY": "test-key"},
        sleep=lambda _: None,
    ).fetch(AS_OF, prior_us_close=PRIOR)
    es = snap.by_symbol()["ES"]
    assert es.source == "polygon"
    assert es.last == 510.0
    assert "proxy" in es.name.lower()
