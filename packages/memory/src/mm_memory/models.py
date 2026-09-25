"""SQLAlchemy models for Market Memory core tables (Phase 1)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from mm_common.enums import (
    DATA_QUALITY_VALUES,
    EVIDENCE_ROLE_VALUES,
    EVIDENCE_TYPE_VALUES,
    OBSERVATION_RELATION_VALUES,
    PAPER_TRADE_STATUS_VALUES,
    RESEARCH_RUN_KIND_VALUES,
    RISK_DECISION_VALUES,
    SKEPTIC_VERDICT_VALUES,
    SOURCE_KIND_VALUES,
    THESIS_STATUS_VALUES,
)


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
        CheckConstraint(
            "as_of_knowledge = ingested_at",
            name="observation_as_of_knowledge_eq_ingested_at",
        ),
        UniqueConstraint("claim_hash", name="observation_claim_hash_uidx"),
        Index("observation_ingested_at_idx", "ingested_at"),
        Index("observation_as_of_knowledge_idx", "as_of_knowledge"),
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
    thesis_links: Mapped[list["ThesisEvidence"]] = relationship(back_populates="observation")


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


class Thesis(Base):
    """Hypothesis / thesis index. Git artifacts remain the human-review source."""

    __tablename__ = "thesis"
    __table_args__ = (
        CheckConstraint(
            "status IN ('" + "','".join(THESIS_STATUS_VALUES) + "')",
            name="thesis_status_check",
        ),
        Index("thesis_status_idx", "status"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    author_role: Mapped[str] = mapped_column(Text, nullable=False, default="Research")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    artifact_git_path: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    instrument: Mapped[str | None] = mapped_column(Text, nullable=True)
    horizon: Mapped[str | None] = mapped_column(Text, nullable=True)
    invalidation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_budget_bps: Mapped[int | None] = mapped_column(nullable=True)

    evidence_links: Mapped[list["ThesisEvidence"]] = relationship(back_populates="thesis")
    skeptic_reviews: Mapped[list["SkepticReview"]] = relationship(back_populates="thesis")
    research_runs: Mapped[list["ResearchRun"]] = relationship(back_populates="thesis")
    paper_trades: Mapped[list["PaperTrade"]] = relationship(back_populates="thesis")
    status_events: Mapped[list["ThesisStatusEvent"]] = relationship(back_populates="thesis")


class ThesisEvidence(Base):
    __tablename__ = "thesis_evidence"
    __table_args__ = (
        CheckConstraint(
            "role IN ('" + "','".join(EVIDENCE_ROLE_VALUES) + "')",
            name="thesis_evidence_role_check",
        ),
        UniqueConstraint("thesis_id", "observation_id", "role", name="thesis_evidence_unique"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thesis_id: Mapped[str] = mapped_column(ForeignKey("thesis.id"), nullable=False, index=True)
    observation_id: Mapped[str] = mapped_column(ForeignKey("observation.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    thesis: Mapped[Thesis] = relationship(back_populates="evidence_links")
    observation: Mapped[Observation] = relationship(back_populates="thesis_links")


class SkepticReview(Base):
    __tablename__ = "skeptic_review"
    __table_args__ = (
        CheckConstraint(
            "verdict IN ('" + "','".join(SKEPTIC_VERDICT_VALUES) + "')",
            name="skeptic_review_verdict_check",
        ),
        Index("skeptic_review_thesis_id_idx", "thesis_id"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    thesis_id: Mapped[str] = mapped_column(ForeignKey("thesis.id"), nullable=False, index=True)
    reviewer_id_or_role: Mapped[str] = mapped_column(Text, nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    findings_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    artifact_git_path: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    thesis: Mapped[Thesis] = relationship(back_populates="skeptic_reviews")


class ResearchRun(Base):
    """Reproducible research/backtest run. params_hash identifies the experiment."""

    __tablename__ = "research_run"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('" + "','".join(RESEARCH_RUN_KIND_VALUES) + "')",
            name="research_run_kind_check",
        ),
        Index("research_run_thesis_id_idx", "thesis_id"),
        Index("research_run_params_hash_idx", "params_hash"),
        Index("research_run_kind_idx", "kind"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    thesis_id: Mapped[str | None] = mapped_column(ForeignKey("thesis.id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    params_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    result_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    artifact_paths: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    thesis: Mapped[Thesis | None] = relationship(back_populates="research_runs")


class PaperTrade(Base):
    """Shadow/paper ledger row. Cannot open without invalidation + max loss."""

    __tablename__ = "paper_trade"
    __table_args__ = (
        CheckConstraint(
            "status IN ('" + "','".join(PAPER_TRADE_STATUS_VALUES) + "')",
            name="paper_trade_status_check",
        ),
        CheckConstraint("length(btrim(invalidation)) > 0", name="paper_trade_invalidation_check"),
        CheckConstraint("length(btrim(max_loss)) > 0", name="paper_trade_max_loss_check"),
        CheckConstraint("max_loss_amount > 0", name="paper_trade_max_loss_amount_check"),
        Index("paper_trade_thesis_id_idx", "thesis_id"),
        Index("paper_trade_status_idx", "status"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    thesis_id: Mapped[str] = mapped_column(ForeignKey("thesis.id"), nullable=False, index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    instrument: Mapped[str] = mapped_column(Text, nullable=False)
    size: Mapped[str] = mapped_column(Text, nullable=False)
    invalidation: Mapped[str] = mapped_column(Text, nullable=False)
    max_loss: Mapped[str] = mapped_column(Text, nullable=False)
    max_loss_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    intent_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    fills_json: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    expected_path: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    realised_path: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    pnl: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    slippage_bps: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    exit_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_git_path: Mapped[str] = mapped_column(Text, nullable=False)
    entry_thesis_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    thesis: Mapped[Thesis] = relationship(back_populates="paper_trades")


class ThesisStatusEvent(Base):
    """Lifecycle transition log hook (actor, ts, reason). Thin Phase 5a table."""

    __tablename__ = "thesis_status_event"
    __table_args__ = (
        CheckConstraint(
            "from_status IN ('" + "','".join(THESIS_STATUS_VALUES) + "')",
            name="thesis_status_event_from_status_check",
        ),
        CheckConstraint(
            "to_status IN ('" + "','".join(THESIS_STATUS_VALUES) + "')",
            name="thesis_status_event_to_status_check",
        ),
        CheckConstraint(
            "risk_decision IN ('" + "','".join(RISK_DECISION_VALUES) + "')",
            name="thesis_status_event_risk_decision_check",
        ),
        Index("thesis_status_event_thesis_id_idx", "thesis_id"),
        Index("thesis_status_event_ts_idx", "ts"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    thesis_id: Mapped[str] = mapped_column(ForeignKey("thesis.id"), nullable=False, index=True)
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    risk_decision: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    principal_override: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    thesis: Mapped[Thesis] = relationship(back_populates="status_events")


class Brief(Base):
    """Optional Market Pulse index. Markdown under briefs/YYYY/MM/DD/ is the artifact."""

    __tablename__ = "brief"
    __table_args__ = (
        CheckConstraint("kind IN ('preopen','close','alert')", name="brief_kind_check"),
        CheckConstraint(
            "data_quality IN ('" + "','".join(DATA_QUALITY_VALUES) + "')",
            name="brief_data_quality_check",
        ),
        UniqueConstraint("kind", "session_date", "content_hash", name="brief_kind_session_hash_uidx"),
        Index("brief_session_date_idx", "session_date"),
        Index("brief_kind_idx", "kind"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    as_of_knowledge: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    artifact_git_path: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    data_quality: Mapped[str] = mapped_column(String(32), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DeskEnvelopeRow(Base):
    """Persisted Phase 6a desk mesh envelope. NOTIFY carries ids only."""

    __tablename__ = "desk_envelope"
    __table_args__ = (
        CheckConstraint("status IN ('OK','DEGRADED','FAILED')", name="desk_envelope_status_check"),
        CheckConstraint("op IN ('paper','observation')", name="desk_envelope_op_check"),
        CheckConstraint(
            "error_class IS NULL OR error_class IN ('desk_missing','desk_killed','desk_error','desk_timeout')",
            name="desk_envelope_error_class_check",
        ),
        CheckConstraint("completeness_pct >= 0 AND completeness_pct <= 100", name="desk_envelope_completeness_check"),
        UniqueConstraint("desk", "as_of_knowledge", "content_hash", name="desk_envelope_desk_as_of_hash_uidx"),
        Index("desk_envelope_desk_as_of_idx", "desk", "as_of_knowledge"),
        Index("desk_envelope_channel_idx", "channel"),
        Index("desk_envelope_as_of_idx", "as_of_knowledge"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    desk: Mapped[str] = mapped_column(String(32), nullable=False)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    as_of_knowledge: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    as_of_sydney: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    n: Mapped[int] = mapped_column(nullable=False)
    completeness_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    regime: Mapped[str] = mapped_column(Text, nullable=False, default="unset")
    op: Mapped[str] = mapped_column(String(32), nullable=False)
    universe: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    missing: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    cadence: Mapped[str] = mapped_column(String(32), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    error_class: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    alert_channel: Mapped[str | None] = mapped_column(Text, nullable=True)
    dq_channel: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DeskHealthRow(Base):
    """Last-seen mesh health per desk slug. Updated when an envelope is persisted."""

    __tablename__ = "desk_health"

    desk: Mapped[str] = mapped_column(String(32), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    last_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_envelope_id: Mapped[str | None] = mapped_column(String(26), nullable=True)
    last_content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_class: Mapped[str | None] = mapped_column(Text, nullable=True)
    n: Mapped[int] = mapped_column(nullable=False, default=0)
    completeness_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DeliveryEventRow(Base):
    """Telegram delivery attempt. FAILED rows escalate to Coord; never silent drop."""

    __tablename__ = "delivery_event"
    __table_args__ = (
        CheckConstraint("status IN ('DRY_RUN','SENT','FAILED','DEDUPE')", name="delivery_event_status_check"),
        Index("delivery_event_desk_as_of_idx", "desk", "as_of_knowledge"),
        Index("delivery_event_content_hash_idx", "content_hash"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    desk: Mapped[str] = mapped_column(String(64), nullable=False)
    as_of_knowledge: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    notes_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class InboundAuditRow(Base):
    """Read-only inbound Telegram audit. Unknown uid is a silent drop row."""

    __tablename__ = "inbound_audit"
    __table_args__ = (Index("inbound_audit_uid_idx", "uid"),)

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    uid: Mapped[str] = mapped_column(Text, nullable=False)
    command: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class LlmCallRow(Base):
    """Accountability ledger for WRITER/CRITIC calls. Prompt hash required."""

    __tablename__ = "llm_call"
    __table_args__ = (
        Index("llm_call_run_id_idx", "run_id"),
        Index("llm_call_desk_idx", "desk_slug"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    desk_slug: Mapped[str] = mapped_column(String(32), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_file: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str] = mapped_column(Text, nullable=False)
    temperature: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    input_tokens: Mapped[int] = mapped_column(nullable=False)
    output_tokens: Mapped[int] = mapped_column(nullable=False)
    cached_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    latency_ms: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    cost: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False, default=0)
    schema_valid: Mapped[bool] = mapped_column(nullable=False)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EventBaseRate(Base):
    """Unconditional event-class base-rate snapshot (IMP-039). One row per class."""

    __tablename__ = "event_base_rate"
    __table_args__ = (
        CheckConstraint(
            "as_of_knowledge = ingested_at",
            name="event_base_rate_as_of_knowledge_eq_ingested_at",
        ),
        CheckConstraint(
            "event_class IN ('dip_touch','zone_boundary_touch','pullback_ema_touch')",
            name="event_base_rate_event_class_check",
        ),
        UniqueConstraint(
            "event_class",
            "params_hash",
            "as_of_knowledge",
            name="event_base_rate_class_params_as_of_uidx",
        ),
        Index("event_base_rate_as_of_idx", "as_of_knowledge"),
        Index("event_base_rate_params_idx", "params_hash"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    event_class: Mapped[str] = mapped_column(String(32), nullable=False)
    as_of_knowledge: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    params_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    instrument_set: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    window_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    cost_model_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    n: Mapped[int] = mapped_column(nullable=False)
    n_min: Mapped[int] = mapped_column(nullable=False)
    claimed: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    hit_rate: Mapped[Decimal | None] = mapped_column(Numeric(16, 8), nullable=True)
    median_fwd_return: Mapped[Decimal | None] = mapped_column(Numeric(16, 8), nullable=True)
    mean_r_after_cost: Mapped[Decimal | None] = mapped_column(Numeric(16, 8), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    cites_candidate: Mapped[str] = mapped_column(String(16), nullable=False)
    survivorship_tag: Mapped[str] = mapped_column(Text, nullable=False)
    fixture_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ScheduleHeartbeat(Base):
    """Completion log for a scheduled anchor. Miss sweep is the control; this is the log."""

    __tablename__ = "schedule_heartbeat"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ok','late','missed','skipped','wrong_anchor')",
            name="schedule_heartbeat_status_check",
        ),
        UniqueConstraint(
            "routine_id",
            "scheduled_anchor_ts",
            name="schedule_heartbeat_routine_anchor_uidx",
        ),
        Index("schedule_heartbeat_as_of_idx", "as_of_knowledge"),
        Index("schedule_heartbeat_routine_idx", "routine_id"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    routine_id: Mapped[str] = mapped_column(Text, nullable=False)
    run_id: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_anchor_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fired_at_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delta_seconds: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    as_of_knowledge: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False, default="lab")
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


