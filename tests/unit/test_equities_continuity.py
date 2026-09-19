"""Polygon/equities ticker-reuse continuity: listing-date + 20/20 level-shift VOID; single-bar FLAG."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import httpx

from mm_ingest.equities.continuity import (
    LEVEL_SHIFT_RATIO,
    LEVEL_SHIFT_WINDOW,
    REASON_SINGLE_BAR_EXTREME,
    REASON_TICKER_REUSE,
    SINGLE_BAR_FLAG_ABS,
    TRIGGER_LEVEL_SHIFT,
    TRIGGER_LISTING_DATE,
    TRIGGER_SINGLE_BAR,
    check_bar_continuity,
    check_ohlcv_continuity,
)
from mm_ingest.equities.interface import EquitiesQuery
from mm_ingest.equities.models import OHLCVBar
from mm_ingest.equities.polygon import POLYGON_ADJUSTED_QUERY, POLYGON_OHLCV_ADJUSTED, PolygonEquitiesAdapter
from mm_ingest.rate_limit import RateLimitBudget


INGESTED = datetime(2026, 9, 19, tzinfo=timezone.utc)


def _pairs(n: int, start: date, start_px: float = 100.0, daily: float = 0.001) -> list[tuple[date, float]]:
    """Constant percent drift — no 3× level shift, no 20% single bar."""
    rows: list[tuple[date, float]] = []
    px = start_px
    for i in range(n):
        px = px * (1.0 + daily)
        rows.append((start + timedelta(days=i), px))
    return rows


def _ohlcv(rows: list[tuple[date, float]], ticker: str = "NVDA") -> list[OHLCVBar]:
    out: list[OHLCVBar] = []
    for d, px in rows:
        out.append(
            OHLCVBar(
                ticker=ticker,
                open=px,
                high=px + 0.1,
                low=px - 0.1,
                close=px,
                volume=1000.0,
                market_time=datetime(d.year, d.month, d.day, tzinfo=timezone.utc),
                timespan="day",
                multiplier=1,
            )
        )
    return out


def test_rule_a_first_bar_before_listing_date_voids() -> None:
    bars = _pairs(20, date(2024, 9, 19), start_px=10.0, daily=0.0005)
    verdict = check_bar_continuity(bars, listed_on=date(2026, 6, 11))
    assert verdict.void is True
    assert verdict.flagged is True
    assert verdict.reason_code == REASON_TICKER_REUSE
    assert TRIGGER_LISTING_DATE in verdict.void_triggers
    assert TRIGGER_LEVEL_SHIFT not in verdict.void_triggers
    assert verdict.first == date(2024, 9, 19)
    assert "precedes known listing 2026-06-11" in verdict.detail


def test_rule_a_first_bar_on_or_after_listing_clears_date_check() -> None:
    bars = _pairs(50, date(2026, 6, 11), start_px=50.0, daily=0.001)
    verdict = check_bar_continuity(bars, listed_on=date(2026, 6, 11))
    assert TRIGGER_LISTING_DATE not in verdict.void_triggers
    assert verdict.void is False
    assert verdict.flag is False


def test_rule_b_sustained_3x_level_shift_voids() -> None:
    start = date(2024, 9, 19)
    bars = [(start + timedelta(days=i), 22.0) for i in range(25)]
    bars += [(start + timedelta(days=25 + i), 150.0) for i in range(25)]
    verdict = check_bar_continuity(bars, listed_on=None)
    assert verdict.void is True
    assert verdict.reason_code == REASON_TICKER_REUSE
    assert TRIGGER_LEVEL_SHIFT in verdict.void_triggers
    assert verdict.level_shift_ratio is not None
    assert verdict.level_shift_ratio >= LEVEL_SHIFT_RATIO
    assert verdict.level_shift_skip_reason is None


def test_rule_b_transient_spike_that_reverts_does_not_void() -> None:
    start = date(2024, 9, 19)
    bars = [(start + timedelta(days=i), 100.0) for i in range(25)]
    bars.append((start + timedelta(days=25), 500.0))  # one huge bar
    bars += [(start + timedelta(days=26 + i), 100.0) for i in range(25)]
    verdict = check_bar_continuity(bars, listed_on=None)
    assert verdict.void is False
    assert TRIGGER_LEVEL_SHIFT not in verdict.void_triggers
    assert verdict.flag is True
    assert verdict.flag_code == REASON_SINGLE_BAR_EXTREME
    assert TRIGGER_SINGLE_BAR in verdict.flag_triggers
    assert verdict.reason_code == ""


def test_rule_c_single_huge_bar_without_shift_flags_and_stays_in_pool() -> None:
    start = date(2024, 1, 1)
    bars = [(start + timedelta(days=i), 100.0) for i in range(25)]
    bars.append((start + timedelta(days=25), 125.0))  # +25%, then reverts
    bars += [(start + timedelta(days=26 + i), 100.0) for i in range(25)]
    verdict = check_bar_continuity(bars, listed_on=None)
    assert verdict.void is False
    assert verdict.level_shift_skip_reason is None
    assert TRIGGER_LEVEL_SHIFT not in verdict.void_triggers
    assert verdict.flag is True
    assert verdict.max_abs_1bar is not None
    assert verdict.max_abs_1bar >= SINGLE_BAR_FLAG_ABS
    assert "stays in compute pool" in verdict.detail
    assert "not a void" in verdict.detail
    assert "n_sigma" not in verdict.void_triggers
    assert "n_sigma" not in verdict.triggers


def test_rule_b_skips_when_fewer_than_20_bars_each_side() -> None:
    start = date(2024, 9, 19)
    bars = [(start + timedelta(days=i), 10.0 if i < 8 else 80.0) for i in range(15)]
    verdict = check_bar_continuity(bars, listed_on=None)
    assert verdict.void is False
    assert TRIGGER_LEVEL_SHIFT not in verdict.void_triggers
    assert verdict.level_shift_skip_reason is not None
    assert "fewer than 20 bars each side" in verdict.level_shift_skip_reason
    assert "rule B skipped" in verdict.detail


def test_nvda_like_series_does_not_void_under_b_or_c() -> None:
    """Fat-tail 18.7% day on a continuous ~$100 series — the #77 N=8 false void."""
    start = date(2024, 9, 19)
    bars: list[tuple[date, float]] = []
    px = 100.0
    for i in range(250):
        if i == 120:
            px = px * 1.1872  # NVDA-like max |1-bar| from the N=8 run
        else:
            px = px * 1.0015
        bars.append((start + timedelta(days=i), px))
    verdict = check_bar_continuity(bars, listed_on=date(1999, 1, 22))
    assert verdict.void is False
    assert TRIGGER_LEVEL_SHIFT not in verdict.void_triggers
    assert TRIGGER_LISTING_DATE not in verdict.void_triggers
    assert verdict.reason_code == ""
    # 18.7% is under the 20% FLAG floor; either way C must not void.
    assert verdict.flagged is False
    if verdict.flag:
        assert verdict.flag_code == REASON_SINGLE_BAR_EXTREME


def test_flat_tape_then_29pct_jump_is_not_a_void() -> None:
    """Old N-sigma / MAD=0 floor would have voided this. 1.30× is not a 3× shift."""
    start = date(2024, 9, 19)
    bars = [(start + timedelta(days=i), 25.0) for i in range(40)]
    bars.append((start + timedelta(days=40), 25.0 * 1.298))
    bars += [(start + timedelta(days=41 + i), 25.0 * 1.298) for i in range(25)]
    verdict = check_bar_continuity(bars, listed_on=None)
    assert verdict.void is False
    assert TRIGGER_LEVEL_SHIFT not in verdict.void_triggers
    assert verdict.flag is True  # 29.8% day is a FLAG


def test_ohlcv_bars_and_adapter_helper_agree() -> None:
    raw = _ohlcv(_pairs(15, date(2024, 9, 19), start_px=10.0, daily=0.0), ticker="SPCX")
    listed = date(2026, 6, 11)
    a = check_ohlcv_continuity(raw, listed_on=listed)
    b = PolygonEquitiesAdapter(api_key="unused", env={"POLYGON_API_KEY": "unused"}).continuity_check(
        raw, listed_on=listed
    )
    assert a.void is True and b.void is True
    assert a.reason_code == b.reason_code == REASON_TICKER_REUSE
    assert a.n_bars == b.n_bars == 15
    assert TRIGGER_LISTING_DATE in a.void_triggers


def test_level_shift_window_and_flag_floor_are_documented_constants() -> None:
    assert LEVEL_SHIFT_WINDOW == 20
    assert LEVEL_SHIFT_RATIO == 3.0
    assert SINGLE_BAR_FLAG_ABS == 0.20
    assert POLYGON_OHLCV_ADJUSTED is True
    assert POLYGON_ADJUSTED_QUERY == "true"


def test_polygon_daily_aggs_request_adjusted_true() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["adjusted"] = request.url.params.get("adjusted", "")
        return httpx.Response(200, json={"results": []})

    adapter = PolygonEquitiesAdapter(
        api_key="test-key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0),
        sleep=lambda _: None,
        budget=RateLimitBudget(name="polygon", max_requests_per_minute=5),
    )
    adapter.ohlcv_daily(
        EquitiesQuery(tickers=("BMNR",), start=INGESTED, end=INGESTED, ingested_at=INGESTED)
    )
    assert captured["adjusted"] == "true"
    assert "adjusted=true" in captured["url"]
