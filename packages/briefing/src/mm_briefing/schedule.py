"""DST-correct Market Pulse fire times (America/New_York wall clock → UTC / Sydney)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from mm_common.time import as_utc
from mm_briefing.config import PulseSchedule
from mm_briefing.models import Fire

UTC = timezone.utc
NY_TZ = ZoneInfo("America/New_York")
SYDNEY_TZ = ZoneInfo("Australia/Sydney")
WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def zone(name: str) -> ZoneInfo:
    return ZoneInfo(name)


def session_local(day: date, hour: int, minute: int, second: int, tz: ZoneInfo) -> datetime:
    """Construct a timezone-aware local datetime. zoneinfo folds/skips DST gaps."""
    return datetime(day.year, day.month, day.day, hour, minute, second, tzinfo=tz)


def fires_between(
    start: datetime,
    end: datetime,
    schedule: PulseSchedule,
    *,
    kinds: tuple[str, ...] | None = None,
) -> list[Fire]:
    """Inclusive start, exclusive end. Times are converted via zoneinfo (DST-safe)."""
    start_u = as_utc(start)
    end_u = as_utc(end)
    session_tz = zone(schedule.session_timezone)
    lab_tz = zone(schedule.lab_timezone)
    start_local = start_u.astimezone(session_tz).date() - timedelta(days=1)
    end_local = end_u.astimezone(session_tz).date() + timedelta(days=1)
    out: list[Fire] = []
    day = start_local
    while day <= end_local:
        weekday = WEEKDAY_NAMES[day.weekday()]
        for spec in schedule.jobs:
            if not spec.enabled:
                continue
            if kinds is not None and spec.kind not in kinds:
                continue
            if weekday not in spec.weekdays:
                continue
            local = session_local(
                day,
                spec.local_time.hour,
                spec.local_time.minute,
                spec.local_time.second,
                session_tz,
            )
            when_utc = local.astimezone(UTC)
            if start_u <= when_utc < end_u:
                out.append(
                    Fire(
                        kind=spec.kind,
                        when_utc=when_utc,
                        when_session=local,
                        when_lab=when_utc.astimezone(lab_tz),
                        session_date=day,
                    )
                )
        day += timedelta(days=1)
    return sorted(out, key=lambda row: (row.when_utc, row.kind))


def next_fire(
    now: datetime,
    schedule: PulseSchedule,
    *,
    kinds: tuple[str, ...] | None = None,
    horizon_days: int = 14,
) -> Fire | None:
    now_u = as_utc(now)
    rows = fires_between(now_u, now_u + timedelta(days=horizon_days), schedule, kinds=kinds)
    return rows[0] if rows else None


def session_date_for(ts: datetime, schedule: PulseSchedule | None = None) -> date:
    tz_name = schedule.session_timezone if schedule is not None else "America/New_York"
    return as_utc(ts).astimezone(zone(tz_name)).date()
