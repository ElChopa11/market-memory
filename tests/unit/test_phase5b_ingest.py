"""Phase 5b adapters: Polygon default, HL structure, spot DQ, FRED/calendar. Degrade-never-invent."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from mm_common.enums import DataQuality
from mm_common.http import ERROR_MISSING_ENV, ERROR_RATE_LIMITED, ERROR_TOS_OR_BLOCKED
from mm_ingest.config import load_equity_instruments, load_ingest_settings
from mm_ingest.equities import DEFAULT_EQUITIES_VENDOR, get_equities_adapter
from mm_ingest.equities.interface import EquitiesQuery
from mm_ingest.equities.polygon import PolygonEquitiesAdapter
from mm_ingest.hl_info import ALLOWED_INFO_TYPES, FORBIDDEN_INFO_TYPES, HyperliquidInfoClient, HyperliquidInfoError
from mm_ingest.pipeline import envelopes_from_fixture, load_fixture_file
from mm_ingest.rate_limit import RateLimitBudget
from mm_ingest.spot import fetch_binance_usd
from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "phase5b"
INGESTED = datetime(2026, 9, 18, 0, 5, tzinfo=timezone.utc)


def test_default_equities_vendor_is_polygon() -> None:
    settings = load_ingest_settings()
    assert settings["equities"]["vendor"] == "polygon"
    assert DEFAULT_EQUITIES_VENDOR == "polygon"
    adapter = get_equities_adapter("unknown-vendor")
    assert adapter.vendor == "polygon"
    assert load_equity_instruments() == ["NVDA", "AVGO", "SMH", "MSFT", "META", "JPM", "XLF", "XOM"]
    limits = settings["rate_limits"]
    for name in ("polygon", "hyperliquid", "coingecko", "binance", "fred", "edgar"):
        assert "max_requests_per_minute" in limits[name]


def test_polygon_missing_key_degrades_without_http() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"results": []})

    adapter = PolygonEquitiesAdapter(
        env={},
        http_client=httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0),
        sleep=lambda _: None,
    )
    query = EquitiesQuery(
        tickers=("NVDA",),
        start=INGESTED,
        end=INGESTED,
        ingested_at=INGESTED,
    )
    assert adapter.ohlcv_daily(query) == ()
    assert adapter.last_error_class == ERROR_MISSING_ENV
    assert calls["n"] == 0
    fixture = load_fixture_file(FIXTURES / "polygon_missing_key.json")
    envelopes = envelopes_from_fixture(fixture)
    assert envelopes
    assert all(e.data_quality is DataQuality.PARTIAL for e in envelopes)
    assert all(e.payload.get("error_class") == "missing_env" for e in envelopes)
    assert all(e.as_of_knowledge == e.ingested_at for e in envelopes)


def test_polygon_ohlcv_fixture_and_retry() -> None:
    fixture = load_fixture_file(FIXTURES / "polygon_ohlcv.json")
    envelopes = envelopes_from_fixture(fixture)
    closes = [e for e in envelopes if e.metric == "ohlcv_close"]
    assert len(closes) == 3
    assert {e.identity.extras.get("timespan") for e in closes} == {"day", "minute"}
    assert all(e.source_name == "polygon" for e in closes)
    assert all("perp" not in e.claim_text for e in closes)
    assert all(e.as_of_knowledge == e.ingested_at == INGESTED for e in closes)

    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, json={"error": "down"})
        return httpx.Response(
            200,
            json={"results": [{"t": 1789675200000, "o": 1, "h": 2, "l": 1, "c": 1.5, "v": 9}]},
        )

    adapter = PolygonEquitiesAdapter(
        api_key="test-key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0),
        sleep=lambda _: None,
        budget=RateLimitBudget(name="polygon", max_requests_per_minute=5),
    )
    bars = adapter.ohlcv_daily(
        EquitiesQuery(tickers=("NVDA",), start=INGESTED, end=INGESTED, ingested_at=INGESTED)
    )
    assert len(bars) == 1
    assert bars[0].close == 1.5
    assert calls["n"] == 2


def test_polygon_rate_limit_budget_skips_without_inventing() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"results": [{"t": 1789675200000, "c": 1}]})

    adapter = PolygonEquitiesAdapter(
        api_key="test-key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0),
        sleep=lambda _: None,
        budget=RateLimitBudget(name="polygon", max_requests_per_minute=1),
    )
    query = EquitiesQuery(tickers=("NVDA", "MSFT"), start=INGESTED, end=INGESTED, ingested_at=INGESTED)
    bars = adapter.ohlcv_daily(query)
    assert len(bars) == 1
    assert adapter.last_error_class == ERROR_RATE_LIMITED
    assert calls["n"] == 1


def test_polygon_corporate_actions_and_earnings_unavailable() -> None:
    divs = envelopes_from_fixture(load_fixture_file(FIXTURES / "polygon_corporate_actions.json"))
    assert any(e.metric == "dividend" and e.instrument == "NVDA" for e in divs)
    earn = envelopes_from_fixture(load_fixture_file(FIXTURES / "polygon_earnings_unavailable.json"))
    assert earn
    assert all(e.payload.get("error_class") == ERROR_TOS_OR_BLOCKED for e in earn)
    assert all(e.identity.value == "unavailable" for e in earn)

    def handler(request: httpx.Request) -> httpx.Response:
        if "/events" in str(request.url):
            return httpx.Response(403, json={"status": "NOT_AUTHORIZED"})
        if "/dividends" in str(request.url):
            return httpx.Response(
                200,
                json={"results": [{"ticker": "NVDA", "cash_amount": 0.01, "ex_dividend_date": "2026-09-16"}]},
            )
        if "/splits" in str(request.url):
            return httpx.Response(200, json={"results": []})
        return httpx.Response(404, json={})

    adapter = PolygonEquitiesAdapter(
        api_key="test-key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0),
        sleep=lambda _: None,
    )
    query = EquitiesQuery(tickers=("NVDA",), start=INGESTED, end=INGESTED, ingested_at=INGESTED)
    actions = adapter.corporate_actions(query)
    assert len(actions) == 1
    assert actions[0].kind == "dividend"
    assert adapter.earnings_calendar(query) == ()
    assert adapter.last_error_class == ERROR_TOS_OR_BLOCKED


def test_hl_structure_fixture_and_l2_allowlist() -> None:
    assert "l2Book" in ALLOWED_INFO_TYPES
    assert "l2Book" not in FORBIDDEN_INFO_TYPES
    envelopes = envelopes_from_fixture(load_fixture_file(FIXTURES / "hl_structure.json"))
    metrics = {e.metric for e in envelopes}
    assert "basis_mark_oracle" in metrics
    assert "l2_spread" in metrics
    assert "predicted_funding" in metrics
    basis = next(e for e in envelopes if e.metric == "basis_mark_oracle")
    assert basis.evidence_type.value == "derived"
    assert float(basis.identity.value or "0") != 0
    assert all(e.as_of_knowledge == e.ingested_at for e in envelopes)

    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        body = json.loads(request.content)
        seen.append(str(body.get("type")))
        if body.get("type") == "l2Book":
            return httpx.Response(200, json={"coin": "BTC", "levels": [[{"px": "1", "sz": "1"}], [{"px": "2", "sz": "1"}]]})
        return httpx.Response(200, json={})

    client = HyperliquidInfoClient(transport=httpx.MockTransport(handler), timeout=2.0, sleep=lambda _: None)
    book = client.l2_book("BTC")
    assert book["coin"] == "BTC"
    with pytest.raises(HyperliquidInfoError, match="refusing non-public"):
        client.post({"type": "clearinghouseState", "user": "0x" + "0" * 40})
    assert "clearinghouseState" not in seen


def test_spot_cross_check_divergence_and_binance_unavailable() -> None:
    envelopes = envelopes_from_fixture(load_fixture_file(FIXTURES / "spot_cross_check.json"))
    spot = [e for e in envelopes if e.metric == "spot_px" and e.source_name == "coingecko"]
    assert spot and spot[0].data_quality is DataQuality.OK
    derived = next(e for e in envelopes if e.metric == "basis_perp_spot")
    assert derived.data_quality is DataQuality.CONTRADICTED
    assert derived.payload.get("not_executable_arb") is True
    binance = [e for e in envelopes if e.source_name == "binance.public"]
    assert binance
    assert all(e.payload.get("error_class") == ERROR_RATE_LIMITED for e in binance)

    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429, json={"msg": "slow"})

    prints, error = fetch_binance_usd(
        symbols={"BTC": "BTCUSDT"},
        http_client=httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0),
        sleep=lambda _: None,
        budget=RateLimitBudget(name="binance", max_requests_per_minute=5),
    )
    assert prints == {}
    assert error == ERROR_RATE_LIMITED
    from mm_common.http import DEFAULT_MAX_ATTEMPTS

    assert calls["n"] == DEFAULT_MAX_ATTEMPTS  # exponential retries on 429


def test_fred_and_calendar_fixtures() -> None:
    series = envelopes_from_fixture(load_fixture_file(FIXTURES / "fred_series.json"))
    assert any(e.metric == "fred_observation" and e.instrument == "US10Y" for e in series)
    assert all(e.as_of_knowledge == e.ingested_at for e in series)
    missing = envelopes_from_fixture(load_fixture_file(FIXTURES / "fred_missing_key.json"))
    assert missing
    assert all(e.payload.get("error_class") == "missing_env" for e in missing)
    cal = envelopes_from_fixture(load_fixture_file(FIXTURES / "economic_calendar.yaml"))
    names = {e.identity.value for e in cal}
    assert "CPI YoY" in names
    assert all(e.source_name == "calendar.yaml" for e in cal)


def test_lab_ingest_no_db_dry_run(capsys) -> None:
    rc = main(
        [
            "ingest",
            "--fixture",
            str(FIXTURES / "polygon_ohlcv.json"),
            "--no-db",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "\"dry_run\": true" in out
    assert "polygon" in out


def test_hl_retry_on_503() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, json={"error": "down"})
        return httpx.Response(200, json={"BTC": "1"})

    client = HyperliquidInfoClient(transport=httpx.MockTransport(handler), timeout=2.0, sleep=lambda _: None)
    assert client.all_mids()["BTC"] == "1"
    assert calls["n"] == 2
