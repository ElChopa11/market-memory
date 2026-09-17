"""Macro calendar: fixture file today, pluggable source tomorrow."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from mm_common.time import as_utc, parse_utc
from mm_briefing.models import CalendarEvent


DEFAULT_CALENDAR_SOURCE = "config/briefing/calendar.yaml"


def events_from_rows(
    rows: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    *,
    source: str = DEFAULT_CALENDAR_SOURCE,
) -> tuple[CalendarEvent, ...]:
    out: list[CalendarEvent] = []
    for row in rows:
        when_raw = row.get("when") or row.get("datetime")
        if not when_raw:
            continue
        when = parse_utc(str(when_raw)) if not isinstance(when_raw, datetime) else as_utc(when_raw)
        out.append(
            CalendarEvent(
                when=when,
                name=str(row.get("name") or "event"),
                importance=str(row.get("importance") or "medium").lower(),
                region=str(row.get("region") or "US"),
                notes=str(row.get("notes") or ""),
                source=str(row.get("source") or source),
            )
        )
    return tuple(sorted(out, key=lambda event: (event.when, event.name)))


def relevant_events(
    events: tuple[CalendarEvent, ...],
    *,
    as_of: datetime,
    horizon_hours: int = 36,
    lookback_hours: int = 6,
) -> tuple[CalendarEvent, ...]:
    start = as_utc(as_of) - timedelta(hours=lookback_hours)
    end = as_utc(as_of) + timedelta(hours=horizon_hours)
    return tuple(event for event in events if start <= event.when <= end)
