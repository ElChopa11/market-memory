"""Normalize Hyperliquid public info payloads into observation envelopes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from mm_common.enums import EvidenceType, SourceKind
from mm_common.hashing import normalize_numeric
from mm_common.schemas import ObservationEnvelope
from mm_common.time import from_unix_ms
from mm_provenance.envelope import build_envelope

HL_SOURCE_NAME = "hyperliquid.info"
HL_SOURCE_KIND = SourceKind.EXCHANGE
HL_BASE_URL = "https://api.hyperliquid.xyz/info"
HL_TOS_NOTES = "Public /info endpoint only. ToS-lawful collection. No user-private or signing endpoints."

SNAPSHOT_METRICS = ("mid_px", "mark_px", "oracle_px", "funding", "open_interest")


def _ctx_value(ctx: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in ctx and ctx[key] is not None:
            return ctx[key]
    return None


def normalize_asset_snapshot(
    meta_and_ctxs: list[Any],
    *,
    instruments: Iterable[str],
    ingested_at: datetime,
    published_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    """metaAndAssetCtxs → mid/mark/oracle/funding/OI observations for configured perps."""
    wanted = {symbol.upper() for symbol in instruments}
    if not isinstance(meta_and_ctxs, list) or len(meta_and_ctxs) < 2:
        return [
            _missing_universe(symbol, ingested_at, published_at, stale_after_seconds) for symbol in sorted(wanted)
        ]
    meta, ctxs = meta_and_ctxs[0], meta_and_ctxs[1]
    universe = meta.get("universe", []) if isinstance(meta, dict) else []
    envelopes: list[ObservationEnvelope] = []
    seen: set[str] = set()
    for idx, asset in enumerate(universe):
        name = str(asset.get("name", "")).upper()
        if name not in wanted:
            continue
        seen.add(name)
        ctx = ctxs[idx] if idx < len(ctxs) else {}
        envelopes.extend(
            _snapshot_for_coin(
                name,
                ctx if isinstance(ctx, dict) else {},
                ingested_at=ingested_at,
                published_at=published_at,
                stale_after_seconds=stale_after_seconds,
            )
        )
    for missing in sorted(wanted - seen):
        envelopes.append(_missing_universe(missing, ingested_at, published_at, stale_after_seconds))
    return envelopes


def _missing_universe(
    symbol: str,
    ingested_at: datetime,
    published_at: datetime,
    stale_after_seconds: int,
) -> ObservationEnvelope:
    return build_envelope(
        source_name=HL_SOURCE_NAME,
        source_kind=HL_SOURCE_KIND,
        source_url_or_id="metaAndAssetCtxs",
        instrument=symbol,
        metric="universe",
        value=None,
        published_at=published_at,
        ingested_at=ingested_at,
        market_time=published_at,
        payload={"reason": "instrument missing from Hyperliquid universe"},
        missing_fields=("universe",),
        stale_after_seconds=stale_after_seconds,
        confidence=0.2,
        evidence_type=EvidenceType.FACT,
    )


def _snapshot_for_coin(
    symbol: str,
    ctx: dict[str, Any],
    *,
    ingested_at: datetime,
    published_at: datetime,
    stale_after_seconds: int,
) -> list[ObservationEnvelope]:
    field_map = {
        "mid_px": ("midPx", "mid"),
        "mark_px": ("markPx", "mark"),
        "oracle_px": ("oraclePx", "oracle"),
        "funding": ("funding",),
        "open_interest": ("openInterest", "open_interest"),
    }
    out: list[ObservationEnvelope] = []
    for metric, keys in field_map.items():
        raw = _ctx_value(ctx, *keys)
        missing = () if raw is not None else keys
        out.append(
            build_envelope(
                source_name=HL_SOURCE_NAME,
                source_kind=HL_SOURCE_KIND,
                source_url_or_id="metaAndAssetCtxs",
                instrument=symbol,
                metric=metric,
                value=normalize_numeric(raw) if raw is not None else None,
                published_at=published_at,
                ingested_at=ingested_at,
                market_time=published_at,
                payload={"raw": ctx, "hl_type": "metaAndAssetCtxs"},
                historical=False,
                missing_fields=missing,
                stale_after_seconds=stale_after_seconds,
            )
        )
    return out


def normalize_all_mids(
    mids: dict[str, Any],
    *,
    instruments: Iterable[str],
    ingested_at: datetime,
    published_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    wanted = {symbol.upper() for symbol in instruments}
    out: list[ObservationEnvelope] = []
    for symbol in sorted(wanted):
        raw = mids.get(symbol) if isinstance(mids, dict) else None
        missing = () if raw is not None else ("mid",)
        out.append(
            build_envelope(
                source_name=HL_SOURCE_NAME,
                source_kind=HL_SOURCE_KIND,
                source_url_or_id="allMids",
                instrument=symbol,
                metric="mid_px",
                value=normalize_numeric(raw) if raw is not None else None,
                published_at=published_at,
                ingested_at=ingested_at,
                market_time=published_at,
                payload={"raw": raw, "hl_type": "allMids"},
                missing_fields=missing,
                stale_after_seconds=stale_after_seconds,
            )
        )
    return out


def normalize_funding_history(
    rows: list[dict[str, Any]],
    *,
    ingested_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    out: list[ObservationEnvelope] = []
    for row in rows:
        coin = str(row.get("coin", "")).upper()
        time_ms = row.get("time")
        if not coin or time_ms is None:
            continue
        market_time = from_unix_ms(int(time_ms))
        row_ingested = _row_ingested_at(row, ingested_at)
        out.append(
            build_envelope(
                source_name=HL_SOURCE_NAME,
                source_kind=HL_SOURCE_KIND,
                source_url_or_id=f"fundingHistory:{coin}:{time_ms}",
                instrument=coin,
                metric="funding",
                value=normalize_numeric(row.get("fundingRate")),
                published_at=market_time,
                ingested_at=row_ingested,
                market_time=market_time,
                payload={"raw": row, "hl_type": "fundingHistory", "premium": row.get("premium")},
                extras={},
                historical=True,
                missing_fields=() if row.get("fundingRate") is not None else ("fundingRate",),
                stale_after_seconds=stale_after_seconds,
            )
        )
    return out


def normalize_candles(
    rows: list[dict[str, Any]],
    *,
    ingested_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    out: list[ObservationEnvelope] = []
    for row in rows:
        coin = str(row.get("s") or row.get("coin") or "").upper()
        time_ms = row.get("t") or row.get("time")
        close = row.get("c") or row.get("close")
        if not coin or time_ms is None:
            continue
        market_time = from_unix_ms(int(time_ms))
        row_ingested = _row_ingested_at(row, ingested_at)
        interval = str(row.get("i") or row.get("interval") or "")
        extras = {"interval": interval} if interval else {}
        out.append(
            build_envelope(
                source_name=HL_SOURCE_NAME,
                source_kind=HL_SOURCE_KIND,
                source_url_or_id=f"candleSnapshot:{coin}:{time_ms}",
                instrument=coin,
                metric="candle_close",
                value=normalize_numeric(close),
                published_at=market_time,
                ingested_at=row_ingested,
                market_time=market_time,
                payload={"raw": row, "hl_type": "candleSnapshot"},
                extras=extras,
                historical=True,
                missing_fields=() if close is not None else ("c",),
                stale_after_seconds=stale_after_seconds,
            )
        )
    return out


def normalize_liquidations(
    trades: list[dict[str, Any]],
    *,
    ingested_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    """Keep trades that carry a public `liquidation` object (info API / fixtures)."""
    out: list[ObservationEnvelope] = []
    for trade in trades:
        liq = trade.get("liquidation")
        if not liq:
            continue
        coin = str(trade.get("coin", "")).upper()
        time_ms = trade.get("time")
        if not coin or time_ms is None:
            continue
        market_time = from_unix_ms(int(time_ms))
        row_ingested = _row_ingested_at(trade, ingested_at)
        tid = str(trade.get("tid") or trade.get("hash") or "")
        extras = {"tid": tid} if tid else {}
        missing = () if trade.get("sz") is not None else ("sz",)
        out.append(
            build_envelope(
                source_name=HL_SOURCE_NAME,
                source_kind=HL_SOURCE_KIND,
                source_url_or_id=f"recentTrades:liquidation:{tid or time_ms}",
                instrument=coin,
                metric="liquidation",
                value=normalize_numeric(trade.get("sz")),
                published_at=market_time,
                ingested_at=row_ingested,
                market_time=market_time,
                payload={"raw": trade, "hl_type": "recentTrades"},
                extras=extras,
                historical=True,
                missing_fields=missing,
                stale_after_seconds=stale_after_seconds,
                evidence_type=EvidenceType.FACT,
                confidence=0.9,
            )
        )
    return out


def _row_ingested_at(row: dict[str, Any], default: datetime) -> datetime:
    extra = row.get("ingested_at")
    if extra is None:
        return default
    from mm_common.time import parse_utc

    if isinstance(extra, datetime):
        return extra
    return parse_utc(str(extra))
