"""Persist generated Market Pulse briefs (optional index; git/markdown remains the artifact)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from mm_common.ids import new_ulid
from mm_memory.models import Brief


class BriefRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def put(
        self,
        *,
        kind: str,
        session_date: date,
        generated_at: datetime,
        as_of_knowledge: datetime,
        artifact_git_path: str,
        content_hash: str,
        data_quality: str,
        payload_json: dict[str, Any] | None = None,
    ) -> Brief:
        existing = self.session.scalar(
            select(Brief).where(Brief.kind == kind, Brief.session_date == session_date, Brief.content_hash == content_hash)
        )
        if existing is not None:
            return existing
        row = Brief(
            id=new_ulid(),
            kind=kind,
            session_date=session_date,
            generated_at=generated_at,
            as_of_knowledge=as_of_knowledge,
            artifact_git_path=artifact_git_path,
            content_hash=content_hash,
            data_quality=data_quality,
            payload_json=payload_json or {},
        )
        self.session.add(row)
        self.session.flush()
        return row

    def list_for_session(self, session_date: date, *, kind: str | None = None) -> list[Brief]:
        stmt = select(Brief).where(Brief.session_date == session_date).order_by(Brief.generated_at.asc(), Brief.id.asc())
        if kind is not None:
            stmt = stmt.where(Brief.kind == kind)
        return list(self.session.scalars(stmt).all())
