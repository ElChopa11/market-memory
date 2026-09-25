"""Persist schedule_heartbeat rows. Secondary log — miss sweep is the control."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from mm_common.ids import new_ulid
from mm_common.time import as_utc, parse_utc
from mm_memory.models import ScheduleHeartbeat


def _ts(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return as_utc(value)
    return parse_utc(str(value))


def persist_heartbeat(session: Session, row: Mapping[str, Any]) -> str:
    """Insert one row per (routine_id, scheduled_anchor_ts, run_id).

    A different run_id is a new row. The same run_id returns the existing id
    and does not replace that row's bytes. Miss-sweep still treats any fire
    for the anchor as closing the window; it does not need the table to keep
    only one row.
    """
    routine_id = str(row["routine_id"])
    anchor = _ts(row["scheduled_anchor_ts"])
    run_id = str(row.get("run_id") or new_ulid())
    existing = session.scalar(
        select(ScheduleHeartbeat).where(
            ScheduleHeartbeat.routine_id == routine_id,
            ScheduleHeartbeat.scheduled_anchor_ts == anchor,
            ScheduleHeartbeat.run_id == run_id,
        )
    )
    if existing is not None:
        return existing.id
    fired_raw = row.get("fired_at_ts")
    fired = None if fired_raw in (None, "") else _ts(fired_raw)
    status = str(row.get("status") or "missed")
    as_of = _ts(row.get("as_of_knowledge") or fired_raw or row["scheduled_anchor_ts"])
    nested = dict(row.get("payload_json") or {})
    if row.get("exit_status") is not None:
        nested["exit_status"] = int(row["exit_status"])
    if row.get("payload_path"):
        nested["payload_path"] = str(row["payload_path"])
    if row.get("cli"):
        nested["cli"] = str(row["cli"])
    if row.get("reason"):
        nested["reason"] = str(row["reason"])
    record = ScheduleHeartbeat(
        id=new_ulid(),
        routine_id=routine_id,
        run_id=run_id,
        scheduled_anchor_ts=anchor,
        fired_at_ts=fired,
        delta_seconds=None if row.get("delta_seconds") is None else int(row["delta_seconds"]),
        status=status,
        as_of_knowledge=as_of,
        source=str(row.get("source") or "lab"),
        payload_json=nested,
    )
    session.add(record)
    session.flush()
    return record.id


def load_completions(session: Session) -> list[dict[str, Any]]:
    rows = session.scalars(select(ScheduleHeartbeat).order_by(ScheduleHeartbeat.scheduled_anchor_ts)).all()
    out: list[dict[str, Any]] = []
    for row in rows:
        nested = dict(row.payload_json or {})
        item: dict[str, Any] = {
            "routine_id": row.routine_id,
            "run_id": row.run_id,
            "scheduled_anchor_ts": as_utc(row.scheduled_anchor_ts).isoformat(),
            "fired_at_ts": None if row.fired_at_ts is None else as_utc(row.fired_at_ts).isoformat(),
            "delta_seconds": row.delta_seconds,
            "status": row.status,
            "as_of_knowledge": as_utc(row.as_of_knowledge).isoformat(),
            "source": row.source,
            "payload_json": nested,
        }
        if nested.get("exit_status") is not None:
            item["exit_status"] = nested["exit_status"]
        if nested.get("payload_path"):
            item["payload_path"] = nested["payload_path"]
        if nested.get("cli"):
            item["cli"] = nested["cli"]
        if nested.get("reason"):
            item["reason"] = nested["reason"]
        out.append(item)
    return out


def persist_many(session: Session, rows: Iterable[Mapping[str, Any]]) -> list[str]:
    return [persist_heartbeat(session, row) for row in rows]
