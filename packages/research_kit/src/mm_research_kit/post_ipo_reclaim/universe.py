"""Load the screen-only Post-IPO / reclaim universe. Not Principal membership."""

from __future__ import annotations

from typing import Any

from mm_research_kit.errors import GateError
from mm_research_kit.post_ipo_reclaim.models import (
    MEMBERSHIP_VALUES,
    STALE_AFTER_HOURS_DEFAULT,
    ScreenContextName,
    ScreenInstrument,
    ScreenRole,
    ScreenUniverse,
)
from mm_research_kit.quant_review.universe import normalize_symbol


def universe_from_mapping(data: dict[str, Any]) -> ScreenUniverse:
    if not isinstance(data, dict):
        raise GateError("post-IPO reclaim universe must be a mapping")
    kind = str(data.get("kind") or "")
    status = str(data.get("status") or "")
    if kind != "post_ipo_reclaim_screen":
        raise GateError("screen universe kind must be post_ipo_reclaim_screen")
    if status != "screen_only":
        raise GateError("screen universe status must be screen_only (not Principal membership)")
    raw_map = data.get("symbol_map") or {}
    if not isinstance(raw_map, dict) or not raw_map:
        raise GateError("screen universe needs symbol_map")
    symbol_map = {str(k).strip().upper(): str(v).strip().upper() for k, v in raw_map.items()}
    instruments: list[ScreenInstrument] = []
    seen: set[str] = set()
    for row in data.get("instruments") or []:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "").strip().upper()
        if not symbol:
            raise GateError("screen instrument missing symbol")
        if symbol in seen:
            raise GateError(f"duplicate screen symbol {symbol}")
        seen.add(symbol)
        membership = str(row.get("membership") or "screen_only")
        if membership not in MEMBERSHIP_VALUES:
            raise GateError(f"unknown membership {membership!r} on {symbol}")
        role = str(row.get("role") or ScreenRole.CANDIDATE.value)
        raw_symbols = tuple(str(s).strip() for s in (row.get("raw_symbols") or [symbol]))
        peers = tuple(str(p).strip().upper() for p in (row.get("peers") or []) if str(p).strip())
        instruments.append(
            ScreenInstrument(
                symbol=symbol,
                raw_symbols=raw_symbols,
                asset_class=str(row.get("asset_class") or "equity"),
                venue=str(row.get("venue") or "unknown"),
                sector=str(row.get("sector") or "unknown"),
                benchmark=str(row.get("benchmark") or "").strip().upper(),
                peers=peers,
                post_ipo=bool(row.get("post_ipo", True)),
                listing_date=(str(row["listing_date"]) if row.get("listing_date") else None),
                role=role,
                membership=membership,
                notes=str(row.get("notes") or ""),
            )
        )
    if not instruments:
        raise GateError("post-IPO reclaim screen has no candidate instruments")
    context: list[ScreenContextName] = []
    for row in data.get("context") or []:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "").strip().upper()
        if not symbol:
            continue
        context.append(
            ScreenContextName(
                symbol=symbol,
                role=str(row.get("role") or ScreenRole.PEER.value),
                asset_class=str(row.get("asset_class") or "unknown"),
            )
        )
    notes = tuple(_note_text(n) for n in (data.get("notes") or []) if n)
    provenance = tuple(row for row in (data.get("provenance") or []) if isinstance(row, dict))
    stale = int(data.get("stale_after_hours") or STALE_AFTER_HOURS_DEFAULT)
    return ScreenUniverse(
        version=str(data.get("version") or "unknown"),
        status=status,
        kind=kind,
        desk=str(data.get("desk") or "Equities & Post-IPO Desk"),
        locked_membership_file=str(data.get("locked_membership_file") or "config/universe.yaml"),
        instruments=tuple(instruments),
        context=tuple(context),
        symbol_map=symbol_map,
        notes=notes,
        provenance=provenance,
        stale_after_hours=stale,
        )


def _note_text(value: Any) -> str:
    if isinstance(value, dict) and len(value) == 1:
        key, val = next(iter(value.items()))
        return f"{key}: {val}"
    return str(value)


__all__ = ["normalize_symbol", "universe_from_mapping"]
