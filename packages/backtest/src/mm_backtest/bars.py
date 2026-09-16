"""Bar / candle models with explicit as-of (knowledge) timestamps."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from mm_common.time import as_utc, from_unix_ms, parse_utc


def _as_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def parse_as_of(value: Any) -> datetime:
    """Parse a UTC instant from ISO-8601 or unix milliseconds."""
    if isinstance(value, datetime):
        return as_utc(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        ms = int(value)
        if abs(ms) < 10**12:
            ms *= 1000
        return from_unix_ms(ms)
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return parse_as_of(int(text))
        return parse_utc(text)
    raise ValueError(f"cannot parse as-of timestamp: {value!r}")


class Bar(BaseModel):
    """One OHLCV bar. `available_at` is the knowledge watermark (like ingested_at)."""

    model_config = ConfigDict(frozen=True)

    instrument: str
    market_time: datetime
    available_at: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal("0")
    interval: str = "1h"

    @field_validator("market_time", "available_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return as_utc(value)

    @field_validator("open", "high", "low", "close", "volume", mode="before")
    @classmethod
    def _decimal(cls, value: Any) -> Decimal:
        return _as_decimal(value)

    def canonical(self) -> dict[str, str]:
        return {
            "instrument": self.instrument,
            "market_time": self.market_time.isoformat(),
            "available_at": self.available_at.isoformat(),
            "open": format(self.open, "f"),
            "high": format(self.high, "f"),
            "low": format(self.low, "f"),
            "close": format(self.close, "f"),
            "volume": format(self.volume, "f"),
            "interval": self.interval,
        }


class KnowledgeFact(BaseModel):
    """Point-in-time observation snapshot. Knowledge time is ingested_at."""

    model_config = ConfigDict(frozen=True)

    id: str
    ingested_at: datetime
    instrument: str | None = None
    claim_text: str = ""
    payload: dict[str, Any] = {}

    @field_validator("ingested_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return as_utc(value)

    def canonical(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ingested_at": self.ingested_at.isoformat(),
            "instrument": self.instrument,
            "claim_text": self.claim_text,
            "payload": self.payload,
        }
