"""Phase 6a Postgres LISTEN/NOTIFY: persist envelopes, lightweight notify, idempotency."""

from __future__ import annotations

import threading
from pathlib import Path

from sqlalchemy import inspect, text

from mm_desks.envelope import envelope_from_output
from mm_desks.mesh import mesh_from_fixture
from mm_desks.orchestrator import run_from_fixture
from mm_desks.pg import PostgresBus, PostgresEnvelopeStore
from mm_desks.protocol import FAILED
from mm_memory.migrate import alembic_head, current_revision
from mm_memory.notify import PostgresNotifyBus

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "phase5d" / "frozen_day.json"


def test_migrate_creates_mesh_tables(postgres_dsn: str) -> None:
    from mm_memory.db import make_engine

    engine = make_engine(postgres_dsn)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert "desk_envelope" in tables
    assert "desk_health" in tables
    assert current_revision(postgres_dsn) == alembic_head()
    columns = {col["name"] for col in inspector.get_columns("desk_envelope")}
    assert "content_hash" in columns
    assert "as_of_sydney" in columns
    assert "body_json" in columns
    uniques = {u["name"] for u in inspector.get_unique_constraints("desk_envelope")}
    assert "desk_envelope_desk_as_of_hash_uidx" in uniques


def test_persist_is_idempotent_and_notify_is_lightweight(db_session, postgres_dsn: str) -> None:
    result = run_from_fixture(FIXTURE, repo_root=ROOT, slugs=("intel",))
    env = envelope_from_output(result.desks[0], repo_root=ROOT)
    store = PostgresEnvelopeStore(db_session)
    assert store.put(env) is True
    db_session.commit()
    assert store.put(env) is False
    db_session.commit()
    loaded = store.latest("intel", result.as_of_knowledge)
    assert loaded is not None
    assert loaded.content_hash == env.content_hash
    assert loaded.body["slug"] == "intel"

    received: list = []
    ready = threading.Event()

    def _listen() -> None:
        bus = PostgresNotifyBus(postgres_dsn)
        for event in bus.listen(("desk.intel.output",), timeout=8.0, stop_after=1, on_listening=ready.set):
            received.append(event)
            break

    thread = threading.Thread(target=_listen, daemon=True)
    thread.start()
    assert ready.wait(timeout=5)
    notify_bus = PostgresNotifyBus(postgres_dsn)
    notify_bus.notify("desk.intel.output", env.notify_payload())
    thread.join(timeout=8)
    assert received, "expected a PG NOTIFY on desk.intel.output"
    payload = received[0].payload
    assert payload["id"] == env.envelope_id
    assert payload["content_hash"] == env.content_hash
    assert "body" not in payload
    assert "pack_markdown" not in payload


def test_killed_desk_still_assembles_from_postgres(db_session, postgres_dsn: str) -> None:
    store = PostgresEnvelopeStore(db_session)
    bus = PostgresBus(postgres_dsn)
    result = mesh_from_fixture(FIXTURE, repo_root=ROOT, killed=("research",), store=store, bus=bus)
    db_session.commit()
    by_desk = {env.desk: env for env in result.assemble.envelopes}
    assert by_desk["research"].status == FAILED
    assert by_desk["research"].error_class == "desk_killed"
    assert result.assemble.status == FAILED
    row = store.latest("research", result.as_of_knowledge)
    assert row is not None
    assert row.error_class == "desk_killed"
    health = store.repo.get_health("research")
    assert health is not None
    assert health.status == FAILED
    again = mesh_from_fixture(FIXTURE, repo_root=ROOT, killed=("research",), store=store, bus=bus)
    assert again.content_hash == result.content_hash
    count = db_session.execute(text("SELECT count(*) FROM desk_envelope WHERE desk = 'research'")).scalar_one()
    assert int(count) == 1
