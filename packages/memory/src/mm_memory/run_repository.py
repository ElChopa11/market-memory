"""Persist research_run rows (backtest / scan / manual)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from mm_common.ids import new_ulid
from mm_memory.models import ResearchRun


class ResearchRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        *,
        kind: str,
        params_hash: str,
        started_at: datetime,
        finished_at: datetime | None = None,
        thesis_id: str | None = None,
        result_summary: dict[str, Any] | None = None,
        artifact_paths: list[Any] | None = None,
        run_id: str | None = None,
    ) -> ResearchRun:
        row = ResearchRun(
            id=run_id or new_ulid(),
            thesis_id=thesis_id,
            kind=kind,
            started_at=started_at,
            finished_at=finished_at,
            params_hash=params_hash,
            result_summary=result_summary or {},
            artifact_paths=artifact_paths or [],
        )
        self.session.add(row)
        self.session.flush()
        return row

    def get(self, run_id: str) -> ResearchRun | None:
        return self.session.get(ResearchRun, run_id)

    def list_runs(
        self,
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
        return list(self.session.scalars(stmt).all())
