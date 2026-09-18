"""Observation envelopes for macro series / regime / EVENT_RISK. PIT provenance."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mm_common.enums import EvidenceType, SourceKind
from mm_common.hashing import normalize_numeric
from mm_common.schemas import ObservationEnvelope
from mm_common.time import as_utc
from mm_macro.models import MacroSnapshot
from mm_provenance.envelope import build_envelope

MACRO_SOURCE_NAME = "mm_macro.derived"


def snapshot_envelopes(
    snapshot: MacroSnapshot,
    *,
    ingested_at: datetime | None = None,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    ingested = as_utc(ingested_at or snapshot.as_of_knowledge)
    out: list[ObservationEnvelope] = []
    for row in snapshot.series:
        out.append(
            _envelope(
                instrument=row.instrument,
                metric=row.metric or "fred_observation",
                value=row.value,
                ingested_at=ingested,
                payload={"observation_id": row.observation_id, "series_id": row.series_id},
                extras={"series_id": row.series_id or row.instrument},
                missing_fields=() if row.value is not None else (row.instrument,),
                stale_after_seconds=stale_after_seconds,
                evidence_type=EvidenceType.METRIC,
            )
        )
    tag = snapshot.regime.tag
    out.append(
        _envelope(
            instrument="MACRO",
            metric="regime_tag",
            value=tag,
            ingested_at=ingested,
            payload=snapshot.regime.canonical(),
            extras={"tag": tag},
            missing_fields=() if snapshot.regime.status != "unavailable" else ("VIX", "DXY"),
            stale_after_seconds=stale_after_seconds,
            evidence_type=EvidenceType.DERIVED,
        )
    )
    er = snapshot.event_risk
    out.append(
        _envelope(
            instrument="MACRO",
            metric="event_risk",
            value="EVENT_RISK" if er.tagged else "clear",
            ingested_at=ingested,
            payload=er.canonical(),
            extras={"rule_id": er.rule_id},
            missing_fields=(),
            stale_after_seconds=stale_after_seconds,
            evidence_type=EvidenceType.FACT,
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
    extras: dict[str, str],
    missing_fields: tuple[str, ...],
    stale_after_seconds: int,
    evidence_type: EvidenceType,
) -> ObservationEnvelope:
    shown = normalize_numeric(value) if isinstance(value, (int, float)) else (None if value is None else str(value))
    return build_envelope(
        source_name=MACRO_SOURCE_NAME,
        source_kind=SourceKind.MACRO,
        source_url_or_id=f"macro:{instrument}:{metric}",
        instrument=instrument,
        metric=metric,
        value=shown,
        published_at=ingested_at,
        ingested_at=ingested_at,
        market_time=None,
        payload={"derived": True, "phase": "6b", **payload},
        extras=extras,
        missing_fields=missing_fields,
        stale_after_seconds=stale_after_seconds,
        evidence_type=evidence_type,
        venue="macro",
    )
