"""Post-IPO / reclaim screen types. Equities desk product; not a call generator."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mm_research_kit.quant_review.models import (
    InstrumentPrint,
    QuantReasonCode,
    QuantVerdict,
    ReclaimObservables,
    SeriesOverlay,
)

ENGINE_VERSION = "imp-006.1"
MAX_RESEARCH_PRIORITY = 3
UNUSUAL_SESSION_PP = 2.0
STALE_AFTER_HOURS_DEFAULT = 36
RECLAIM_MIN_HOLD_SESSIONS = 2

SCREEN_FOOTER = (
    "Informational research triage only. Not a trading decision, allocation, or execution approval. "
    "A Quant verdict is not permission to paper or live. Principal gate still required for anything beyond research."
)

DATA_QUALITY_VALUES = ("fresh", "stale", "partial", "unavailable")
MEMBERSHIP_VALUES = ("in_universe", "watch_only", "screen_only", "deferred_must_cut", "unknown")


class ScreenDataQuality(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class ScreenRole(StrEnum):
    CANDIDATE = "candidate"
    BENCHMARK = "benchmark"
    PEER = "peer"
    PEER_CONTEXT = "peer_context"


@dataclass(frozen=True)
class ScreenInstrument:
    symbol: str
    raw_symbols: tuple[str, ...]
    asset_class: str
    venue: str
    sector: str
    benchmark: str
    peers: tuple[str, ...]
    post_ipo: bool = True
    listing_date: str | None = None
    role: str = ScreenRole.CANDIDATE.value
    membership: str = "screen_only"
    notes: str = ""


@dataclass(frozen=True)
class ScreenContextName:
    symbol: str
    role: str
    asset_class: str = "unknown"


@dataclass(frozen=True)
class ScreenUniverse:
    version: str
    status: str
    kind: str
    desk: str
    locked_membership_file: str
    instruments: tuple[ScreenInstrument, ...]
    context: tuple[ScreenContextName, ...]
    symbol_map: dict[str, str]
    notes: tuple[str, ...] = ()
    provenance: tuple[dict[str, Any], ...] = ()
    stale_after_hours: int = STALE_AFTER_HOURS_DEFAULT

    def candidates(self) -> tuple[ScreenInstrument, ...]:
        return tuple(row for row in self.instruments if row.role == ScreenRole.CANDIDATE.value)

    def by_symbol(self) -> dict[str, ScreenInstrument]:
        return {row.symbol: row for row in self.instruments}


@dataclass(frozen=True)
class MetricCell:
    name: str
    value: str
    source: str
    as_of: str
    freshness: str
    notes: str = ""


@dataclass(frozen=True)
class ScreenRow:
    instrument: str
    raw_symbols: tuple[str, ...]
    as_of_knowledge: str
    membership: str
    post_ipo: bool
    listing_date: str
    sector: str
    benchmark: str
    peers: tuple[str, ...]
    data_quality: str
    metrics: tuple[MetricCell, ...]
    verdict: str
    reason_codes: tuple[str, ...]
    labels: tuple[str, ...]
    unusual: str
    catalyst: str
    invalidation: str
    liquidity: str
    what_must_change: str


@dataclass(frozen=True)
class ScreenResult:
    screen_date: str
    as_of_knowledge: str
    generated_at: str
    universe_version: str
    params_hash: str
    rows: tuple[ScreenRow, ...]
    markdown: str
    coverage_notes: tuple[str, ...]
    snapshot_source: str


# Re-export Quant closed sets so callers import from one desk module.
__all__ = [
    "DATA_QUALITY_VALUES",
    "ENGINE_VERSION",
    "MAX_RESEARCH_PRIORITY",
    "MEMBERSHIP_VALUES",
    "MetricCell",
    "QuantReasonCode",
    "QuantVerdict",
    "RECLAIM_MIN_HOLD_SESSIONS",
    "SCREEN_FOOTER",
    "STALE_AFTER_HOURS_DEFAULT",
    "ScreenContextName",
    "ScreenDataQuality",
    "ScreenInstrument",
    "ScreenResult",
    "ScreenRole",
    "ScreenRow",
    "ScreenUniverse",
    "UNUSUAL_SESSION_PP",
    "InstrumentPrint",
    "ReclaimObservables",
    "SeriesOverlay",
]
