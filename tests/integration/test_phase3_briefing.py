"""Phase 3 briefing: fixture generate + optional DB index; HL from Market Memory."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import inspect

from mm_briefing.config import load_briefing_settings
from mm_briefing.engine import generate_from_fixture, generate_preopen, load_fixture_file
from mm_briefing.fetchers import snapshot_from_payload
from mm_briefing.hl import hl_from_memory
from mm_briefing.store import index_brief, write_brief
from mm_ingest.pipeline import ingest_from_fixture
from mm_memory.brief_repository import BriefRepository
from mm_memory.db import make_engine
from mm_memory.migrate import current_revision
from mm_memory.models import Brief

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "tests" / "fixtures" / "briefing" / "frozen_day.json"
HL_WINDOW = ROOT / "tests" / "fixtures" / "hl_window.json"


def test_brief_table_migrated(postgres_dsn: str) -> None:
    engine = make_engine(postgres_dsn)
    tables = set(inspect(engine).get_table_names())
    assert "brief" in tables
    assert current_revision(postgres_dsn) == "0003_phase3"


def test_frozen_brief_indexes_in_memory(db_session, tmp_path: Path) -> None:
    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(FROZEN)
    doc, _ = generate_from_fixture("preopen", fixture, settings=settings)
    assert doc is not None
    path = write_brief(doc, root=tmp_path)
    brief_id = index_brief(db_session, doc, artifact_path=path, root=tmp_path)
    db_session.commit()
    row = db_session.get(Brief, brief_id)
    assert row is not None
    assert row.kind == "preopen"
    assert row.session_date.isoformat() == "2026-03-10"
    assert row.content_hash == doc.content_hash
    listed = BriefRepository(db_session).list_for_session(doc.session_date, kind="preopen")
    assert len(listed) == 1


def test_preopen_uses_memory_observations(db_session, fixture_window: dict) -> None:
    ingest_from_fixture(db_session, fixture_window)
    db_session.commit()
    as_of = datetime(2026, 9, 10, 12, 5, tzinfo=timezone.utc)
    hl = hl_from_memory(db_session, as_of)
    by_inst = {row.instrument: row for row in hl}
    assert "BTC" in by_inst
    funding = by_inst["BTC"].metric("funding")
    assert funding is not None
    assert funding.observation_id
    settings = load_briefing_settings(ROOT)
    frozen = load_fixture_file(FROZEN)
    macro = snapshot_from_payload(
        frozen["macro"],
        as_of=as_of,
        prior_us_close=datetime(2026, 9, 9, 20, 0, tzinfo=timezone.utc),
        source="fixture",
    )
    doc = generate_preopen(as_of=as_of, settings=settings, macro=macro, hl=hl, generated_at=as_of)
    assert funding.observation_id in doc.markdown
    assert "Hyperliquid" in doc.markdown
    assert doc.session_date.isoformat() == "2026-09-10"
