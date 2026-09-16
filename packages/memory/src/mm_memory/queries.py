"""Point-in-time Market Memory queries.

Contract: what_did_we_know(T) = observations where as_of_knowledge <= T.

Writers MUST set as_of_knowledge = ingested_at (lab knowledge time). A database
check constraint enforces that lockstep. published_at and market_time NEVER gate
knowledge — they are provenance (lab capture vs exchange event time), not the
investigator watermark.

Exactly one definition of “what did we know at T?”: as_of_knowledge <= T.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from mm_common.enums import DataQuality
from mm_common.time import as_utc
from mm_memory.models import Observation, PaperTrade, ResearchRun, Thesis


def what_did_we_know_statement(
    ts: datetime,
    *,
    instrument: str | None = None,
    metric: str | None = None,
    include_rejected: bool = False,
) -> Select[tuple[Observation]]:
    knowledge_time = as_utc(ts)
    stmt = select(Observation).where(Observation.as_of_knowledge <= knowledge_time)
    if not include_rejected:
        stmt = stmt.where(Observation.data_quality != DataQuality.REJECTED.value)
    if instrument is not None:
        stmt = stmt.where(Observation.instrument == instrument)
    if metric is not None:
        stmt = stmt.where(Observation.metric == metric)
    return stmt.order_by(Observation.as_of_knowledge.asc(), Observation.id.asc())


def what_did_we_know(
    session: Session,
    ts: datetime,
    *,
    instrument: str | None = None,
    metric: str | None = None,
    include_rejected: bool = False,
) -> list[Observation]:
    """Observations known at *ts* (as_of_knowledge <= ts).

    published_at and market_time are ignored. as_of_knowledge is always equal to
    ingested_at (lab knowledge time).
    """
    stmt = what_did_we_know_statement(
        ts,
        instrument=instrument,
        metric=metric,
        include_rejected=include_rejected,
    )
    return list(session.scalars(stmt).all())


def list_theses(
    session: Session,
    *,
    status: str | None = None,
) -> list[Thesis]:
    """Return thesis indexes. Rejected rows are included unless *status* filters them in."""
    stmt = select(Thesis).order_by(Thesis.created_at.asc(), Thesis.slug.asc())
    if status is not None:
        stmt = stmt.where(Thesis.status == status)
    return list(session.scalars(stmt).all())


def get_thesis_by_slug(session: Session, slug: str) -> Thesis | None:
    return session.scalar(select(Thesis).where(Thesis.slug == slug))


def list_research_runs(
    session: Session,
    *,
    thesis_id: str | None = None,
    kind: str | None = None,
    params_hash: str | None = None,
) -> list[ResearchRun]:
    stmt = select(ResearchRun).order_by(ResearchRun.started_at.asc(), ResearchRun.id.asc())
    if thesis_id is not None:
        stmt = stmt.where(ResearchRun.thesis_id == thesis_id)
    if kind is not None:
        stmt = stmt.where(ResearchRun.kind == kind)
    if params_hash is not None:
        stmt = stmt.where(ResearchRun.params_hash == params_hash)
    return list(session.scalars(stmt).all())


def list_paper_trades(
    session: Session,
    *,
    thesis_id: str | None = None,
    status: str | None = None,
) -> list[PaperTrade]:
    stmt = select(PaperTrade).order_by(PaperTrade.opened_at.asc(), PaperTrade.id.asc())
    if thesis_id is not None:
        stmt = stmt.where(PaperTrade.thesis_id == thesis_id)
    if status is not None:
        stmt = stmt.where(PaperTrade.status == status)
    return list(session.scalars(stmt).all())
