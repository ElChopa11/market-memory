"""Equities adapter registry. Default vendor = Polygon (Principal lock; Ask is N/A)."""

from __future__ import annotations

from mm_ingest.equities.interface import DEFAULT_EQUITIES_VENDOR, EquitiesAdapter
from mm_ingest.equities.polygon import PolygonEquitiesAdapter

_ADAPTERS: dict[str, type] = {
    "polygon": PolygonEquitiesAdapter,
}


def get_equities_adapter(vendor: str | None = None, **kwargs) -> EquitiesAdapter:
    name = (vendor or DEFAULT_EQUITIES_VENDOR).strip().lower()
    if name not in _ADAPTERS:
        # Do not silently invent a vendor. Polygon is the locked default.
        name = DEFAULT_EQUITIES_VENDOR
    return _ADAPTERS[name](**kwargs)
