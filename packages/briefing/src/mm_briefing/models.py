"""Shared dataclasses for Market Pulse briefs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


ASSET_ORDER = ("ES", "NQ", "US10Y", "DXY", "CL", "VIX", "BTC", "ETH")
HL_BRIEF_INSTRUMENTS = ("BTC", "ETH")
# Close-path perps. BTC and ETH stay in the price table; the other twelve follow.
# Pre-open keeps HL_BRIEF_INSTRUMENTS so a missing name is not invented there.
MORNING_HL_PERPS = (
    "BTC",
    "ETH",
    "SOL",
    "HYPE",
    "NEAR",
    "ARB",
    "UNI",
    "VVV",
    "ZEC",
    "DOGE",
    "XMR",
    "CHIP",
    "LTC",
    "PURR",
)

# Principal Phase 2 required snapshot slots. Symbols are proxies; missing stays listed.
REQUIRED_SLOTS = ("crypto", "equity-index proxy", "rates", "USD", "oil", "vol")
SLOT_FOR_SYMBOL = {
    "ES": "equity-index proxy",
    "NQ": "equity-index proxy",
    "US10Y": "rates",
    "DXY": "USD",
    "CL": "oil",
    "VIX": "vol",
    "BTC": "crypto",
    "ETH": "crypto",
}

# Display vocabulary for Market Pulse (Principal Phase 2). Storage/DB stays ok|stale|…
PULSE_QUALITY = ("fresh", "stale", "partial", "unavailable")

QUALITY_RANK = {
    "ok": 0,
    "fresh": 0,
    "partial": 1,
    "stale": 2,
    "unavailable": 3,
    "contradicted": 4,
    "rejected": 5,
}

_PULSE_MAP = {
    "ok": "fresh",
    "fresh": "fresh",
    "stale": "stale",
    "partial": "partial",
    "unavailable": "unavailable",
    "contradicted": "unavailable",
    "rejected": "unavailable",
    "none": "unavailable",
    "off": "unavailable",
}

_STORAGE_MAP = {
    "fresh": "ok",
    "ok": "ok",
    "stale": "stale",
    "partial": "partial",
    "unavailable": "partial",
    "contradicted": "contradicted",
    "rejected": "rejected",
}


def pulse_quality(value: str | None) -> str:
    """Map internal/data-quality flags to fresh|stale|partial|unavailable."""
    if value is None or value == "":
        return "unavailable"
    return _PULSE_MAP.get(value, "partial")


def storage_quality(value: str | None) -> str:
    """Map pulse display quality back to the brief-table / observation enum."""
    if value is None or value == "":
        return "partial"
    return _STORAGE_MAP.get(value, "partial")


def worst_quality(*values: str | None) -> str:
    worst = "ok"
    for value in values:
        if value is None:
            continue
        if QUALITY_RANK.get(value, 1) > QUALITY_RANK.get(worst, 0):
            worst = value
    return worst


def overall_pulse_quality(*values: str | None) -> str:
    """Roll up mixed sources: some missing does not hide the rest as unavailable."""
    mapped = [pulse_quality(value) for value in values if value is not None]
    if not mapped:
        return "unavailable"
    unique = set(mapped)
    if unique == {"fresh"}:
        return "fresh"
    if unique == {"unavailable"}:
        return "unavailable"
    if unique <= {"fresh", "stale"}:
        return "stale"
    return "partial"


def slot_label(symbol: str) -> str:
    return SLOT_FOR_SYMBOL.get(symbol.upper(), "other")


def display_symbol(row: AssetPrint) -> str:
    """Symbol column: the proxy ticker that was quoted, otherwise the slot symbol."""
    quoted = (row.quoted_symbol or "").strip()
    return quoted or row.symbol


@dataclass(frozen=True)
class AssetPrint:
    symbol: str
    name: str
    last: float | None
    prior_close: float | None
    unit: str = "px"
    data_quality: str = "ok"
    source: str = "fixture"
    open: float | None = None
    as_of: datetime | None = None
    observation_id: str | None = None
    source_url: str | None = None
    # Polygon ETF ticker actually quoted (SPY/QQQ/UUP/USO). Slot id stays on ``symbol``.
    quoted_symbol: str | None = None
    # Entitlement gap (VIX). Listed on the price row and excluded from the health denominator.
    structural_unavailable: bool = False

    @property
    def change(self) -> float | None:
        if self.last is None or self.prior_close is None:
            return None
        return self.last - self.prior_close

    @property
    def change_pct(self) -> float | None:
        if self.last is None or self.prior_close in (None, 0):
            return None
        return (self.last - self.prior_close) / self.prior_close * 100.0

    @property
    def change_bp(self) -> float | None:
        """Yield change in basis points when unit is percent."""
        delta = self.change
        if delta is None:
            return None
        if self.unit == "%":
            return delta * 100.0
        return None

    @property
    def slot(self) -> str:
        return SLOT_FOR_SYMBOL.get(self.symbol, "other")


@dataclass(frozen=True)
class MacroSnapshot:
    as_of: datetime
    prior_us_close: datetime
    assets: tuple[AssetPrint, ...]
    data_quality: str
    source: str
    notes: tuple[str, ...] = ()

    def by_symbol(self) -> dict[str, AssetPrint]:
        return {row.symbol: row for row in self.assets}


@dataclass(frozen=True)
class CalendarEvent:
    when: datetime
    name: str
    importance: str
    region: str = "US"
    notes: str = ""
    source: str = "config/briefing/calendar.yaml"


@dataclass(frozen=True)
class Divergence:
    rule_id: str
    title: str
    detail: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class HLMetric:
    instrument: str
    metric: str
    value: str | None
    observation_id: str | None
    claim_hash: str | None
    data_quality: str
    market_time: datetime | None = None
    as_of_knowledge: datetime | None = None
    source_url: str | None = None


@dataclass(frozen=True)
class HLInstrumentState:
    instrument: str
    metrics: dict[str, HLMetric]
    liquidations: tuple[HLMetric, ...]
    levels: tuple[tuple[str, str], ...]
    data_quality: str
    as_of_knowledge: datetime | None = None
    source: str = "market_memory"

    def metric(self, name: str) -> HLMetric | None:
        return self.metrics.get(name)

    def observation_ids(self) -> tuple[str, ...]:
        ids: list[str] = []
        for metric in self.metrics.values():
            if metric.observation_id:
                ids.append(metric.observation_id)
        for liq in self.liquidations:
            if liq.observation_id:
                ids.append(liq.observation_id)
        return tuple(ids)


@dataclass(frozen=True)
class WatchItem:
    instrument: str
    why_now: str
    evidence: tuple[str, ...]
    levels: tuple[tuple[str, str], ...]
    invalidation: str
    no_trade: str


@dataclass(frozen=True)
class ThesisHook:
    slug: str
    status: str
    instrument: str | None
    invalidation_summary: str | None
    expected_direction: str | None
    verdict_hook: str
    hypothesis: str = ""


@dataclass(frozen=True)
class AlertEvent:
    alert_type: str
    instrument: str
    detail: str
    evidence: tuple[str, ...]
    threshold: dict[str, Any]
    identity_hash: str


@dataclass(frozen=True)
class AlertDecision:
    pushed: bool
    reason: str
    events: tuple[AlertEvent, ...] = ()


@dataclass(frozen=True)
class BriefDocument:
    kind: str
    session_date: date
    generated_at: datetime
    as_of_knowledge: datetime
    session_tz: str
    lab_tz: str
    data_quality: str
    markdown: str
    content_hash: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Fire:
    kind: str
    when_utc: datetime
    when_session: datetime
    when_lab: datetime
    session_date: date


@dataclass(frozen=True)
class SessionStatus:
    code: str
    label: str
    timezone: str
    tzname: str
    utc_offset: str
    cash_open: str
    cash_close: str
    local: datetime


@dataclass(frozen=True)
class SourceStatus:
    name: str
    quality: str
    as_of: datetime | None = None
    notes: str = ""
    evidence: str = ""
