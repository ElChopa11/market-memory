"""US session status and prior-close clocks — DST via zoneinfo."""

from __future__ import annotations

from datetime import datetime, timezone

from mm_briefing.schedule import prior_us_cash_close, us_session_status


UTC = timezone.utc


def test_pre_market_status_on_frozen_fixture_morning() -> None:
    # 2026-03-10 12:00 UTC = 08:00 EDT (DST already on).
    status = us_session_status(datetime(2026, 3, 10, 12, 0, tzinfo=UTC))
    assert status.code == "pre_market"
    assert status.tzname == "EDT"
    assert status.utc_offset == "-04:00"
    assert status.cash_open == "09:30"
    assert status.cash_close == "16:00"
    assert "pre-market" in status.label.lower()


def test_regular_hours_and_after_hours() -> None:
    rth = us_session_status(datetime(2026, 3, 10, 14, 0, tzinfo=UTC))  # 10:00 EDT
    assert rth.code == "regular_hours"
    after = us_session_status(datetime(2026, 3, 10, 21, 0, tzinfo=UTC))  # 17:00 EDT
    assert after.code == "after_hours"
    overnight = us_session_status(datetime(2026, 3, 11, 2, 0, tzinfo=UTC))  # 22:00 EDT
    assert overnight.code == "overnight_closed"


def test_weekend_closed_on_dst_sunday() -> None:
    status = us_session_status(datetime(2026, 3, 8, 13, 0, tzinfo=UTC))
    assert status.code == "weekend_closed"


def test_session_status_tzname_shifts_across_spring_forward() -> None:
    friday = us_session_status(datetime(2026, 3, 6, 13, 0, tzinfo=UTC))  # 08:00 EST
    monday = us_session_status(datetime(2026, 3, 9, 12, 0, tzinfo=UTC))  # 08:00 EDT
    assert friday.tzname == "EST"
    assert friday.utc_offset == "-05:00"
    assert friday.code == "pre_market"
    assert monday.tzname == "EDT"
    assert monday.utc_offset == "-04:00"
    assert monday.code == "pre_market"


def test_session_status_tzname_shifts_across_fall_back() -> None:
    # US DST ends 2026-11-01 02:00 local.
    friday = us_session_status(datetime(2026, 10, 30, 12, 0, tzinfo=UTC))  # 08:00 EDT
    monday = us_session_status(datetime(2026, 11, 2, 13, 0, tzinfo=UTC))  # 08:00 EST
    assert friday.tzname == "EDT"
    assert friday.utc_offset == "-04:00"
    assert monday.tzname == "EST"
    assert monday.utc_offset == "-05:00"


def test_prior_us_cash_close_skips_weekend_and_uses_1600_et() -> None:
    # Monday 2026-03-09 08:00 EDT preopen → Friday 2026-03-06 16:00 EST = 21:00 UTC.
    prior = prior_us_cash_close(datetime(2026, 3, 9, 12, 0, tzinfo=UTC))
    assert prior == datetime(2026, 3, 6, 21, 0, tzinfo=UTC)
    # Tuesday 2026-03-10 08:00 EDT → Monday 2026-03-09 16:00 EDT = 20:00 UTC.
    prior_tue = prior_us_cash_close(datetime(2026, 3, 10, 12, 0, tzinfo=UTC))
    assert prior_tue == datetime(2026, 3, 9, 20, 0, tzinfo=UTC)
