"""IMP-042: schedule_heartbeat table + persist (log). Miss sweep is the control."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import inspect

from mm_desks.scheduler import classify_fire, parse_utc
from mm_memory.db import make_engine
from mm_memory.heartbeat_repository import load_completions, persist_heartbeat
from mm_memory.migrate import alembic_head, current_revision

UTC = timezone.utc


def test_schedule_heartbeat_migrated(postgres_dsn: str) -> None:
    engine = make_engine(postgres_dsn)
    tables = set(inspect(engine).get_table_names())
    assert "schedule_heartbeat" in tables
    assert current_revision(postgres_dsn) == alembic_head()
    assert len(alembic_head()) <= 32
    columns = {col["name"] for col in inspect(engine).get_columns("schedule_heartbeat")}
    assert {
        "routine_id",
        "run_id",
        "scheduled_anchor_ts",
        "fired_at_ts",
        "delta_seconds",
        "status",
        "as_of_knowledge",
    } <= columns


def test_persist_idempotent_and_fire_outranks_miss(db_session) -> None:
    anchor = "2026-09-18T22:00:00+00:00"
    miss = {
        "routine_id": "grok.sydney_morning_digest_8am",
        "run_id": "miss-detector",
        "scheduled_anchor_ts": anchor,
        "fired_at_ts": None,
        "delta_seconds": None,
        "status": "missed",
        "as_of_knowledge": "2026-09-19T09:49:00Z",
        "source": "miss_sweep",
    }
    first = persist_heartbeat(db_session, miss)
    db_session.flush()
    fired_at = datetime(2026, 9, 18, 22, 2, tzinfo=UTC)
    delta, status = classify_fire(parse_utc(anchor), fired_at, 300)
    fire = {
        "routine_id": "grok.sydney_morning_digest_8am",
        "run_id": "late-fire",
        "scheduled_anchor_ts": anchor,
        "fired_at_ts": fired_at.isoformat(),
        "delta_seconds": delta,
        "status": status,
        "as_of_knowledge": fired_at.isoformat(),
        "source": "lab",
    }
    second = persist_heartbeat(db_session, fire)
    assert first == second
    rows = load_completions(db_session)
    assert len(rows) == 1
    assert rows[0]["status"] == "ok"
    assert rows[0]["delta_seconds"] == 120
    assert rows[0]["as_of_knowledge"].startswith("2026-09-18")
