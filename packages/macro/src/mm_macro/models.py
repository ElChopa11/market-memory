"""Typed macro models. Research-only; a regime tag is not a call."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from mm_common.hashing import canonical_json, normalize_numeric, sha256_hex
from mm_common.time import as_utc

ENGINE_VERSION = "imp-015.1"
CARD_FOOTER = (
    "Research only. Regime tag is not a trade instruction, allocation, or execution approval. "
    "EVENT_RISK is a calendar proximity flag for Risk haircut, not an order."
)
UNAVAILABLE = "unavailable"
OK = "ok"
PARTIAL = "partial"
STATUS_VALUES = (OK, PARTIAL, UNAVAILABLE)


def _iso(value: datetime) -> str:
    return as_utc(value).isoformat()


@dataclass(frozen=True)
class MacroPoint:
    instrument: str
    metric: str
    as_of_knowledge: datetime
    value: float | None
    observation_id: str | None = None
    fixture_id: str | None = None
    ingested_at: datetime | None = None
    series_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_knowledge", as_utc(self.as_of_knowledge))
        ingested = self.ingested_at if self.ingested_at is not None else self.as_of_knowledge
        object.__setattr__(self, "ingested_at", as_utc(ingested))

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "metric": self.metric,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "value": normalize_numeric(self.value) if self.value is not None else None,
            "observation_id": self.observation_id,
            "series_id": self.series_id,
        }


@dataclass(frozen=True)
class CalendarEvent:
    when: datetime
    name: str
    importance: str = "medium"
    region: str = "US"
    notes: str = ""
    source: str = "fixture"
    as_of_knowledge: datetime | None = None
    ingested_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "when", as_utc(self.when))
        known = self.as_of_knowledge or self.ingested_at
        if known is not None:
            object.__setattr__(self, "as_of_knowledge", as_utc(known))
        ingested = self.ingested_at if self.ingested_at is not None else self.as_of_knowledge
        if ingested is not None:
            object.__setattr__(self, "ingested_at", as_utc(ingested))


@dataclass(frozen=True)
class RegimeResult:
    tag: str
    confidence: float
    as_of_knowledge: datetime
    status: str
    driving_inputs: dict[str, Any]
    thresholds_version: str
    reason: str = ""

    def canonical(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "confidence": normalize_numeric(self.confidence),
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "status": self.status,
            "driving_inputs": self.driving_inputs,
            "thresholds_version": self.thresholds_version,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class EventRiskTag:
    tagged: bool
    rule_id: str
    window_minutes: int
    as_of_knowledge: datetime
    event_name: str | None = None
    event_when: str | None = None
    minutes_to_event: float | None = None
    size_haircut_pct: float | None = None
    reason: str = ""

    def canonical(self) -> dict[str, Any]:
        return {
            "tagged": self.tagged,
            "rule_id": self.rule_id,
            "window_minutes": self.window_minutes,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "event_name": self.event_name,
            "event_when": self.event_when,
            "minutes_to_event": (
                normalize_numeric(self.minutes_to_event) if self.minutes_to_event is not None else None
            ),
            "size_haircut_pct": (
                normalize_numeric(self.size_haircut_pct) if self.size_haircut_pct is not None else None
            ),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class MacroSnapshot:
    as_of_knowledge: datetime
    config_version: str
    data_quality: str
    regime: RegimeResult
    event_risk: EventRiskTag
    series: tuple[MacroPoint, ...]
    missing: tuple[str, ...]
    footer: str = CARD_FOOTER
    engine_version: str = ENGINE_VERSION
    payload: dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> dict[str, Any]:
        return {
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "config_version": self.config_version,
            "data_quality": self.data_quality,
            "engine_version": self.engine_version,
            "regime": self.regime.canonical(),
            "event_risk": self.event_risk.canonical(),
            "series": [row.canonical() for row in self.series],
            "missing": list(self.missing),
            "footer": self.footer,
        }

    def result_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical()))
