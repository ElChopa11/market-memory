"""Point-in-time Market Memory queries.

Contract: what_did_we_know(ts) = observations where ingested_at <= ts.
Never use published_at alone (avoids look-ahead from delayed ingest).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from mm_common.enums import DataQuality
from mm_common.time import as_utc
from mm_memory.models import Observation


def what_did_we_know_statement(
    ts: datetime,
    *,
    instrument: str | None = None,
    metric: str | None = None,
    include_rejected: bool = False,
) -> Select[tuple[Observation]]:
    knowledge_time = as_utc(ts)
    stmt = select(Observation).where(Observation.ingested_at <= knowledge_time)
    if not include_rejected:
        stmt = stmt.where(Observation.data_quality != DataQuality.REJECTED.value)
    if instrument is not None:
        stmt = stmt.where(Observation.instrument == instrument)
    if metric is not None:
        stmt = stmt.where(Observation.metric == metric)
    return stmt.order_by(Observation.ingested_at.asc(), Observation.id.asc())


def what_did_we_know(
    session: Session,
    ts: datetime,
    *,
    instrument: str | None = None,
    metric: str | None = None,
    include_rejected: bool = False,
) -> list[Observation]:
    """Observations known at *ts* (ingested_at <= ts)."""
    stmt = what_did_we_know_statement(
        ts,
        instrument=instrument,
        metric=metric,
        include_rejected=include_rejected,
    )
    return list(session.scalars(stmt).all())
