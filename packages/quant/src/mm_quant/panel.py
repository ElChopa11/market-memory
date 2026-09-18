"""Load a Phase 5c MarketPanel from JSON. No network. Missing fields stay missing."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from mm_common.time import parse_utc
from mm_quant.models import MarketPanel, SeriesBar, StructurePoint


def _ts(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return parse_utc(str(value))


def _bar(raw: dict[str, Any], *, fixture_id: str | None) -> SeriesBar:
    as_of = raw.get("as_of_knowledge") or raw.get("ingested_at") or raw.get("available_at")
    if as_of is None:
        raise ValueError("bar missing as_of_knowledge/ingested_at/available_at")
    ingested = raw.get("ingested_at") or as_of
    return SeriesBar(
        instrument=str(raw["instrument"]).upper(),
        market_time=_ts(raw["market_time"]),
        as_of_knowledge=_ts(as_of),
        ingested_at=_ts(ingested),
        open=None if raw.get("o", raw.get("open")) is None else float(raw.get("o", raw.get("open"))),
        high=None if raw.get("h", raw.get("high")) is None else float(raw.get("h", raw.get("high"))),
        low=None if raw.get("l", raw.get("low")) is None else float(raw.get("l", raw.get("low"))),
        close=float(raw.get("c", raw.get("close"))),
        volume=None if raw.get("v", raw.get("volume")) is None else float(raw.get("v", raw.get("volume"))),
        observation_id=None if raw.get("observation_id") is None else str(raw.get("observation_id")),
        fixture_id=str(raw.get("fixture_id") or fixture_id) if (raw.get("fixture_id") or fixture_id) else None,
        asset_class=str(raw.get("asset_class") or "unknown"),
    )


def _structure(raw: dict[str, Any], *, fixture_id: str | None) -> StructurePoint:
    as_of = raw.get("as_of_knowledge") or raw.get("ingested_at")
    if as_of is None:
        raise ValueError("structure point missing as_of_knowledge")
    value = raw.get("value")
    return StructurePoint(
        instrument=str(raw["instrument"]).upper(),
        metric=str(raw["metric"]),
        as_of_knowledge=_ts(as_of),
        ingested_at=_ts(raw.get("ingested_at") or as_of),
        value=None if value is None else float(value),
        observation_id=None if raw.get("observation_id") is None else str(raw.get("observation_id")),
        fixture_id=str(raw.get("fixture_id") or fixture_id) if (raw.get("fixture_id") or fixture_id) else None,
        data_quality=str(raw.get("data_quality") or "ok"),
    )


def panel_from_mapping(data: dict[str, Any]) -> MarketPanel:
    fixture_id = None if data.get("fixture_id") is None else str(data.get("fixture_id"))
    bars = tuple(_bar(row, fixture_id=fixture_id) for row in (data.get("bars") or []))
    structure = tuple(_structure(row, fixture_id=fixture_id) for row in (data.get("structure") or []))
    return MarketPanel(
        bars=bars,
        structure=structure,
        fixture_id=fixture_id,
        sector_of={str(k).upper(): str(v) for k, v in (data.get("sector_of") or {}).items()},
        asset_class_of={str(k).upper(): str(v) for k, v in (data.get("asset_class_of") or {}).items()},
    )


def load_panel_file(path: Path) -> MarketPanel:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON object")
    if not data.get("fixture_id"):
        data = dict(data)
        data["fixture_id"] = path.stem
    return panel_from_mapping(data)
