"""PIT filters for macro series and calendar. Knowledge clock is as_of_knowledge."""

from __future__ import annotations

from datetime import datetime

from mm_common.time import as_utc
from mm_macro.models import CalendarEvent, MacroPoint


def visible_points(points: tuple[MacroPoint, ...] | list[MacroPoint], watermark: datetime) -> tuple[MacroPoint, ...]:
    cut = as_utc(watermark)
    return tuple(row for row in points if row.as_of_knowledge <= cut)


def latest_value(points: tuple[MacroPoint, ...] | list[MacroPoint], instrument: str, watermark: datetime) -> MacroPoint | None:
    wanted = instrument.upper()
    vis = [
        row
        for row in visible_points(points, watermark)
        if row.instrument.upper() == wanted and row.value is not None
    ]
    if not vis:
        return None
    vis.sort(key=lambda row: (row.as_of_knowledge, row.observation_id or ""))
    return vis[-1]


def visible_events(events: tuple[CalendarEvent, ...] | list[CalendarEvent], watermark: datetime) -> tuple[CalendarEvent, ...]:
    cut = as_utc(watermark)
    out: list[CalendarEvent] = []
    for row in events:
        known = row.as_of_knowledge or row.ingested_at
        if known is None or known <= cut:
            out.append(row)
    return tuple(out)
