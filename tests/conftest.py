"""Shared pytest fixtures."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_WINDOW = ROOT / "tests" / "fixtures" / "hl_window.json"


@pytest.fixture(scope="session")
def fixture_window() -> dict:
    return json.loads(FIXTURE_WINDOW.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def postgres_dsn() -> str:
    dsn = os.environ.get("POSTGRES_DSN", "postgresql://lab:lab@localhost:5432/market_memory")
    from mm_memory.db import make_engine
    from mm_memory.migrate import upgrade_head

    engine = make_engine(dsn)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"Postgres is not available for integration tests: {exc}")
    upgrade_head(dsn)
    return dsn


@pytest.fixture
def db_session(postgres_dsn: str):
    from mm_memory.db import make_engine, make_session_factory

    engine = make_engine(postgres_dsn)
    factory = make_session_factory(engine)
    session = factory()
    session.execute(
        text(
            "TRUNCATE brief, skeptic_review, thesis_evidence, thesis, observation_link, observation, raw_object, source RESTART IDENTITY CASCADE"
        )
    )
    session.commit()
    try:
        yield session
        session.commit()
    finally:
        session.close()
