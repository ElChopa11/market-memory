"""Assemble a PIT macro snapshot: series + regime + EVENT_RISK. Never invent."""

from __future__ import annotations

from datetime import datetime

from mm_common.time import as_utc
from mm_macro.calendar import event_risk_at
from mm_macro.config import MacroConfig, load_macro_config
from mm_macro.models import (
    OK,
    PARTIAL,
    UNAVAILABLE,
    CalendarEvent,
    MacroPoint,
    MacroSnapshot,
)
from mm_macro.regime import classify_macro_regime
from mm_macro.series import latest_value, visible_points

CATALOG = ("VIX", "DXY", "US10Y", "US2Y", "T10Y2Y", "HY_OAS", "WTI")


def compute_macro(
    *,
    series: tuple[MacroPoint, ...] | list[MacroPoint],
    calendar: tuple[CalendarEvent, ...] | list[CalendarEvent],
    watermark: datetime,
    config: MacroConfig | None = None,
    repo_root=None,
) -> MacroSnapshot:
    cfg = config or load_macro_config(repo_root)
    cut = as_utc(watermark)
    visible = visible_points(tuple(series), cut)
    values: dict[str, float | None] = {}
    latest: list[MacroPoint] = []
    missing: list[str] = []
    for name in CATALOG:
        point = latest_value(visible, name, cut)
        if point is None:
            values[name] = None
            missing.append(name)
        else:
            values[name] = point.value
            latest.append(point)
    regime = classify_macro_regime(values, watermark=cut, config=cfg)
    risk = event_risk_at(tuple(calendar), watermark=cut, config=cfg)
    if not latest:
        quality = UNAVAILABLE
    elif missing:
        quality = PARTIAL
    else:
        quality = OK
    if regime.status == UNAVAILABLE and quality == OK:
        quality = PARTIAL
    return MacroSnapshot(
        as_of_knowledge=cut,
        config_version=cfg.version,
        data_quality=quality,
        regime=regime,
        event_risk=risk,
        series=tuple(latest),
        missing=tuple(missing),
        payload={"values": values, "fred_series": dict(cfg.fred_series)},
    )
