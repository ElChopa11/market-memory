"""SQLAlchemy models for Market Memory core tables (Phase 1)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from mm_common.enums import DATA_QUALITY_VALUES, EVIDENCE_TYPE_VALUES, OBSERVATION_RELATION_VALUES, SOURCE_KIND_VALUES


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "source"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('" + "','".join(SOURCE_KIND_VALUES) + "')",
            name="source_kind_check",
        ),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    trust_tier: Mapped[int] = mapped_column(nullable=False, default=3)
    tos_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    observations: Mapped[list[Observation]] = relationship(back_populates="source")


class RawObject(Base):
    """Object-store pointer inventory (checksum + key, never secrets)."""

    __tablename__ = "raw_object"
    __table_args__ = (UniqueConstraint("bucket", "object_key", name="raw_object_bucket_key_uidx"),)

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    bucket: Mapped[str] = mapped_column(Text, nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    content_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    byte_size: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Observation(Base):
    __tablename__ = "observation"
    __table_args__ = (
        CheckConstraint(
            "evidence_type IN ('" + "','".join(EVIDENCE_TYPE_VALUES) + "')",
            name="observation_evidence_type_check",
        ),
        CheckConstraint(
            "data_quality IN ('" + "','".join(DATA_QUALITY_VALUES) + "')",
            name="observation_data_quality_check",
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="observation_confidence_check"),
        UniqueConstraint("claim_hash", name="observation_claim_hash_uidx"),
        Index("observation_ingested_at_idx", "ingested_at"),
        Index("observation_market_time_idx", "market_time"),
        Index("observation_identity_hash_idx", "identity_hash"),
        Index("observation_identity_idx", "source_id", "instrument", "metric", "market_time"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("source.id"), nullable=False, index=True)
    source_url_or_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    market_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(32), nullable=False)
    data_quality: Mapped[str] = mapped_column(String(32), nullable=False, default="ok")
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    raw_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_object_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    as_of_knowledge: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    instrument: Mapped[str] = mapped_column(Text, nullable=False)
    metric: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    source: Mapped[Source] = relationship(back_populates="observations")


class ObservationLink(Base):
    __tablename__ = "observation_link"
    __table_args__ = (
        CheckConstraint(
            "relation IN ('" + "','".join(OBSERVATION_RELATION_VALUES) + "')",
            name="observation_link_relation_check",
        ),
        CheckConstraint("observation_id <> related_observation_id", name="observation_link_no_self"),
        UniqueConstraint(
            "observation_id",
            "related_observation_id",
            "relation",
            name="observation_link_unique",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    observation_id: Mapped[str] = mapped_column(ForeignKey("observation.id"), nullable=False, index=True)
    related_observation_id: Mapped[str] = mapped_column(ForeignKey("observation.id"), nullable=False, index=True)
    relation: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
