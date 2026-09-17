"""DST-correct Market Pulse fire times (America/New_York wall clock → UTC / Sydney)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from mm_common.time import as_utc
from mm_briefing.config import PulseSchedule
from mm_briefing.models import Fire, SessionStatus

UTC = timezone.utc
NY_TZ = ZoneInfo("America/New_York")
SYDNEY_TZ = ZoneInfo("Australia/Sydney")
WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
WEEKDAY_SESSION = ("Mon", "Tue", "Wed", "Thu", "Fri")

# US cash session (NYSE) wall clocks in America/New_York. zoneinfo applies DST.
PREMARKET_OPEN = time(4, 0)
CASH_OPEN = time(9, 30)
CASH_CLOSE = time(16, 0)
AFTER_HOURS_END = time(20, 0)


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


def _fmt_offset(delta: timedelta | None) -> str:
    if delta is None:
        return "+00:00"
    total = int(delta.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    hours, rem = divmod(total, 3600)
    minutes = rem // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def us_session_status(ts: datetime, *, session_tz: str = "America/New_York") -> SessionStatus:
    """US-session status at *ts*. DST is whatever zoneinfo says for America/New_York."""
    tz = zone(session_tz)
    local = as_utc(ts).astimezone(tz)
    weekday = WEEKDAY_NAMES[local.weekday()]
    clock = time(local.hour, local.minute, local.second)
    if weekday not in WEEKDAY_SESSION:
        code = "weekend_closed"
        label = "Weekend — US cash session closed"
    elif CASH_OPEN <= clock < CASH_CLOSE:
        code = "regular_hours"
        label = "Regular hours (NYSE cash session 09:30–16:00)"
    elif PREMARKET_OPEN <= clock < CASH_OPEN:
        code = "pre_market"
        label = "US pre-market (04:00–09:30 before cash open)"
    elif CASH_CLOSE <= clock < AFTER_HOURS_END:
        code = "after_hours"
        label = "US after-hours (16:00–20:00 after cash close)"
    else:
        code = "overnight_closed"
        label = "Overnight — US cash session closed"
    tzname = local.tzname() or session_tz
    return SessionStatus(
        code=code,
        label=label,
        timezone=session_tz,
        tzname=tzname,
        utc_offset=_fmt_offset(local.utcoffset()),
        cash_open="09:30",
        cash_close="16:00",
        local=local,
    )


def prior_us_cash_close(ts: datetime, *, session_tz: str = "America/New_York") -> datetime:
    """Previous weekday 16:00 in the US session timezone (DST-correct)."""
    tz = zone(session_tz)
    local = as_utc(ts).astimezone(tz)
    day = local.date()
    close_today = session_local(day, CASH_CLOSE.hour, CASH_CLOSE.minute, 0, tz)
    if local < close_today:
        day = day - timedelta(days=1)
    while WEEKDAY_NAMES[day.weekday()] not in WEEKDAY_SESSION:
        day = day - timedelta(days=1)
    return session_local(day, CASH_CLOSE.hour, CASH_CLOSE.minute, 0, tz).astimezone(UTC)
