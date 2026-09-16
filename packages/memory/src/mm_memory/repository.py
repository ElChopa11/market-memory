"""Persist observation envelopes with claim_hash dedupe and contradiction links."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from mm_common.enums import DataQuality, ObservationRelation
from mm_common.hashing import claim_hash
from mm_common.ids import new_ulid
from mm_common.schemas import ObservationEnvelope
from mm_memory.models import Observation, ObservationLink, RawObject, Source
from mm_memory.object_store import ObjectPointer


@dataclass(frozen=True)
class PutResult:
    observation: Observation
    created: bool
    contradicted: bool = False


class ObservationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_source(
        self,
        *,
        name: str,
        kind: str,
        base_url: str | None = None,
        trust_tier: int = 3,
        tos_notes: str | None = None,
    ) -> Source:
        existing = self.session.scalar(select(Source).where(Source.name == name))
        if existing is not None:
            return existing
        source = Source(
            id=new_ulid(),
            name=name,
            kind=kind,
            base_url=base_url,
            trust_tier=trust_tier,
            tos_notes=tos_notes,
        )
        self.session.add(source)
        self.session.flush()
        return source

    def record_raw_object(self, pointer: ObjectPointer) -> RawObject | None:
        """Persist a durable object pointer. Empty keys (NullObjectStore) are not rows."""
        if not pointer.key:
            return None
        existing = self.session.scalar(
            select(RawObject).where(RawObject.bucket == pointer.bucket, RawObject.object_key == pointer.key)
        )
        if existing is not None:
            return existing
        row = RawObject(
            id=new_ulid(),
            bucket=pointer.bucket,
            object_key=pointer.key,
            checksum_sha256=pointer.checksum_sha256,
            content_type=pointer.content_type,
            byte_size=pointer.byte_size,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def put_observation(
        self,
        envelope: ObservationEnvelope,
        *,
        source: Source | None = None,
        raw_pointer: ObjectPointer | None = None,
    ) -> PutResult:
        if source is None:
            source = self.ensure_source(
                name=envelope.source_name,
                kind=envelope.source_kind.value,
            )
        raw_key = envelope.raw_object_key
        raw_checksum = envelope.raw_object_checksum
        if raw_pointer is not None:
            recorded = self.record_raw_object(raw_pointer)
            if recorded is not None:
                raw_key = raw_pointer.key
                raw_checksum = raw_pointer.checksum_sha256
            else:
                raw_key = None
                raw_checksum = None

        existing = self.session.scalar(select(Observation).where(Observation.claim_hash == envelope.claim_hash))
        if existing is not None:
            return PutResult(observation=existing, created=False)

        identity_hash = claim_hash(envelope.identity.slot_payload())
        values = {
            "id": new_ulid(),
            "source_id": source.id,
            "source_url_or_id": envelope.source_url_or_id,
            "published_at": envelope.published_at,
            "ingested_at": envelope.ingested_at,
            "market_time": envelope.market_time,
            "claim_text": envelope.claim_text,
            "claim_hash": envelope.claim_hash,
            "identity_hash": identity_hash,
            "confidence": Decimal(str(envelope.confidence)),
            "evidence_type": envelope.evidence_type.value,
            "data_quality": envelope.data_quality.value,
            "payload_json": envelope.payload,
            "raw_object_key": raw_key,
            "raw_object_checksum": raw_checksum,
            # Knowledge watermark is lab ingest time. published_at / market_time never gate knowledge.
            "as_of_knowledge": envelope.ingested_at,
            "instrument": envelope.instrument,
            "metric": envelope.metric,
        }
        stmt = (
            pg_insert(Observation)
            .values(**values)
            .on_conflict_do_nothing(constraint="observation_claim_hash_uidx")
            .returning(Observation.id)
        )
        inserted = self.session.execute(stmt).first()
        if inserted is None:
            raced = self.session.scalar(select(Observation).where(Observation.claim_hash == envelope.claim_hash))
            assert raced is not None
            return PutResult(observation=raced, created=False)
        row = self.session.get(Observation, inserted[0])
        assert row is not None
        contradicted = self._link_contradictions(row)
        return PutResult(observation=row, created=True, contradicted=contradicted)

    def link(
        self,
        observation_id: str,
        related_observation_id: str,
        relation: ObservationRelation | str,
    ) -> ObservationLink | None:
        rel = relation.value if isinstance(relation, ObservationRelation) else relation
        if observation_id == related_observation_id:
            return None
        stmt = (
            pg_insert(ObservationLink)
            .values(
                observation_id=observation_id,
                related_observation_id=related_observation_id,
                relation=rel,
            )
            .on_conflict_do_nothing(constraint="observation_link_unique")
            .returning(ObservationLink.id)
        )
        inserted = self.session.execute(stmt).first()
        self.session.flush()
        if inserted is None:
            return self.session.scalar(
                select(ObservationLink).where(
                    ObservationLink.observation_id == observation_id,
                    ObservationLink.related_observation_id == related_observation_id,
                    ObservationLink.relation == rel,
                )
            )
        return self.session.get(ObservationLink, inserted[0])

    def _link_contradictions(self, row: Observation) -> bool:
        others = list(
            self.session.scalars(
                select(Observation).where(
                    Observation.id != row.id,
                    Observation.identity_hash == row.identity_hash,
                    Observation.claim_hash != row.claim_hash,
                    Observation.data_quality != DataQuality.REJECTED.value,
                )
            ).all()
        )
        if not others:
            return False
        for other in others:
            self.link(row.id, other.id, ObservationRelation.CONTRADICTS)
            self.link(other.id, row.id, ObservationRelation.CONTRADICTS)
            if other.data_quality == DataQuality.OK.value:
                other.data_quality = DataQuality.CONTRADICTED.value
        if row.data_quality == DataQuality.OK.value:
            row.data_quality = DataQuality.CONTRADICTED.value
        self.session.flush()
        return True
