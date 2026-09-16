"""DST-correct Market Pulse fire times across a US spring-forward."""

from __future__ import annotations

from datetime import datetime, timezone

from mm_briefing.config import load_schedule
from mm_briefing.schedule import fires_between, next_fire


def test_preopen_utc_shifts_one_hour_across_us_dst() -> None:
    schedule = load_schedule()
    start = datetime(2026, 3, 6, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc)
    fires = fires_between(start, end, schedule)
    preopens = [row for row in fires if row.kind == "preopen"]
    closes = [row for row in fires if row.kind == "close"]

    # Weekdays only: Fri 6, Mon 9, Tue 10. Sun 8 is the DST jump and must not fire.
    assert [row.session_date.isoformat() for row in preopens] == ["2026-03-06", "2026-03-09", "2026-03-10"]
    assert [row.session_date.isoformat() for row in closes] == ["2026-03-06", "2026-03-09", "2026-03-10"]

    friday = preopens[0]
    monday = preopens[1]
    # 08:00 America/New_York: EST (UTC-5) before the jump, EDT (UTC-4) after.
    assert friday.when_utc == datetime(2026, 3, 6, 13, 0, tzinfo=timezone.utc)
    assert monday.when_utc == datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
    assert friday.when_session.hour == 8 and friday.when_session.minute == 0
    assert monday.when_session.hour == 8 and monday.when_session.minute == 0
    assert friday.when_session.tzname() == "EST"
    assert monday.when_session.tzname() == "EDT"

    # Lab clocks (Australia/Sydney still on AEDT through early April).
    assert friday.when_lab.tzname() in {"AEDT", "AEDT"}
    assert friday.when_lab.hour == 0 and friday.when_lab.day == 7
    assert monday.when_lab.hour == 23 and monday.when_lab.day == 9

    friday_close = closes[0]
    monday_close = closes[1]
    assert friday_close.when_utc == datetime(2026, 3, 6, 21, 15, tzinfo=timezone.utc)
    assert monday_close.when_utc == datetime(2026, 3, 9, 20, 15, tzinfo=timezone.utc)
    assert friday_close.when_session.hour == 16 and friday_close.when_session.minute == 15
    assert monday_close.when_session.hour == 16 and monday_close.when_session.minute == 15


def test_no_weekend_fires_on_dst_sunday() -> None:
    schedule = load_schedule()
    start = datetime(2026, 3, 8, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 3, 9, 0, 0, tzinfo=timezone.utc)
    assert fires_between(start, end, schedule) == []


def test_next_fire_after_dst_jump_is_monday_preopen() -> None:
    schedule = load_schedule()
    now = datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc)
    nxt = next_fire(now, schedule)
    assert nxt is not None
    assert nxt.kind == "preopen"
    assert nxt.when_utc == datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
    assert nxt.session_date.isoformat() == "2026-03-09"
