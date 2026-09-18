"""Swappable equities adapter interface. Default vendor is Polygon (Principal lock).

Intel/ingest only. Must not import mm_desks / mm_quant / mm_delivery / mm_execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from mm_ingest.equities.models import CorporateAction, EarningsEvent, OHLCVBar


@dataclass(frozen=True)
class EquitiesQuery:
    tickers: tuple[str, ...]
    start: datetime
    end: datetime
    ingested_at: datetime
    include_intraday: bool = True
    include_corporate_actions: bool = True
    include_earnings: bool = True


class EquitiesAdapter(Protocol):
    """Read-only equities tape. Secrets only via env. Degrade, never invent."""

    vendor: str
    source_name: str

    def ohlcv_daily(self, query: EquitiesQuery) -> tuple[OHLCVBar, ...]: ...

    def ohlcv_intraday(self, query: EquitiesQuery) -> tuple[OHLCVBar, ...]: ...

    def corporate_actions(self, query: EquitiesQuery) -> tuple[CorporateAction, ...]: ...

    def earnings_calendar(self, query: EquitiesQuery) -> tuple[EarningsEvent, ...]: ...


DEFAULT_EQUITIES_VENDOR = "polygon"
