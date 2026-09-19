"""Persist schedule_heartbeat rows. Secondary log — miss sweep is the control."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from mm_common.ids import new_ulid
from mm_common.time import as_utc, parse_utc
from mm_memory.models import ScheduleHeartbeat

RANK = {"ok": 3, "late": 2, "skipped": 1, "missed": 0}


def _ts(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return as_utc(value)
    return parse_utc(str(value))


def persist_heartbeat(session: Session, row: Mapping[str, Any]) -> str:
    """Idempotent on (routine_id, scheduled_anchor_ts). Higher-rank status wins."""
    routine_id = str(row["routine_id"])
    anchor = _ts(row["scheduled_anchor_ts"])
    existing = session.scalar(
        select(ScheduleHeartbeat).where(
            ScheduleHeartbeat.routine_id == routine_id,
            ScheduleHeartbeat.scheduled_anchor_ts == anchor,
        )
    )
    fired_raw = row.get("fired_at_ts")
    fired = None if fired_raw in (None, "") else _ts(fired_raw)
    status = str(row.get("status") or "missed")
    as_of = _ts(row.get("as_of_knowledge") or fired_raw or row["scheduled_anchor_ts"])
    payload = {
        "run_id": str(row.get("run_id") or new_ulid()),
        "fired_at_ts": fired,
        "delta_seconds": None if row.get("delta_seconds") is None else int(row["delta_seconds"]),
        "status": status,
        "as_of_knowledge": as_of,
        "source": str(row.get("source") or "lab"),
        "payload_json": dict(row.get("payload_json") or {}),
    }
    if existing is not None:
        if RANK.get(status, 0) >= RANK.get(existing.status, 0):
            existing.run_id = payload["run_id"]
            existing.fired_at_ts = payload["fired_at_ts"]
            existing.delta_seconds = payload["delta_seconds"]
            existing.status = payload["status"]
            existing.as_of_knowledge = payload["as_of_knowledge"]
            existing.source = payload["source"]
            existing.payload_json = payload["payload_json"]
        session.flush()
        return existing.id
    record = ScheduleHeartbeat(
        id=new_ulid(),
        routine_id=routine_id,
        run_id=payload["run_id"],
        scheduled_anchor_ts=anchor,
        fired_at_ts=payload["fired_at_ts"],
        delta_seconds=payload["delta_seconds"],
        status=payload["status"],
        as_of_knowledge=payload["as_of_knowledge"],
        source=payload["source"],
        payload_json=payload["payload_json"],
    )
    session.add(record)
    session.flush()
    return record.id


def load_completions(session: Session) -> list[dict[str, Any]]:
    rows = session.scalars(select(ScheduleHeartbeat).order_by(ScheduleHeartbeat.scheduled_anchor_ts)).all()
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "routine_id": row.routine_id,
                "run_id": row.run_id,
                "scheduled_anchor_ts": as_utc(row.scheduled_anchor_ts).isoformat(),
                "fired_at_ts": None if row.fired_at_ts is None else as_utc(row.fired_at_ts).isoformat(),
                "delta_seconds": row.delta_seconds,
                "status": row.status,
                "as_of_knowledge": as_utc(row.as_of_knowledge).isoformat(),
                "source": row.source,
            }
        )
    return out


def persist_many(session: Session, rows: Iterable[Mapping[str, Any]]) -> list[str]:
    return [persist_heartbeat(session, row) for row in rows]
