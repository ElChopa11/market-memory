"""History backfill plan, CLI, and fetch limits. No live HTTP."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import yaml

from mm_briefing.fetchers import LiveMacroFetcher
from mm_common.http import ERROR_NONE
from mm_ingest.equities.polygon import PolygonEquitiesAdapter
from mm_ingest.history_backfill import (
    FRED_BACKFILL_SERIES,
    HL_DAILY_INTERVAL,
    HL_MIN_SESSIONS,
    MinutePacer,
    POLYGON_BACKFILL_AGG_LIMIT,
    POLYGON_LOOKBACK_CALENDAR_DAYS,
    brief_polygon_slots,
    collect_history_backfill,
    history_backfill_plan,
)
from mm_ingest.macro import fetch_fred_series
from mm_ingest.rate_limit import RateLimitBudget
from mm_lab_cli.cli import main
from mm_provenance.normalize import normalize_candles

ROOT = Path(__file__).resolve().parents[2]
AS_OF = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)


def test_plan_uses_brief_tape_slots_and_states_call_counts() -> None:
    plan = history_backfill_plan(now=AS_OF, repo=ROOT)
    public = plan.as_public_dict()
    assert plan.polygon_tickers == ("SPY", "QQQ", "UUP", "USO")
    assert "VIX" not in plan.polygon_tickers
    assert plan.polygon_calls == 4
    assert plan.polygon_rpm == 5
    assert plan.polygon_multi_minute is False
    assert "Not multi-minute" in public["polygon"]["rate_limit_duration"]
    assert plan.fred_series == {"US10Y": "DGS10", "US2Y": "DGS2"}
    assert plan.fred_calls == 2
    assert plan.hl_coins == ("BTC", "ETH", "UNI", "AAVE")
    assert plan.hl_calls == 4
    assert public["hyperliquid"]["interval"] == HL_DAILY_INTERVAL
    assert public["hyperliquid"]["min_sessions"] == HL_MIN_SESSIONS
    assert public["hyperliquid"]["timestamp_field"].startswith("t ")
    assert "after lab migrate" in public["sequence"]
    assert "DO NOT RUN" in public["do_not_run"]
    assert plan.polygon_start == (AS_OF.date() - timedelta(days=POLYGON_LOOKBACK_CALENDAR_DAYS)).isoformat()
    macro = yaml.safe_load((ROOT / "config" / "briefing" / "macro.yaml").read_text(encoding="utf-8"))
    slots = brief_polygon_slots(macro)
    assert [ticker for _slot, ticker in slots] == ["SPY", "QQQ", "UUP", "USO"]
    structural = macro["live"]["polygon"]["structural_unavailable"]
    assert "VIX" in structural
    assert macro["live"]["fred"]["series"] == {"US10Y": "DGS10"}
    regimes = yaml.safe_load((ROOT / "config" / "macro" / "regimes.yaml").read_text(encoding="utf-8"))
    assert regimes["fred_series"]["US10Y"] == "DGS10"
    assert regimes["fred_series"]["US2Y"] == "DGS2"
    assert FRED_BACKFILL_SERIES["US2Y"] == "DGS2"


def test_history_backfill_is_cli_only_and_hybrid_brief_stays(capsys) -> None:
    workflow = ROOT / ".github" / "workflows" / "history-backfill.yml"
    assert not workflow.exists()
    for path in (ROOT / ".github" / "workflows").glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        assert "i_mean_it_backfill" not in text
        assert "name: history-backfill" not in text
        assert "environment: neon-write" not in text

    runbook = (ROOT / "docs" / "runbooks" / "ingest.md").read_text(encoding="utf-8")
    section = runbook.split("## History backfill", 1)[1].split("## Phase 5b feeds", 1)[0]
    assert "CLI-only" in section
    assert "uv run lab history-backfill" in section
    assert '"phase": "plan"' in section
    assert '"phase": "fetch"' in section
    assert "morning-deliver PAT" in section
    assert "No `workflow_dispatch`" in section
    assert "no `repository_dispatch`" in section
    assert "no `schedule`" in section
    assert "POSTGRES_DSN" in section
    assert "POLYGON_API_KEY" in section
    assert "FRED_API_KEY" in section
    assert "MINIO_ENDPOINT" in section
    assert "MINIO_ACCESS_KEY" in section
    assert "MINIO_SECRET_KEY" in section
    assert "MINIO_BUCKET" in section
    assert "market-memory" in section
    assert "S3_REGION=auto" in section
    assert "No `TELEGRAM_*`" in section
    assert "public `/info`" in section
    assert "ON CONFLICT DO NOTHING" in section
    assert "observation_claim_hash_uidx" in section
    assert "contradicts" in section
    assert "not a gate" in section
    assert "Delete `neon-write`" in section
    assert "This repository is private" in section
    assert "The repository is public" not in section
    assert "Waiting" not in section
    assert "New environment" not in section
    assert "i_mean_it_backfill" in section

    assert main([]) == 0
    status = capsys.readouterr().out
    assert "Actions gate" not in status
    assert "i_mean_it_backfill" not in status
    assert "CLI-only" in status
    assert "no GitHub Actions trigger" in status

    hybrid = (ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml").read_text(encoding="utf-8")
    assert 'cron: "30 20 * * 0-4"' in hybrid
    assert "brief-and-deliver" in hybrid
    assert "uv run lab brief close --live --no-db" in hybrid
    assert "lab deliver pack --to-principal-dm --i-mean-it --no-db" in hybrid


def test_fred_default_limit_stays_five_and_backfill_omits_limit() -> None:
    seen: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(dict(request.url.params))
        return httpx.Response(
            200,
            json={
                "count": 1,
                "observations": [{"date": "2026-09-18", "value": "4.1"}],
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    envelopes, error = fetch_fred_series(
        series={"US10Y": "DGS10"},
        ingested_at=AS_OF,
        env={"FRED_API_KEY": "test-key"},
        http_client=client,
        sleep=lambda _s: None,
    )
    assert error == ERROR_NONE
    assert envelopes[0].metric == "fred_observation"
    assert seen[0]["limit"] == "5"
    assert seen[0]["sort_order"] == "desc"

    seen.clear()
    full, full_error = fetch_fred_series(
        series={"US10Y": "DGS10", "US2Y": "DGS2"},
        ingested_at=AS_OF,
        env={"FRED_API_KEY": "test-key"},
        http_client=client,
        sleep=lambda _s: None,
        limit=None,
        page_all=True,
        budget=RateLimitBudget(name="fred", max_requests_per_minute=20),
    )
    assert full_error == ERROR_NONE
    assert len(full) == 2
    assert all("limit" not in row for row in seen)
    assert all(row["sort_order"] == "asc" for row in seen)
    assert [row["series_id"] for row in seen] == ["DGS10", "DGS2"]


def test_live_brief_fred_fetch_stays_limit_two() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.params.get("limit", ""))
        return httpx.Response(
            200,
            json={"observations": [{"date": "2026-09-22", "value": "4.1"}, {"date": "2026-09-19", "value": "4.0"}]},
        )

    spec = {
        "live": {
            "enabled": True,
            "fred": {
                "enabled": True,
                "api_key_env": "FRED_API_KEY",
                "series": {"US10Y": "DGS10"},
            },
            "stooq": {"enabled": False},
            "polygon": {"enabled": False},
            "coingecko": {"enabled": False},
        }
    }
    fetcher = LiveMacroFetcher(
        spec,
        env={"FRED_API_KEY": "test-key"},
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _s: None,
    )
    snap = fetcher.fetch(AS_OF, prior_us_close=AS_OF - timedelta(days=1))
    assert seen == ["2"]
    assert snap.assets
    assert snap.assets[0].last == 4.1


def test_pacer_sleeps_only_after_the_minute_budget() -> None:
    sleeps: list[float] = []
    clock = {"now": 1000.0}

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock["now"] += seconds

    pacer = MinutePacer(max_per_minute=5, sleep=sleep, clock=lambda: clock["now"])
    for _ in range(4):
        pacer.acquire()
    assert sleeps == []

    tight = MinutePacer(max_per_minute=2, sleep=sleep, clock=lambda: clock["now"])
    tight.acquire()
    tight.acquire()
    tight.acquire()
    assert sleeps == [60.0]


def test_collect_shapes_daily_rows_without_a_database() -> None:
    def polygon_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("adjusted") == "true"
        assert request.url.params.get("limit") == str(POLYGON_BACKFILL_AGG_LIMIT)
        assert "/range/1/day/" in str(request.url)
        ticker = str(request.url).split("/ticker/")[1].split("/")[0]
        return httpx.Response(
            200,
            json={"results": [{"t": 1789603200000, "o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 10}], "ticker": ticker},
        )

    adapter = PolygonEquitiesAdapter(
        api_key="test-key",
        http_client=httpx.Client(transport=httpx.MockTransport(polygon_handler)),
        sleep=lambda _s: None,
        budget=RateLimitBudget(name="polygon", max_requests_per_minute=4),
        agg_limit=POLYGON_BACKFILL_AGG_LIMIT,
    )

    candles = {
        "BTC": [_candle("BTC", day) for day in range(HL_MIN_SESSIONS)],
        "ETH": [_candle("ETH", day) for day in range(HL_MIN_SESSIONS)],
        "UNI": [_candle("UNI", day) for day in range(HL_MIN_SESSIONS)],
        "AAVE": [_candle("AAVE", day) for day in range(HL_MIN_SESSIONS)],
    }

    class _HL:
        def iter_candles(self, coin: str, interval: str, start_ms: int, end_ms: int) -> list[dict]:
            assert interval == "1d"
            assert end_ms > start_ms
            return candles[coin]

    plan = history_backfill_plan(now=AS_OF, repo=ROOT)
    from mm_ingest import history_backfill as module

    def _fake_fred(**kwargs: object) -> tuple[list, str]:
        assert kwargs["limit"] is None
        assert kwargs["page_all"] is True
        assert kwargs["series"] == plan.fred_series
        budget = kwargs["budget"]
        assert isinstance(budget, RateLimitBudget)
        budget.allow()
        budget.allow()
        from mm_ingest.macro import normalize_fred_observations

        rows: list = []
        for symbol, series_id in plan.fred_series.items():
            rows.extend(
                normalize_fred_observations(
                    {"observations": [{"date": "2026-09-18", "value": "4.1"}]},
                    instrument=symbol,
                    series_id=series_id,
                    ingested_at=AS_OF,
                )
            )
        return rows, ERROR_NONE

    original = module.fetch_fred_series
    module.fetch_fred_series = _fake_fred  # type: ignore[assignment]
    try:
        collected = collect_history_backfill(
            plan,
            ingested_at=AS_OF,
            polygon=adapter,
            hl_client=_HL(),  # type: ignore[arg-type]
            pacer=MinutePacer(max_per_minute=5, sleep=lambda _s: (_ for _ in ()).throw(AssertionError("sleep"))),
        )
    finally:
        module.fetch_fred_series = original

    assert collected.errors == []
    assert collected.calls == {"polygon": 4, "fred": 2, "hyperliquid": 4}
    assert collected.polygon_bars == {"SPY": 1, "QQQ": 1, "UUP": 1, "USO": 1}
    assert collected.fred_rows == {"US10Y": 1, "US2Y": 1}
    assert collected.hl_sessions == {coin: HL_MIN_SESSIONS for coin in plan.hl_coins}
    assert collected.hl_below_minimum() == {}
    assert collected.pacer_slept_s == 0.0
    metrics = {row.metric for row in collected.envelopes}
    assert metrics == {"ohlcv_close", "fred_observation", "candle_close"}
    daily = [row for row in collected.envelopes if row.metric == "candle_close"]
    assert daily[0].identity.extras.get("interval") == "1d"
    assert daily[0].market_time is not None


def test_hl_daily_candle_uses_open_time_field_t() -> None:
    row = {"t": 1790121600000, "T": 1790207999999, "s": "BTC", "i": "1d", "o": "1", "h": "2", "l": "1", "c": "1.5", "v": "3", "n": 4}
    envelopes = normalize_candles([row], ingested_at=AS_OF)
    assert len(envelopes) == 1
    assert envelopes[0].source_url_or_id == "candleSnapshot:BTC:1790121600000"
    assert envelopes[0].identity.extras["interval"] == "1d"
    assert envelopes[0].metric == "candle_close"
    hourly = dict(row)
    hourly["i"] = "1h"
    hourly["t"] = 1790121600000
    other = normalize_candles([hourly], ingested_at=AS_OF)
    assert other[0].claim_hash != envelopes[0].claim_hash


def test_cli_incomplete_object_store_exits_before_http(monkeypatch) -> None:
    monkeypatch.setenv("POLYGON_API_KEY", "test-polygon")
    monkeypatch.setenv("FRED_API_KEY", "test-fred")
    for key in (
        "MINIO_ENDPOINT",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "MINIO_ROOT_USER",
        "MINIO_ROOT_PASSWORD",
        "S3_ENDPOINT",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "MM_OBJECT_STORE",
        "MM_OBJECT_STORE_PATH",
    ):
        monkeypatch.delenv(key, raising=False)

    def refuse(self, request, *args, **kwargs):  # noqa: ANN001
        raise AssertionError(f"http during refused backfill: {request.url}")

    monkeypatch.setattr(httpx.Client, "send", refuse)
    assert main(["history-backfill"]) == 2


def test_cli_missing_keys_does_not_call_http(monkeypatch) -> None:
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    def refuse(self, request, *args, **kwargs):  # noqa: ANN001
        raise AssertionError(f"http during refused backfill: {request.url}")

    monkeypatch.setattr(httpx.Client, "send", refuse)
    code = main(["history-backfill"])
    assert code == 2


def _candle(coin: str, day: int) -> dict:
    open_ms = 1789603200000 + day * 86_400_000
    return {
        "t": open_ms,
        "T": open_ms + 86_400_000 - 1,
        "s": coin,
        "i": "1d",
        "o": "1",
        "h": "2",
        "l": "1",
        "c": "1.5",
        "v": "3",
        "n": 1,
    }

