"""Normalize equities adapter rows into observation envelopes."""

from __future__ import annotations

from datetime import datetime

from mm_common.enums import EvidenceType, SourceKind
from mm_common.hashing import normalize_numeric
from mm_common.schemas import ObservationEnvelope
from mm_ingest.equities.models import CorporateAction, EarningsEvent, OHLCVBar
from mm_ingest.sources import POLYGON_SOURCE_NAME
from mm_provenance.envelope import build_envelope


def normalize_ohlcv_bars(
    bars: tuple[OHLCVBar, ...] | list[OHLCVBar],
    *,
    ingested_at: datetime,
    source_name: str = POLYGON_SOURCE_NAME,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    out: list[ObservationEnvelope] = []
    for bar in bars:
        missing = () if bar.close is not None else ("close",)
        extras = {"timespan": bar.timespan, "multiplier": str(bar.multiplier)}
        out.append(
            build_envelope(
                source_name=source_name,
                source_kind=SourceKind.EXCHANGE,
                source_url_or_id=f"aggs:{bar.ticker}:{bar.timespan}:{bar.multiplier}:{int(bar.market_time.timestamp())}",
                instrument=bar.ticker.upper(),
                metric="ohlcv_close",
                value=normalize_numeric(bar.close) if bar.close is not None else None,
                published_at=bar.market_time,
                ingested_at=ingested_at,
                market_time=bar.market_time,
                payload={
                    "raw": bar.raw,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "vwap": bar.vwap,
                    "error_class": bar.error_class,
                },
                extras=extras,
                historical=True,
                missing_fields=missing,
                stale_after_seconds=stale_after_seconds,
                venue="equity",
            )
        )
    return out


def normalize_corporate_actions(
    rows: tuple[CorporateAction, ...] | list[CorporateAction],
    *,
    ingested_at: datetime,
    source_name: str = POLYGON_SOURCE_NAME,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    out: list[ObservationEnvelope] = []
    for row in rows:
        if row.kind == "split":
            metric = "split"
            value = None
            if row.split_from is not None and row.split_to is not None:
                value = normalize_numeric(row.split_to / row.split_from) if row.split_from else None
            missing = () if value is not None else ("split_ratio",)
        else:
            metric = "dividend"
            value = normalize_numeric(row.cash_amount) if row.cash_amount is not None else None
            missing = () if value is not None else ("cash_amount",)
        out.append(
            build_envelope(
                source_name=source_name,
                source_kind=SourceKind.EXCHANGE,
                source_url_or_id=f"{row.kind}:{row.ticker}:{row.ex_date or int(row.market_time.timestamp())}",
                instrument=row.ticker.upper(),
                metric=metric,
                value=value,
                published_at=row.market_time,
                ingested_at=ingested_at,
                market_time=row.market_time,
                payload={"raw": row.raw, "kind": row.kind, "error_class": row.error_class},
                extras={"kind": row.kind},
                historical=True,
                missing_fields=missing,
                stale_after_seconds=stale_after_seconds,
                venue="equity",
                evidence_type=EvidenceType.FACT,
            )
        )
    return out


def normalize_earnings(
    rows: tuple[EarningsEvent, ...] | list[EarningsEvent],
    *,
    ingested_at: datetime,
    source_name: str = POLYGON_SOURCE_NAME,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    out: list[ObservationEnvelope] = []
    for row in rows:
        out.append(
            build_envelope(
                source_name=source_name,
                source_kind=SourceKind.EXCHANGE,
                source_url_or_id=f"earnings:{row.ticker}:{int(row.market_time.timestamp())}",
                instrument=row.ticker.upper(),
                metric="earnings",
                value=row.fiscal_period or row.event_type,
                published_at=row.market_time,
                ingested_at=ingested_at,
                market_time=row.market_time,
                payload={"raw": row.raw, "error_class": row.error_class},
                extras={"event_type": row.event_type},
                historical=True,
                stale_after_seconds=stale_after_seconds,
                venue="equity",
                evidence_type=EvidenceType.FACT,
            )
        )
    return out
