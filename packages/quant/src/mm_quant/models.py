"""Typed factor / card models. Research-only; not an order surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from mm_common.hashing import canonical_json, normalize_numeric, sha256_hex
from mm_common.time import as_utc

ENGINE_VERSION = "imp-011.1"
CARD_FOOTER = (
    "Research only. Not a trade instruction, allocation decision, or execution approval. "
    "Intent-level budget fraction is not an order."
)
UNAVAILABLE = "unavailable"
OK = "ok"
PARTIAL = "partial"

STATUS_VALUES = (OK, PARTIAL, UNAVAILABLE)


def _iso(value: datetime) -> str:
    return as_utc(value).isoformat()


@dataclass(frozen=True)
class ProvenanceRef:
    """Every number points at an observation, fixture row, and knowledge watermark."""

    as_of_knowledge: str
    observation_id: str | None = None
    fixture_id: str | None = None
    instrument: str | None = None
    metric: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "as_of_knowledge": self.as_of_knowledge,
            "observation_id": self.observation_id,
            "fixture_id": self.fixture_id,
            "instrument": self.instrument,
            "metric": self.metric,
        }


@dataclass(frozen=True)
class SeriesBar:
    """OHLCV bar with a knowledge watermark. Factors must key off as_of_knowledge."""

    instrument: str
    market_time: datetime
    as_of_knowledge: datetime
    close: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: float | None = None
    observation_id: str | None = None
    fixture_id: str | None = None
    ingested_at: datetime | None = None
    asset_class: str = "unknown"

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_time", as_utc(self.market_time))
        object.__setattr__(self, "as_of_knowledge", as_utc(self.as_of_knowledge))
        ingested = self.ingested_at if self.ingested_at is not None else self.as_of_knowledge
        object.__setattr__(self, "ingested_at", as_utc(ingested))

    def provenance(self) -> ProvenanceRef:
        return ProvenanceRef(
            as_of_knowledge=_iso(self.as_of_knowledge),
            observation_id=self.observation_id,
            fixture_id=self.fixture_id,
            instrument=self.instrument,
            metric="ohlcv_close",
        )


@dataclass(frozen=True)
class StructurePoint:
    """Phase 5b HL structure (or fixture stand-in). Missing value → degrade, never invent."""

    instrument: str
    metric: str
    as_of_knowledge: datetime
    value: float | None
    observation_id: str | None = None
    fixture_id: str | None = None
    ingested_at: datetime | None = None
    data_quality: str = OK

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_knowledge", as_utc(self.as_of_knowledge))
        ingested = self.ingested_at if self.ingested_at is not None else self.as_of_knowledge
        object.__setattr__(self, "ingested_at", as_utc(ingested))

    def provenance(self) -> ProvenanceRef:
        return ProvenanceRef(
            as_of_knowledge=_iso(self.as_of_knowledge),
            observation_id=self.observation_id,
            fixture_id=self.fixture_id,
            instrument=self.instrument,
            metric=self.metric,
        )


@dataclass(frozen=True)
class MarketPanel:
    bars: tuple[SeriesBar, ...] = ()
    structure: tuple[StructurePoint, ...] = ()
    fixture_id: str | None = None
    sector_of: dict[str, str] = field(default_factory=dict)
    asset_class_of: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class FactorValue:
    name: str
    status: str
    as_of_knowledge: datetime
    value: float | None = None
    unit: str = ""
    window: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    inputs: dict[str, Any] = field(default_factory=dict)
    provenance: tuple[ProvenanceRef, ...] = ()
    reason: str = ""

    def canonical(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "value": normalize_numeric(self.value) if self.value is not None else None,
            "unit": self.unit,
            "window": self.window,
            "payload": self.payload,
            "inputs": self.inputs,
            "provenance": [row.canonical() for row in self.provenance],
            "reason": self.reason,
        }


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
class SizingHint:
    """Intent-level % of research budget. Not an order and not a fill size."""

    method: str
    budget_fraction_pct: float | None
    status: str
    as_of_knowledge: datetime
    inputs: dict[str, Any]
    provenance: tuple[ProvenanceRef, ...] = ()
    reason: str = ""

    def canonical(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "budget_fraction_pct": (
                normalize_numeric(self.budget_fraction_pct)
                if self.budget_fraction_pct is not None
                else None
            ),
            "status": self.status,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "inputs": self.inputs,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class QuantCard:
    """Factor-layer Quant Card (IMP-011). Distinct from IMP-001 review-board QuantCard."""

    instrument: str
    as_of_knowledge: datetime
    config_version: str
    params_hash: str
    data_quality: str
    factors: tuple[FactorValue, ...]
    regime: RegimeResult
    sizing_hints: tuple[SizingHint, ...]
    gaps: tuple[str, ...]
    provenance: tuple[ProvenanceRef, ...]
    footer: str = CARD_FOOTER
    engine_version: str = ENGINE_VERSION

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "config_version": self.config_version,
            "params_hash": self.params_hash,
            "data_quality": self.data_quality,
            "engine_version": self.engine_version,
            "factors": [row.canonical() for row in self.factors],
            "regime": self.regime.canonical(),
            "sizing_hints": [row.canonical() for row in self.sizing_hints],
            "gaps": list(self.gaps),
            "footer": self.footer,
        }

    def result_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical()))
