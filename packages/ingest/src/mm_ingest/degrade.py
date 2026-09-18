"""Honest degrade envelopes. Never invent market prints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mm_common.enums import DataQuality, EvidenceType, SourceKind
from mm_common.http import ERROR_MISSING_ENV, missing_env_notes
from mm_common.schemas import ObservationEnvelope
from mm_ingest.sources import meta_for
from mm_provenance.envelope import build_envelope


def feed_status_envelope(
    *,
    source_name: str,
    instrument: str,
    ingested_at: datetime,
    published_at: datetime | None = None,
    error_class: str,
    metric: str = "feed_status",
    notes: tuple[str, ...] = (),
    payload: dict[str, Any] | None = None,
    venue: str = "feed",
    source_url_or_id: str = "feed_status",
) -> ObservationEnvelope:
    """Record that a feed was unavailable/degraded at lab knowledge time."""
    spec = meta_for(source_name)
    body = dict(payload or {})
    body["error_class"] = error_class
    body["notes"] = list(notes)
    body["degrade"] = True
    return build_envelope(
        source_name=spec.name,
        source_kind=spec.kind if isinstance(spec.kind, SourceKind) else SourceKind.INTERNAL,
        source_url_or_id=source_url_or_id,
        instrument=instrument,
        metric=metric,
        value="unavailable",
        published_at=published_at or ingested_at,
        ingested_at=ingested_at,
        market_time=None,
        payload=body,
        extras={"capture_kind": "lab_snapshot", "error_class": error_class},
        missing_fields=(metric,),
        evidence_type=EvidenceType.FACT,
        confidence=0.2,
        venue=venue,
        data_quality=DataQuality.PARTIAL,
    )


def missing_env_envelopes(
    *,
    source_name: str,
    env_name: str,
    instruments: list[str],
    ingested_at: datetime,
    venue: str,
) -> list[ObservationEnvelope]:
    notes = missing_env_notes(env_name, source=source_name)
    return [
        feed_status_envelope(
            source_name=source_name,
            instrument=symbol,
            ingested_at=ingested_at,
            error_class=ERROR_MISSING_ENV,
            notes=notes,
            venue=venue,
            source_url_or_id=f"missing_env:{env_name}",
        )
        for symbol in instruments
    ]
