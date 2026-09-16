"""Build observation envelopes from normalized claims."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mm_common.enums import DataQuality, EvidenceType, SourceKind
from mm_common.hashing import claim_hash, normalize_numeric
from mm_common.schemas import ClaimIdentity, ObservationEnvelope
from mm_common.time import as_utc
from mm_provenance.quality import assess_quality


def build_envelope(
    *,
    source_name: str,
    source_kind: SourceKind,
    source_url_or_id: str,
    instrument: str,
    metric: str,
    value: str | None,
    published_at: datetime,
    ingested_at: datetime,
    market_time: datetime | None,
    payload: dict[str, Any],
    extras: dict[str, str] | None = None,
    evidence_type: EvidenceType = EvidenceType.METRIC,
    confidence: float = 0.99,
    historical: bool = False,
    missing_fields: tuple[str, ...] = (),
    stale_after_seconds: int = 120,
    raw_object_key: str | None = None,
    raw_object_checksum: str | None = None,
) -> ObservationEnvelope:
    published = as_utc(published_at)
    ingested = as_utc(ingested_at)
    market = as_utc(market_time) if market_time is not None else None
    identity = ClaimIdentity(
        source_name=source_name,
        instrument=instrument,
        metric=metric,
        market_time=market,
        value=normalize_numeric(value) if value is not None and _looks_numeric(value) else value,
        extras=extras or {},
    )
    quality = assess_quality(
        ingested_at=ingested,
        published_at=published,
        missing_fields=missing_fields,
        historical=historical,
        stale_after_seconds=stale_after_seconds,
    )
    when = market.isoformat() if market is not None else f"lab_capture {published.isoformat()}"
    if missing_fields:
        confidence = min(confidence, 0.2)
        claim_text = f"{instrument} perp {metric} missing ({', '.join(missing_fields)}) at {when}"
    else:
        shown = identity.value if identity.value is not None else "null"
        claim_text = f"{instrument} perp {metric}={shown} at {when}"
        if quality is DataQuality.STALE:
            claim_text += " [stale]"

    payload_out = dict(payload)
    payload_out.setdefault("instrument", instrument)
    payload_out.setdefault("metric", metric)
    payload_out.setdefault("historical", historical)
    payload_out.setdefault("missing_fields", list(missing_fields))
    payload_out.setdefault("value", identity.value)
    capture_kind = (extras or {}).get("capture_kind")
    if capture_kind:
        payload_out.setdefault("capture_kind", capture_kind)

    return ObservationEnvelope(
        source_name=source_name,
        source_kind=source_kind,
        source_url_or_id=source_url_or_id,
        published_at=published,
        ingested_at=ingested,
        market_time=market,
        claim_text=claim_text,
        claim_hash=claim_hash(identity.hash_payload()),
        confidence=confidence,
        evidence_type=evidence_type,
        data_quality=quality,
        payload=payload_out,
        raw_object_key=raw_object_key,
        raw_object_checksum=raw_object_checksum,
        as_of_knowledge=ingested,
        instrument=instrument,
        metric=metric,
        identity=identity,
    )


def _looks_numeric(value: str) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True
