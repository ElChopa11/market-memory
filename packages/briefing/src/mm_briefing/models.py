"""Shared dataclasses for Market Pulse briefs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


ASSET_ORDER = ("ES", "NQ", "US10Y", "DXY", "CL", "VIX", "BTC", "ETH")

QUALITY_RANK = {
    "ok": 0,
    "partial": 1,
    "stale": 2,
    "contradicted": 3,
    "rejected": 4,
}


def worst_quality(*values: str | None) -> str:
    worst = "ok"
    for value in values:
        if value is None:
            continue
        if QUALITY_RANK.get(value, 1) > QUALITY_RANK.get(worst, 0):
            worst = value
    return worst


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


@dataclass(frozen=True)
class HLInstrumentState:
    instrument: str
    metrics: dict[str, HLMetric]
    liquidations: tuple[HLMetric, ...]
    levels: tuple[tuple[str, str], ...]
    data_quality: str

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
