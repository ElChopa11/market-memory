"""Phase 6a desk mesh envelopes. Persist full envelopes; NOTIFY is ids only.

Must not import mm_desks (Intel/memory stays off the opine packages).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from mm_common.time import as_utc, utcnow
from mm_memory.models import DeskEnvelopeRow, DeskHealthRow


class MeshEnvelopeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, envelope_id: str) -> DeskEnvelopeRow | None:
        return self.session.get(DeskEnvelopeRow, envelope_id)

    def find_duplicate(self, *, desk: str, as_of: datetime, content_hash: str) -> DeskEnvelopeRow | None:
        return self.session.scalar(
            select(DeskEnvelopeRow).where(
                DeskEnvelopeRow.desk == desk,
                DeskEnvelopeRow.as_of_knowledge == as_utc(as_of),
                DeskEnvelopeRow.content_hash == content_hash,
            )
        )

    def latest(self, desk: str, as_of: datetime) -> DeskEnvelopeRow | None:
        stmt = (
            select(DeskEnvelopeRow)
            .where(DeskEnvelopeRow.desk == desk, DeskEnvelopeRow.as_of_knowledge == as_utc(as_of))
            .order_by(DeskEnvelopeRow.created_at.desc(), DeskEnvelopeRow.id.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def list_for_as_of(self, as_of: datetime) -> list[DeskEnvelopeRow]:
        stmt = (
            select(DeskEnvelopeRow)
            .where(DeskEnvelopeRow.as_of_knowledge == as_utc(as_of))
            .order_by(DeskEnvelopeRow.desk.asc(), DeskEnvelopeRow.created_at.asc())
        )
        return list(self.session.scalars(stmt).all())

    def put(self, fields: dict[str, Any]) -> tuple[DeskEnvelopeRow, bool]:
        existing = self.find_duplicate(
            desk=str(fields["desk"]),
            as_of=fields["as_of_knowledge"],
            content_hash=str(fields["content_hash"]),
        )
        if existing is not None:
            self._upsert_health(existing)
            return existing, False
        row = DeskEnvelopeRow(
            id=str(fields["id"]),
            desk=str(fields["desk"]),
            channel=str(fields["channel"]),
            as_of_knowledge=as_utc(fields["as_of_knowledge"]),
            as_of_sydney=str(fields["as_of_sydney"]),
            status=str(fields["status"]),
            n=int(fields["n"]),
            completeness_pct=fields["completeness_pct"],
            regime=str(fields.get("regime") or "unset"),
            op=str(fields["op"]),
            universe=str(fields["universe"]),
            sources=list(fields.get("sources") or []),
            missing=list(fields.get("missing") or []),
            cadence=str(fields["cadence"]),
            content_hash=str(fields["content_hash"]),
            error_class=fields.get("error_class"),
            body_json=dict(fields.get("body_json") or {}),
            alert_channel=fields.get("alert_channel"),
            dq_channel=fields.get("dq_channel"),
        )
        self.session.add(row)
        self.session.flush()
        self._upsert_health(row)
        return row, True

    def _upsert_health(self, row: DeskEnvelopeRow) -> None:
        health = self.session.get(DeskHealthRow, row.desk)
        if health is None:
            health = DeskHealthRow(desk=row.desk, status=row.status)
            self.session.add(health)
        health.status = row.status
        health.last_as_of = row.as_of_knowledge
        health.last_envelope_id = row.id
        health.last_content_hash = row.content_hash
        health.error_class = row.error_class
        health.n = int(row.n)
        health.completeness_pct = row.completeness_pct
        health.updated_at = utcnow()
        self.session.flush()

    def get_health(self, desk: str) -> DeskHealthRow | None:
        return self.session.get(DeskHealthRow, desk)

    def list_health(self) -> list[DeskHealthRow]:
        return list(self.session.scalars(select(DeskHealthRow).order_by(DeskHealthRow.desk.asc())).all())
