"""Observation envelopes for flow metrics. as_of_knowledge lockstep with ingested_at."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mm_common.enums import EvidenceType, SourceKind
from mm_common.hashing import normalize_numeric
from mm_common.schemas import ObservationEnvelope
from mm_common.time import as_utc
from mm_flow.models import FlowSnapshot
from mm_provenance.envelope import build_envelope

FLOW_SOURCE_NAME = "mm_flow.derived"


def snapshot_envelopes(
    snapshot: FlowSnapshot,
    *,
    ingested_at: datetime | None = None,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    """Derived flow claims. Knowledge watermark is ingest time; never market_time."""
    ingested = as_utc(ingested_at or snapshot.as_of_knowledge)
    out: list[ObservationEnvelope] = []
    for row in snapshot.metrics:
        missing = () if row.status != "unavailable" else (row.name,)
        out.append(
            _envelope(
                instrument=snapshot.instrument,
                metric=row.name,
                value=row.value,
                ingested_at=ingested,
                payload={"status": row.status, "reason": row.reason, "unit": row.unit, **dict(row.payload)},
                extras={"observation_id": (row.provenance[0].observation_id or "")} if row.provenance else None,
                missing_fields=missing,
                stale_after_seconds=stale_after_seconds,
            )
        )
    v = snapshot.verdict
    out.append(
        _envelope(
            instrument=snapshot.instrument,
            metric="liquidity_verdict",
            value=v.verdict,
            ingested_at=ingested,
            payload={
                "max_clip_usd": v.max_clip_usd,
                "slippage_budget_bps": v.slippage_budget_bps,
                "reason": v.reason,
                "thresholds_version": v.thresholds_version,
                "clips": [row.canonical() for row in v.clips],
            },
            extras={"verdict": v.verdict},
            missing_fields=() if v.verdict != "unavailable" else ("liquidity_verdict",),
            stale_after_seconds=stale_after_seconds,
        )
    )
    return out


def _envelope(
    *,
    instrument: str,
    metric: str,
    value: Any,
    ingested_at: datetime,
    payload: dict[str, Any],
    extras: dict[str, str] | None,
    missing_fields: tuple[str, ...],
    stale_after_seconds: int,
) -> ObservationEnvelope:
    shown = normalize_numeric(value) if isinstance(value, (int, float)) else (None if value is None else str(value))
    return build_envelope(
        source_name=FLOW_SOURCE_NAME,
        source_kind=SourceKind.INTERNAL,
        source_url_or_id=f"flow:{instrument}:{metric}",
        instrument=instrument,
        metric=metric,
        value=shown,
        published_at=ingested_at,
        ingested_at=ingested_at,
        market_time=None,
        payload={"derived": True, "phase": "6b", **payload},
        extras=extras or {"capture_kind": "derived"},
        missing_fields=missing_fields,
        stale_after_seconds=stale_after_seconds,
        evidence_type=EvidenceType.DERIVED,
        venue="flow",
    )
