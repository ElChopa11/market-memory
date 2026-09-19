"""IMP-039: event_base_rate table + persist + PIT visibility."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect

from mm_memory.base_rate_repository import persist_memory_rows, rows_visible_at
from mm_memory.db import make_engine
from mm_memory.migrate import alembic_head, current_revision
from mm_quant.base_rates import snapshot_from_fixture

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "tests" / "fixtures" / "phase1_base_rates" / "panel.json"


def test_event_base_rate_migrated(postgres_dsn: str) -> None:
    engine = make_engine(postgres_dsn)
    tables = set(inspect(engine).get_table_names())
    assert "event_base_rate" in tables
    assert current_revision(postgres_dsn) == alembic_head()
    assert alembic_head() == "0011_schedule_heartbeat"
    columns = {col["name"] for col in inspect(engine).get_columns("event_base_rate")}
    assert {
        "event_class",
        "as_of_knowledge",
        "ingested_at",
        "params_hash",
        "content_hash",
        "instrument_set",
        "window_json",
        "cost_model_json",
        "claimed",
        "cites_candidate",
    } <= columns
    checks = {c["name"] for c in inspect(engine).get_check_constraints("event_base_rate")}
    assert "event_base_rate_as_of_knowledge_eq_ingested_at" in checks


def test_persist_is_idempotent_and_pit(db_session) -> None:
    snap = snapshot_from_fixture(PANEL, repo_root=ROOT)
    rows = [snap.memory_row(rate) for rate in snap.rates]
    assert len(rows) == 3
    first = persist_memory_rows(db_session, rows)
    db_session.flush()
    second = persist_memory_rows(db_session, rows)
    assert first == second
    visible = rows_visible_at(db_session, snap.canonical()["as_of_knowledge"])
    assert {row.event_class for row in visible} == {
        "dip_touch",
        "zone_boundary_touch",
        "pullback_ema_touch",
    }
    for row in visible:
        assert row.as_of_knowledge == row.ingested_at
        assert row.params_hash == snap.params_hash
        assert row.claimed is False
    assert rows_visible_at(db_session, "2020-01-01T00:00:00Z") == []


def test_persist_rejects_clock_skew(db_session) -> None:
    snap = snapshot_from_fixture(PANEL, repo_root=ROOT)
    payload = dict(snap.memory_row(snap.rates[0]))
    payload["ingested_at"] = "2020-01-01T00:00:00Z"
    with pytest.raises(ValueError, match="lockstep"):
        persist_memory_rows(db_session, [payload])
