"""Frozen-day fixture models for desk runners. No network. Missing stays missing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from mm_common.time import as_utc, parse_utc
from mm_quant.models import MarketPanel


def _ts(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return as_utc(value)
    return parse_utc(str(value))


@dataclass(frozen=True)
class FeedRow:
    source_id: str
    status: str
    freshness: str = "unavailable"
    observation_id: str | None = None
    notes: str = ""
    required: bool = False

    def canonical(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "status": self.status,
            "freshness": self.freshness,
            "observation_id": self.observation_id,
            "notes": self.notes,
            "required": self.required,
        }


@dataclass(frozen=True)
class TapeRow:
    instrument: str
    metric: str
    value: str | None
    source: str
    freshness: str
    observation_id: str | None = None
    asset_class: str = "unknown"
    membership: str = "not_in_membership"

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "metric": self.metric,
            "value": self.value,
            "source": self.source,
            "freshness": self.freshness,
            "observation_id": self.observation_id,
            "asset_class": self.asset_class,
            "membership": self.membership,
        }


@dataclass(frozen=True)
class CalendarRow:
    when: datetime
    name: str
    importance: str = "medium"
    region: str = "US"
    notes: str = ""
    source: str = "fixture"
    ingested_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "when", as_utc(self.when))
        if self.ingested_at is not None:
            object.__setattr__(self, "ingested_at", as_utc(self.ingested_at))


@dataclass
class ThesisSnapshot:
    """In-memory thesis for fixture runs. Git workspace is optional."""

    slug: str
    status: str
    author: str
    instrument: str
    invalidation: str
    max_loss: str
    intent: str = ""
    horizon: str = ""
    membership: str = "in_universe"
    evidence_ids: tuple[str, ...] = ()
    look_ahead: bool = False
    leakage: bool = False
    already_priced: bool = False
    crowding: str = "noted"
    invalidation_quality: str = "ok"
    reviewer: str = "Independent Skeptic"


@dataclass(frozen=True)
class RiskIntentSpec:
    instrument: str
    invalidation: str
    max_loss: str
    leverage: float = 1.0
    environment: str = "paper"
    requested_target: str | None = None
    halt: bool = False


@dataclass
class FrozenDay:
    fixture_id: str
    as_of_knowledge: datetime
    session_date: str
    inventory: tuple[str, ...]
    feeds: tuple[FeedRow, ...]
    tape: tuple[TapeRow, ...]
    calendar: tuple[CalendarRow, ...]
    thesis: ThesisSnapshot
    risk: RiskIntentSpec
    panel: MarketPanel
    quant_instruments: tuple[str, ...]
    what_changed: str = "none"
    skeptic_force_verdict: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.as_of_knowledge = as_utc(self.as_of_knowledge)
