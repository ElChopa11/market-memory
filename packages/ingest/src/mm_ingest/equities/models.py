"""Typed Polygon / equities response models. No invented fields."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OHLCVBar(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ticker: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: float | None = None
    vwap: float | None = None
    transactions: int | None = None
    market_time: datetime
    timespan: str
    multiplier: int = 1
    error_class: str = "none"
    raw: dict[str, Any] = Field(default_factory=dict)


class CorporateAction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ticker: str
    kind: str  # dividend | split
    market_time: datetime
    cash_amount: float | None = None
    split_from: float | None = None
    split_to: float | None = None
    declaration_date: str | None = None
    ex_date: str | None = None
    pay_date: str | None = None
    record_date: str | None = None
    error_class: str = "none"
    raw: dict[str, Any] = Field(default_factory=dict)


class EarningsEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ticker: str
    market_time: datetime
    event_type: str = "earnings"
    fiscal_period: str | None = None
    error_class: str = "none"
    raw: dict[str, Any] = Field(default_factory=dict)
