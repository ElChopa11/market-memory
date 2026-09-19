"""Polygon/equities ticker-reuse continuity check (listing date + N-sigma)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from mm_ingest.equities.continuity import (
    CONTINUITY_N_SIGMA,
    MAD_ZERO_ABS_FLOOR,
    REASON_TICKER_REUSE,
    check_bar_continuity,
    check_ohlcv_continuity,
)
from mm_ingest.equities.models import OHLCVBar
from mm_ingest.equities.polygon import PolygonEquitiesAdapter


def _pairs(n: int, start: date, start_px: float = 100.0, daily: float = 0.001) -> list[tuple[date, float]]:
    """Constant percent drift — identical 1-bar returns (MAD=0, below the 5% floor)."""
    rows: list[tuple[date, float]] = []
    px = start_px
    for i in range(n):
        px = px * (1.0 + daily)
        rows.append((start + timedelta(days=i), px))
    return rows


def test_first_bar_before_listing_date_is_ticker_reuse() -> None:
    bars = _pairs(20, date(2024, 9, 19), start_px=10.0, daily=0.0005)
    verdict = check_bar_continuity(bars, listed_on=date(2026, 6, 11), n_sigma=CONTINUITY_N_SIGMA)
    assert verdict.flagged is True
    assert verdict.reason_code == REASON_TICKER_REUSE
    assert "listing_date" in verdict.triggers
    assert verdict.first == date(2024, 9, 19)
    assert "precedes known listing 2026-06-11" in verdict.detail


def test_first_bar_on_or_after_listing_clears_date_check() -> None:
    bars = _pairs(30, date(2026, 6, 11), start_px=50.0, daily=0.001)
    verdict = check_bar_continuity(bars, listed_on=date(2026, 6, 11))
    assert "listing_date" not in verdict.triggers
    assert verdict.flagged is False


def test_flat_tape_then_jump_flags_n_sigma() -> None:
    # Illiquid ETF: many exact-zero days, then a splice-sized jump.
    start = date(2024, 9, 19)
    bars = [(start + timedelta(days=i), 25.0) for i in range(40)]
    bars.append((start + timedelta(days=40), 25.0 * 1.298))  # +29.8% like SPCX
    verdict = check_bar_continuity(bars, listed_on=None, n_sigma=CONTINUITY_N_SIGMA)
    assert verdict.flagged is True
    assert verdict.reason_code == REASON_TICKER_REUSE
    assert "n_sigma" in verdict.triggers
    assert verdict.max_abs_1bar is not None
    assert verdict.max_abs_1bar > MAD_ZERO_ABS_FLOOR


def test_calm_series_does_not_flag_n_sigma() -> None:
    bars = _pairs(250, date(2024, 9, 19), start_px=100.0, daily=0.0015)
    verdict = check_bar_continuity(bars, listed_on=date(1999, 1, 22), n_sigma=CONTINUITY_N_SIGMA)
    assert verdict.flagged is False
    assert verdict.reason_code == ""
    assert verdict.triggers == ()


def test_ohlcv_bars_and_adapter_helper_agree() -> None:
    start = datetime(2024, 9, 19, tzinfo=timezone.utc)
    raw = []
    px = 10.0
    for i in range(15):
        raw.append(
            OHLCVBar(
                ticker="SPCX",
                open=px,
                high=px + 0.1,
                low=px - 0.1,
                close=px,
                volume=1000.0,
                market_time=start + timedelta(days=i),
                timespan="day",
                multiplier=1,
            )
        )
    listed = date(2026, 6, 11)
    a = check_ohlcv_continuity(raw, listed_on=listed)
    b = PolygonEquitiesAdapter(api_key="unused", env={"POLYGON_API_KEY": "unused"}).continuity_check(
        raw, listed_on=listed
    )
    assert a.flagged is True and b.flagged is True
    assert a.reason_code == b.reason_code == REASON_TICKER_REUSE
    assert a.n_bars == b.n_bars == 15


def test_n_and_method_are_documented_constants() -> None:
    assert CONTINUITY_N_SIGMA == 8.0
    assert MAD_ZERO_ABS_FLOOR == 0.05
