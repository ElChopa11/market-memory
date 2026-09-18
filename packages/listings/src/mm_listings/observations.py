"""Observation envelopes for listings metrics. as_of_knowledge lockstep with ingested_at."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mm_common.enums import EvidenceType, SourceKind
from mm_common.hashing import normalize_numeric
from mm_common.schemas import ObservationEnvelope
from mm_common.time import as_utc
from mm_listings.models import ListingsSnapshot
from mm_provenance.envelope import build_envelope

LISTINGS_SOURCE_NAME = "mm_listings.derived"


def snapshot_envelopes(
    snapshot: ListingsSnapshot,
    *,
    ingested_at: datetime | None = None,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    ingested = as_utc(ingested_at or snapshot.as_of_knowledge)
    out: list[ObservationEnvelope] = []
    for idea in snapshot.ideas:
        track = idea.track
        for metric, value in (
            ("listing_day1_vs_offer", track.day1_vs_offer),
            ("listing_day1_vwap", track.day1_vwap),
            ("listing_ret_30d", track.ret_30d),
            ("listing_ret_90d", track.ret_90d),
            ("listing_dd_from_day1_high", track.drawdown_from_day1_high),
        ):
            missing = () if value is not None else (metric,)
            out.append(
                _envelope(
                    instrument=idea.instrument,
                    metric=metric,
                    value=value,
                    ingested_at=ingested,
                    payload={"status": track.status, "gaps": list(track.gaps)},
                    extras={"observation_id": idea.deal.observation_id or ""},
                    missing_fields=missing,
                    stale_after_seconds=stale_after_seconds,
                )
            )
        out.append(
            _envelope(
                instrument=idea.instrument,
                metric="listings_liquidity_verdict",
                value=idea.liquidity_verdict,
                ingested_at=ingested,
                payload={
                    "observation_only": idea.observation_only,
                    "quant_verdict": idea.quant_verdict,
                    "warning": idea.warning.canonical(),
                },
                extras={"verdict": idea.liquidity_verdict},
                missing_fields=() if idea.liquidity_verdict != "unavailable" else ("listings_liquidity_verdict",),
                stale_after_seconds=stale_after_seconds,
            )
        )
    br = snapshot.base_rates
    out.append(
        _envelope(
            instrument="LISTINGS_COHORT",
            metric="listings_base_rate",
            value=br.median_30d if br.claimed else None,
            ingested_at=ingested,
            payload=br.canonical(),
            extras={"claimed": "true" if br.claimed else "false"},
            missing_fields=() if br.claimed else ("listings_base_rate",),
            stale_after_seconds=stale_after_seconds,
        )
    )
    for event in snapshot.index_events:
        out.append(
            _envelope(
                instrument=event.instrument,
                metric=f"index_{event.kind}",
                value=event.index_name or event.kind,
                ingested_at=ingested,
                payload=event.canonical(),
                extras={"observation_id": event.observation_id or ""},
                missing_fields=(),
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
        source_name=LISTINGS_SOURCE_NAME,
        source_kind=SourceKind.INTERNAL,
        source_url_or_id=f"listings:{instrument}:{metric}",
        instrument=instrument,
        metric=metric,
        value=shown,
        published_at=ingested_at,
        ingested_at=ingested_at,
        market_time=None,
        payload={"derived": True, "phase": "6d", **payload},
        extras=extras or {"capture_kind": "derived"},
        missing_fields=missing_fields,
        stale_after_seconds=stale_after_seconds,
        evidence_type=EvidenceType.DERIVED,
        venue="listings",
    )
