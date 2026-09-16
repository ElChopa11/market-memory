"""Integration: thesis indexes, evidence FKs, rejected retention."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import inspect, select

from mm_common.enums import DataQuality, EvidenceType, SourceKind, ThesisStatus
from mm_common.ids import new_ulid
from mm_common.schemas import ClaimIdentity, ObservationEnvelope
from mm_memory.db import make_engine
from mm_memory.migrate import current_revision
from mm_memory.models import SkepticReview, Thesis, ThesisEvidence
from mm_memory.repository import ObservationRepository
from mm_memory.thesis_repository import ThesisRepository, UnknownObservationError
from mm_research_kit.evidence import link_evidence
from mm_research_kit.lifecycle import read_status
from mm_research_kit.skeptic import record_skeptic_verdict
from mm_research_kit.workspace import ThesisSpec, create_thesis_from_intent

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates"


def _seed_observation(session) -> str:
    repo = ObservationRepository(session)
    ts = datetime(2026, 9, 16, tzinfo=timezone.utc)
    identity = ClaimIdentity(
        source_name="hyperliquid.info",
        instrument="BTC",
        metric="funding",
        market_time=ts,
        value="0.0001",
    )
    envelope = ObservationEnvelope(
        source_name="hyperliquid.info",
        source_kind=SourceKind.EXCHANGE,
        source_url_or_id="info:funding",
        published_at=ts,
        ingested_at=ts,
        market_time=ts,
        claim_text="BTC funding 0.0001",
        confidence=0.9,
        evidence_type=EvidenceType.METRIC,
        data_quality=DataQuality.OK,
        payload={"value": "0.0001"},
        instrument="BTC",
        metric="funding",
        identity=identity,
    )
    result = repo.put_observation(envelope)
    session.flush()
    return result.observation.id


def test_phase2_tables_exist(postgres_dsn: str) -> None:
    engine = make_engine(postgres_dsn)
    tables = set(inspect(engine).get_table_names())
    assert {"thesis", "thesis_evidence", "skeptic_review"} <= tables
    assert current_revision(postgres_dsn) == "0004_phase4"


def test_thesis_evidence_and_rejected_retention(db_session, tmp_path: Path) -> None:
    observation_id = _seed_observation(db_session)
    created = create_thesis_from_intent(
        research_root=tmp_path / "research",
        templates_root=TEMPLATES,
        spec=ThesisSpec(
            goal="BTC funding fade",
            owner="Research",
            instrument="BTC",
            hypothesis="Crowding unwinds.",
        ),
        repo_root=tmp_path,
    )
    repo = ThesisRepository(db_session)
    record = repo.upsert(
        slug=created.slug,
        status=created.status,
        author_role="Research",
        artifact_git_path=created.artifact_git_path,
        artifact_content_hash=created.artifact_content_hash,
        instrument="BTC",
        horizon="5d",
    )
    db_session.flush()

    try:
        repo.link_evidence(thesis_id=record.thesis.id, observation_id="not-a-real-obs", role="supports")
        raise AssertionError("expected unknown observation")
    except UnknownObservationError:
        pass

    link_evidence(created.path, observation_id=observation_id, role="supports", notes="fixture")
    repo.link_evidence(
        thesis_id=record.thesis.id,
        observation_id=observation_id,
        role="supports",
        notes="fixture",
    )
    db_session.flush()
    links = list(db_session.scalars(select(ThesisEvidence).where(ThesisEvidence.thesis_id == record.thesis.id)).all())
    assert len(links) == 1
    assert links[0].observation_id == observation_id

    status = record_skeptic_verdict(
        created.path,
        verdict="reject",
        reviewer="Skeptic",
        findings="Already priced.",
    )
    assert status == ThesisStatus.REJECTED.value
    repo.upsert(
        slug=created.slug,
        status=status,
        author_role="Research",
        artifact_git_path=created.artifact_git_path,
        artifact_content_hash=created.artifact_content_hash,
        instrument="BTC",
    )
    repo.record_skeptic(
        thesis_id=record.thesis.id,
        reviewer_id_or_role="Skeptic",
        verdict="reject",
        findings_json={"notes": "Already priced."},
        artifact_git_path=str(created.path / "skeptic-review.md"),
        content_hash=created.artifact_content_hash,
    )
    db_session.commit()

    rejected = repo.list_theses(status=ThesisStatus.REJECTED.value)
    assert any(row.slug == created.slug for row in rejected)
    all_rows = repo.list_theses()
    assert any(row.slug == created.slug and row.status == "rejected" for row in all_rows)
    still = db_session.get(Thesis, record.thesis.id)
    assert still is not None
    assert still.status == "rejected"
    assert created.path.is_dir()
    assert read_status(created.path) == "rejected"
    reviews = list(db_session.scalars(select(SkepticReview).where(SkepticReview.thesis_id == record.thesis.id)).all())
    assert reviews and reviews[0].verdict == "reject"


def test_ulid_helper_still_26() -> None:
    assert len(new_ulid()) == 26
