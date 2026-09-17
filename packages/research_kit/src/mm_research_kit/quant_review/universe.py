"""Load and normalize the Quant Review Board universe."""

from __future__ import annotations

from typing import Any

from mm_research_kit.errors import GateError
from mm_research_kit.quant_review.models import InstrumentSpec, QuantTrack, TRACK_VALUES, UniverseSpec


def universe_from_mapping(data: dict[str, Any]) -> UniverseSpec:
    if not isinstance(data, dict):
        raise GateError("quant review universe must be a mapping")
    raw_map = data.get("symbol_map") or {}
    if not isinstance(raw_map, dict) or not raw_map:
        raise GateError("quant review universe needs symbol_map")
    symbol_map = {str(k).strip().upper(): str(v).strip().upper() for k, v in raw_map.items()}
    instruments: list[InstrumentSpec] = []
    seen: set[str] = set()
    for row in data.get("instruments") or []:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "").strip().upper()
        if not symbol:
            raise GateError("universe instrument missing symbol")
        if symbol in seen:
            raise GateError(f"duplicate universe symbol {symbol}")
        seen.add(symbol)
        tracks = tuple(str(t).strip().upper() for t in (row.get("tracks") or []))
        for track in tracks:
            if track not in TRACK_VALUES:
                raise GateError(f"unknown track {track!r} on {symbol}")
        raw_symbols = tuple(str(s).strip() for s in (row.get("raw_symbols") or [symbol]))
        peers = tuple(str(p).strip().upper() for p in (row.get("peers") or []) if str(p).strip())
        instruments.append(
            InstrumentSpec(
                symbol=symbol,
                raw_symbols=raw_symbols,
                asset_class=str(row.get("asset_class") or "unknown"),
                venue=str(row.get("venue") or "unknown"),
                sector=str(row.get("sector") or "unknown"),
                benchmark=str(row.get("benchmark") or symbol).strip().upper(),
                peers=peers,
                tracks=tracks or (QuantTrack.A.value,),
                post_ipo=bool(row.get("post_ipo")),
                listing_date=(str(row["listing_date"]) if row.get("listing_date") else None),
                role=str(row.get("role") or "name"),
            )
        )
    if not instruments:
        raise GateError("quant review universe has no instruments")
    peer_groups = {
        str(name): tuple(str(s).strip().upper() for s in (members or []))
        for name, members in (data.get("peer_groups") or {}).items()
    }
    arb_pairs: list[tuple[str, str, str]] = []
    for pair in data.get("arb_pairs") or []:
        if not isinstance(pair, dict):
            continue
        left = str(pair.get("left") or "").strip().upper()
        right = str(pair.get("right") or "").strip().upper()
        if left and right:
            arb_pairs.append((left, right, str(pair.get("note") or "")))
    notes = tuple(str(n) for n in (data.get("notes") or []) if n)
    provenance = tuple(row for row in (data.get("provenance") or []) if isinstance(row, dict))
    return UniverseSpec(
        version=str(data.get("version") or "unknown"),
        status=str(data.get("status") or "unknown"),
        kind=str(data.get("kind") or "quant_review"),
        instruments=tuple(instruments),
        symbol_map=symbol_map,
        peer_groups=peer_groups,
        arb_pairs=tuple(arb_pairs),
        notes=notes,
        provenance=provenance,
    )


def normalize_symbol(raw: str, symbol_map: dict[str, str]) -> str:
    key = raw.strip().upper()
    if key in symbol_map:
        return symbol_map[key]
    # Heuristic fallback — still prefer the explicit map.
    if key.endswith("USDC.P"):
        return key[: -len("USDC.P")]
    if key.endswith("USDT.F"):
        return key[: -len("USDT.F")]
    if key.endswith("1!"):
        return key[:-2]
    return key


def counterpart(symbol: str, universe: UniverseSpec) -> str | None:
    for left, right, _note in universe.arb_pairs:
        if symbol == left:
            return right
        if symbol == right:
            return left
    return None
