"""Shared pytest fixtures."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

import pytest
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_WINDOW = ROOT / "tests" / "fixtures" / "hl_window.json"
TELEGRAM_LIVE_HOST = "api.telegram.org"


@pytest.fixture(scope="session")
def fixture_window() -> dict:
    return json.loads(FIXTURE_WINDOW.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _block_live_telegram(monkeypatch):
    """Pytest must never hit the live Telegram Bot API."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    import httpx

    real_send = httpx.Client.send

    def guarded(self, request, *args, **kwargs):
        host = urlparse(str(request.url)).hostname or ""
        if host == TELEGRAM_LIVE_HOST:
            raise RuntimeError(f"pytest must not hit live Telegram API: {request.url}")
        return real_send(self, request, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "send", guarded)


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
            "TRUNCATE event_base_rate, desk_health, desk_envelope, delivery_event, inbound_audit, llm_call, paper_trade, research_run, brief, skeptic_review, thesis_evidence, thesis_status_event, thesis, observation_link, observation, raw_object, source RESTART IDENTITY CASCADE"
        )
    )
    session.commit()
    try:
        yield session
        session.commit()
    finally:
        session.close()
