"""Persist thesis indexes and evidence links. Git remains the human-review source."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from mm_common.ids import new_ulid
from mm_memory.models import Observation, SkepticReview, Thesis, ThesisEvidence, ThesisStatusEvent


class UnknownObservationError(ValueError):
    """Raised when linking evidence to an observation id that is not in Market Memory."""


@dataclass(frozen=True)
class ThesisRecord:
    thesis: Thesis
    created: bool


class ThesisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_slug(self, slug: str) -> Thesis | None:
        return self.session.scalar(select(Thesis).where(Thesis.slug == slug))

    def get(self, thesis_id: str) -> Thesis | None:
        return self.session.get(Thesis, thesis_id)

    def upsert(
        self,
        *,
        slug: str,
        status: str,
        author_role: str,
        artifact_git_path: str,
        artifact_content_hash: str,
        instrument: str | None = None,
        horizon: str | None = None,
        invalidation_summary: str | None = None,
        risk_budget_bps: int | None = None,
    ) -> ThesisRecord:
        existing = self.get_by_slug(slug)
        now = datetime.now(timezone.utc)
        if existing is None:
            row = Thesis(
                id=new_ulid(),
                slug=slug,
                status=status,
                author_role=author_role,
                artifact_git_path=artifact_git_path,
                artifact_content_hash=artifact_content_hash,
                instrument=instrument or None,
                horizon=horizon or None,
                invalidation_summary=invalidation_summary,
                risk_budget_bps=risk_budget_bps,
                created_at=now,
                updated_at=now,
            )
            self.session.add(row)
            self.session.flush()
            return ThesisRecord(thesis=row, created=True)
        existing.status = status
        existing.author_role = author_role
        existing.artifact_git_path = artifact_git_path
        existing.artifact_content_hash = artifact_content_hash
        existing.instrument = instrument or None
        existing.horizon = horizon or None
        if invalidation_summary is not None:
            existing.invalidation_summary = invalidation_summary
        existing.risk_budget_bps = risk_budget_bps
        existing.updated_at = now
        self.session.flush()
        return ThesisRecord(thesis=existing, created=False)

    def link_evidence(
        self,
        *,
        thesis_id: str,
        observation_id: str,
        role: str,
        notes: str | None = None,
    ) -> ThesisEvidence:
        observation = self.session.get(Observation, observation_id)
        if observation is None:
            raise UnknownObservationError(f"unknown observation id: {observation_id}")
        stmt = (
            pg_insert(ThesisEvidence)
            .values(
                thesis_id=thesis_id,
                observation_id=observation_id,
                role=role,
                notes=notes,
            )
            .on_conflict_do_nothing(constraint="thesis_evidence_unique")
            .returning(ThesisEvidence.id)
        )
        inserted = self.session.execute(stmt).first()
        self.session.flush()
        if inserted is None:
            row = self.session.scalar(
                select(ThesisEvidence).where(
                    ThesisEvidence.thesis_id == thesis_id,
                    ThesisEvidence.observation_id == observation_id,
                    ThesisEvidence.role == role,
                )
            )
            assert row is not None
            if notes is not None:
                row.notes = notes
            self.session.flush()
            return row
        row = self.session.get(ThesisEvidence, inserted[0])
        assert row is not None
        return row

    def record_skeptic(
        self,
        *,
        thesis_id: str,
        reviewer_id_or_role: str,
        verdict: str,
        findings_json: dict | None,
        artifact_git_path: str,
        content_hash: str,
    ) -> SkepticReview:
        row = SkepticReview(
            id=new_ulid(),
            thesis_id=thesis_id,
            reviewer_id_or_role=reviewer_id_or_role,
            verdict=verdict,
            findings_json=findings_json or {},
            artifact_git_path=artifact_git_path,
            content_hash=content_hash,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def list_theses(self, *, status: str | None = None) -> list[Thesis]:
        stmt = select(Thesis).order_by(Thesis.created_at.asc(), Thesis.slug.asc())
        if status is not None:
            stmt = stmt.where(Thesis.status == status)
        return list(self.session.scalars(stmt).all())

    def evidence_count(self, thesis_id: str) -> int:
        value = self.session.scalar(
            select(func.count()).select_from(ThesisEvidence).where(ThesisEvidence.thesis_id == thesis_id)
        )
        return int(value or 0)

    def log_status_event(
        self,
        *,
        thesis_id: str,
        from_status: str,
        to_status: str,
        actor: str,
        ts: datetime,
        reason: str,
        risk_decision: str = "pending",
        principal_override: bool = False,
    ) -> ThesisStatusEvent:
        row = ThesisStatusEvent(
            id=new_ulid(),
            thesis_id=thesis_id,
            from_status=from_status,
            to_status=to_status,
            actor=actor,
            ts=ts,
            reason=reason,
            risk_decision=risk_decision,
            principal_override=principal_override,
        )
        self.session.add(row)
        self.session.flush()
        return row
