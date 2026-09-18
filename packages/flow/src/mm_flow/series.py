"""Point-in-time helpers for flow. Knowledge clock is as_of_knowledge."""

from __future__ import annotations

from datetime import datetime

from mm_common.time import as_utc
from mm_quant.models import MarketPanel, SeriesBar, StructurePoint
from mm_quant.series import bars_for, visible_bars, visible_panel, visible_structure


def points_for(
    panel: MarketPanel,
    instrument: str,
    metric: str | tuple[str, ...],
    watermark: datetime,
) -> tuple[StructurePoint, ...]:
    wanted = instrument.upper()
    names = (metric,) if isinstance(metric, str) else tuple(metric)
    vis = visible_structure(panel.structure, watermark)
    matches = [
        point
        for point in vis
        if point.instrument.upper() == wanted and point.metric in names and point.value is not None
    ]
    matches.sort(key=lambda point: (point.as_of_knowledge, point.observation_id or ""))
    return tuple(matches)


def latest_point(
    panel: MarketPanel,
    instrument: str,
    metric: str | tuple[str, ...],
    watermark: datetime,
) -> StructurePoint | None:
    rows = points_for(panel, instrument, metric, watermark)
    return rows[-1] if rows else None


def visible_closes(panel: MarketPanel, instrument: str, watermark: datetime) -> tuple[SeriesBar, ...]:
    vis = visible_panel(panel, watermark)
    return bars_for(vis, instrument)


__all__ = [
    "bars_for",
    "latest_point",
    "points_for",
    "visible_bars",
    "visible_closes",
    "visible_panel",
    "visible_structure",
    "as_utc",
]
