"""Pydantic observation envelope — the provenance contract for every claim."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from mm_common.enums import DataQuality, EvidenceType, SourceKind
from mm_common.hashing import claim_hash as hash_claim
from mm_common.time import as_utc


class ClaimIdentity(BaseModel):
    """Fields that uniquely identify a claim for dedupe (excludes ingested_at)."""

    model_config = ConfigDict(frozen=True)

    source_name: str
    instrument: str
    metric: str
    market_time: datetime | None
    value: str | None
    extras: dict[str, str] = Field(default_factory=dict)

    @field_validator("market_time")
    @classmethod
    def _utc_market_time(cls, value: datetime | None) -> datetime | None:
        return as_utc(value) if value is not None else None

    def hash_payload(self) -> dict[str, Any]:
        market_time = self.market_time.isoformat() if self.market_time is not None else None
        return {
            "source_name": self.source_name,
            "instrument": self.instrument,
            "metric": self.metric,
            "market_time": market_time,
            "value": self.value,
            "extras": dict(sorted(self.extras.items())),
        }

    def slot_payload(self) -> dict[str, Any]:
        """Contradiction slot: same fact identity with value excluded."""
        payload = self.hash_payload()
        payload.pop("value", None)
        return payload


class ObservationEnvelope(BaseModel):
    """Normalized observation ready to persist. Timestamps are timezone-aware UTC."""

    model_config = ConfigDict(extra="forbid")

    source_name: str
    source_kind: SourceKind
    source_url_or_id: str
    published_at: datetime
    ingested_at: datetime
    market_time: datetime | None = None  # exchange event time; None for lab snapshots
    claim_text: str
    claim_hash: str = ""
    confidence: float = Field(ge=0, le=1)
    evidence_type: EvidenceType
    data_quality: DataQuality = DataQuality.OK
    payload: dict[str, Any] = Field(default_factory=dict)
    raw_object_key: str | None = None
    raw_object_checksum: str | None = None
    as_of_knowledge: datetime | None = None  # always coerced to ingested_at
    instrument: str
    metric: str
    identity: ClaimIdentity

    @field_validator("published_at", "ingested_at", "market_time", "as_of_knowledge")
    @classmethod
    def _aware_utc(cls, value: datetime | None) -> datetime | None:
        return as_utc(value) if value is not None else None

    @model_validator(mode="after")
    def _fill_defaults(self) -> ObservationEnvelope:
        if not self.claim_hash:
            self.claim_hash = hash_claim(self.identity.hash_payload())
        # Sole knowledge watermark: lab ingest time. Never published_at / market_time.
        self.as_of_knowledge = self.ingested_at
        return self
