"""Typed flow / liquidity models. Research-only; not an order surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from mm_common.hashing import canonical_json, normalize_numeric, sha256_hex
from mm_common.time import as_utc
from mm_quant.models import ProvenanceRef

ENGINE_VERSION = "imp-015.1"
CARD_FOOTER = (
    "Research only. Liquidity verdict is not an order, fill, or execution approval. "
    "Clip sizes are configured research notionals, not live size."
)
UNAVAILABLE = "unavailable"
OK = "ok"
PARTIAL = "partial"
STATUS_VALUES = (OK, PARTIAL, UNAVAILABLE)

VERDICT_OK = "OK"
VERDICT_THIN = "THIN"
VERDICT_UNTRADEABLE = "UNTRADEABLE_AT_SIZE"
VERDICT_UNAVAILABLE = "unavailable"
VERDICT_VALUES = (VERDICT_OK, VERDICT_THIN, VERDICT_UNTRADEABLE, VERDICT_UNAVAILABLE)


def _iso(value: datetime) -> str:
    return as_utc(value).isoformat()


@dataclass(frozen=True)
class MetricValue:
    name: str
    status: str
    as_of_knowledge: datetime
    value: float | None = None
    unit: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    provenance: tuple[ProvenanceRef, ...] = ()
    reason: str = ""

    def canonical(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "value": normalize_numeric(self.value) if self.value is not None else None,
            "unit": self.unit,
            "payload": self.payload,
            "provenance": [row.canonical() for row in self.provenance],
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ClipSlippage:
    clip_usd: float
    slippage_bps: float | None
    status: str
    method: str
    reason: str = ""

    def canonical(self) -> dict[str, Any]:
        return {
            "clip_usd": normalize_numeric(self.clip_usd),
            "slippage_bps": normalize_numeric(self.slippage_bps) if self.slippage_bps is not None else None,
            "status": self.status,
            "method": self.method,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class LiquidityVerdict:
    """OK | THIN | UNTRADEABLE_AT_SIZE. Missing tape → unavailable, never invented."""

    verdict: str
    as_of_knowledge: datetime
    status: str
    max_clip_usd: float | None
    slippage_budget_bps: float
    clips: tuple[ClipSlippage, ...]
    reason: str = ""
    thresholds_version: str = ""

    def canonical(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "status": self.status,
            "max_clip_usd": normalize_numeric(self.max_clip_usd) if self.max_clip_usd is not None else None,
            "slippage_budget_bps": normalize_numeric(self.slippage_budget_bps),
            "clips": [row.canonical() for row in self.clips],
            "reason": self.reason,
            "thresholds_version": self.thresholds_version,
        }


@dataclass(frozen=True)
class FlowSnapshot:
    instrument: str
    as_of_knowledge: datetime
    config_version: str
    data_quality: str
    metrics: tuple[MetricValue, ...]
    verdict: LiquidityVerdict
    gaps: tuple[str, ...]
    provenance: tuple[ProvenanceRef, ...]
    footer: str = CARD_FOOTER
    engine_version: str = ENGINE_VERSION

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "config_version": self.config_version,
            "data_quality": self.data_quality,
            "engine_version": self.engine_version,
            "metrics": [row.canonical() for row in self.metrics],
            "verdict": self.verdict.canonical(),
            "gaps": list(self.gaps),
            "footer": self.footer,
        }

    def result_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical()))
