"""Hyperliquid public-info structure: funding, OI, basis, L2 depth.

Derived values only from public `/info`. Never invent. No signing.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from mm_common.enums import EvidenceType, SourceKind
from mm_common.hashing import normalize_numeric
from mm_common.schemas import ObservationEnvelope
from mm_common.time import from_unix_ms
from mm_provenance.envelope import build_envelope
from mm_provenance.normalize import HL_SOURCE_KIND, HL_SOURCE_NAME, SNAPSHOT_CAPTURE_KIND, SNAPSHOT_EXTRAS


def derive_basis_from_ctx(ctx: dict[str, Any]) -> float | None:
    """(mark - oracle) / oracle when both public fields exist. None → caller degrades."""
    mark = _maybe_float(_first(ctx, "markPx", "mark"))
    oracle = _maybe_float(_first(ctx, "oraclePx", "oracle"))
    if mark is None or oracle is None or oracle == 0:
        return None
    return (mark - oracle) / oracle


def normalize_basis_snapshot(
    meta_and_ctxs: list[Any],
    *,
    instruments: Iterable[str],
    ingested_at: datetime,
    published_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    wanted = {symbol.upper() for symbol in instruments}
    out: list[ObservationEnvelope] = []
    if not isinstance(meta_and_ctxs, list) or len(meta_and_ctxs) < 2:
        for symbol in sorted(wanted):
            out.append(
                _missing_basis(symbol, ingested_at, published_at, stale_after_seconds, missing=("markPx", "oraclePx"))
            )
        return out
    meta, ctxs = meta_and_ctxs[0], meta_and_ctxs[1]
    universe = meta.get("universe", []) if isinstance(meta, dict) else []
    seen: set[str] = set()
    for idx, asset in enumerate(universe):
        name = str(asset.get("name", "")).upper()
        if name not in wanted:
            continue
        seen.add(name)
        ctx = ctxs[idx] if idx < len(ctxs) and isinstance(ctxs[idx], dict) else {}
        basis = derive_basis_from_ctx(ctx)
        missing = () if basis is not None else ("markPx", "oraclePx")
        out.append(
            build_envelope(
                source_name=HL_SOURCE_NAME,
                source_kind=HL_SOURCE_KIND,
                source_url_or_id="metaAndAssetCtxs:basis",
                instrument=name,
                metric="basis_mark_oracle",
                value=normalize_numeric(basis) if basis is not None else None,
                published_at=published_at,
                ingested_at=ingested_at,
                market_time=None,
                payload={
                    "raw": {"markPx": ctx.get("markPx"), "oraclePx": ctx.get("oraclePx"), "premium": ctx.get("premium")},
                    "hl_type": "metaAndAssetCtxs",
                    "capture_kind": SNAPSHOT_CAPTURE_KIND,
                    "derived": True,
                },
                extras=dict(SNAPSHOT_EXTRAS),
                missing_fields=missing,
                stale_after_seconds=stale_after_seconds,
                evidence_type=EvidenceType.DERIVED,
                venue="perp",
            )
        )
    for missing_sym in sorted(wanted - seen):
        out.append(_missing_basis(missing_sym, ingested_at, published_at, stale_after_seconds, missing=("universe",)))
    return out


def normalize_l2_book(
    payload: Any,
    *,
    instrument: str,
    ingested_at: datetime,
    published_at: datetime,
    stale_after_seconds: int = 120,
    levels: int = 5,
) -> list[ObservationEnvelope]:
    """Compact BBO + top-N depth snapshot. Missing book → partial, never invented sizes."""
    coin = str(instrument).upper()
    if not isinstance(payload, dict):
        return [
            build_envelope(
                source_name=HL_SOURCE_NAME,
                source_kind=HL_SOURCE_KIND,
                source_url_or_id="l2Book",
                instrument=coin,
                metric="l2_spread",
                value=None,
                published_at=published_at,
                ingested_at=ingested_at,
                market_time=None,
                payload={"raw": payload, "hl_type": "l2Book", "error_class": "parse_error"},
                extras=dict(SNAPSHOT_EXTRAS),
                missing_fields=("levels",),
                stale_after_seconds=stale_after_seconds,
                venue="perp",
            )
        ]
    time_ms = payload.get("time")
    market_time = from_unix_ms(int(time_ms)) if time_ms is not None else None
    book_levels = payload.get("levels") or []
    bids = book_levels[0] if isinstance(book_levels, list) and len(book_levels) > 0 else []
    asks = book_levels[1] if isinstance(book_levels, list) and len(book_levels) > 1 else []
    bid = _level(bids[0] if bids else None)
    ask = _level(asks[0] if asks else None)
    spread = None
    if bid and ask and bid[0] is not None and ask[0] is not None:
        spread = ask[0] - bid[0]
    compact = {
        "bid_px": bid[0] if bid else None,
        "bid_sz": bid[1] if bid else None,
        "ask_px": ask[0] if ask else None,
        "ask_sz": ask[1] if ask else None,
        "n_bids": min(len(bids), levels) if isinstance(bids, list) else 0,
        "n_asks": min(len(asks), levels) if isinstance(asks, list) else 0,
    }
    extras = dict(SNAPSHOT_EXTRAS)
    if market_time is None:
        extras = dict(SNAPSHOT_EXTRAS)
    missing = () if spread is not None else ("bid", "ask")
    pub = market_time or published_at
    return [
        build_envelope(
            source_name=HL_SOURCE_NAME,
            source_kind=SourceKind.EXCHANGE,
            source_url_or_id=f"l2Book:{coin}",
            instrument=coin,
            metric="l2_spread",
            value=normalize_numeric(spread) if spread is not None else None,
            published_at=pub,
            ingested_at=ingested_at,
            market_time=None if market_time is None else market_time,
            payload={"raw": compact, "hl_type": "l2Book", "capture_kind": SNAPSHOT_CAPTURE_KIND},
            extras=extras,
            missing_fields=missing,
            historical=market_time is not None,
            stale_after_seconds=stale_after_seconds,
            venue="perp",
        )
    ]


def normalize_predicted_fundings(
    payload: Any,
    *,
    instruments: Iterable[str],
    ingested_at: datetime,
    published_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    wanted = {symbol.upper() for symbol in instruments}
    rows = _predicted_rows(payload)
    out: list[ObservationEnvelope] = []
    seen: set[str] = set()
    for coin, rate in rows:
        if coin not in wanted:
            continue
        seen.add(coin)
        out.append(
            build_envelope(
                source_name=HL_SOURCE_NAME,
                source_kind=HL_SOURCE_KIND,
                source_url_or_id=f"predictedFundings:{coin}",
                instrument=coin,
                metric="predicted_funding",
                value=normalize_numeric(rate) if rate is not None else None,
                published_at=published_at,
                ingested_at=ingested_at,
                market_time=None,
                payload={"hl_type": "predictedFundings", "capture_kind": SNAPSHOT_CAPTURE_KIND},
                extras=dict(SNAPSHOT_EXTRAS),
                missing_fields=() if rate is not None else ("predicted_funding",),
                stale_after_seconds=stale_after_seconds,
                venue="perp",
            )
        )
    for missing_sym in sorted(wanted - seen):
        out.append(
            build_envelope(
                source_name=HL_SOURCE_NAME,
                source_kind=HL_SOURCE_KIND,
                source_url_or_id=f"predictedFundings:{missing_sym}",
                instrument=missing_sym,
                metric="predicted_funding",
                value=None,
                published_at=published_at,
                ingested_at=ingested_at,
                market_time=None,
                payload={"hl_type": "predictedFundings", "error_class": "parse_error"},
                extras=dict(SNAPSHOT_EXTRAS),
                missing_fields=("predicted_funding",),
                stale_after_seconds=stale_after_seconds,
                venue="perp",
            )
        )
    return out


def _missing_basis(
    symbol: str,
    ingested_at: datetime,
    published_at: datetime,
    stale_after_seconds: int,
    *,
    missing: tuple[str, ...],
) -> ObservationEnvelope:
    return build_envelope(
        source_name=HL_SOURCE_NAME,
        source_kind=HL_SOURCE_KIND,
        source_url_or_id="metaAndAssetCtxs:basis",
        instrument=symbol,
        metric="basis_mark_oracle",
        value=None,
        published_at=published_at,
        ingested_at=ingested_at,
        market_time=None,
        payload={"hl_type": "metaAndAssetCtxs", "derived": True, "error_class": "parse_error"},
        extras=dict(SNAPSHOT_EXTRAS),
        missing_fields=missing,
        stale_after_seconds=stale_after_seconds,
        evidence_type=EvidenceType.DERIVED,
        venue="perp",
    )


def _level(row: Any) -> tuple[float | None, float | None] | None:
    if not isinstance(row, dict):
        return None
    return _maybe_float(row.get("px")), _maybe_float(row.get("sz"))


def _predicted_rows(payload: Any) -> list[tuple[str, float | None]]:
    out: list[tuple[str, float | None]] = []
    if isinstance(payload, dict):
        for coin, body in payload.items():
            rate = _funding_from_predicted(body)
            out.append((str(coin).upper(), rate))
        return out
    if not isinstance(payload, list):
        return out
    for row in payload:
        if isinstance(row, dict) and "coin" in row:
            out.append((str(row.get("coin", "")).upper(), _funding_from_predicted(row)))
            continue
        if isinstance(row, list) and len(row) >= 2:
            coin = str(row[0]).upper()
            out.append((coin, _funding_from_predicted(row[1])))
    return out


def _funding_from_predicted(body: Any) -> float | None:
    if body is None:
        return None
    if isinstance(body, (int, float, str)):
        return _maybe_float(body)
    if isinstance(body, dict):
        return _maybe_float(body.get("fundingRate") or body.get("predictedFunding") or body.get("funding"))
    if isinstance(body, list) and body:
        first = body[0]
        if isinstance(first, dict):
            return _maybe_float(first.get("fundingRate") or first.get("predictedFunding"))
    return None


def _first(ctx: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in ctx and ctx[key] is not None:
            return ctx[key]
    return None


def _maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
