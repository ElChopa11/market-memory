"""Integration: migrate, fixture ingest, claim_hash dedupe, quality flags, PIT replay."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, inspect, select

from mm_common.enums import DataQuality, ObservationRelation
from mm_ingest.pipeline import ingest_from_fixture
from mm_memory.db import make_engine
from mm_memory.migrate import current_revision
from mm_memory.models import Observation, ObservationLink, RawObject, Source
from mm_memory.object_store import InMemoryObjectStore
from mm_memory.queries import what_did_we_know
from mm_provenance.normalize import normalize_all_mids

ROOT = Path(__file__).resolve().parents[2]
WINDOW_START = datetime(2026, 9, 9, 0, 0, tzinfo=timezone.utc)
BEFORE_SNAPSHOT = datetime(2026, 9, 10, 0, 0, tzinfo=timezone.utc)
AFTER_SNAPSHOT = datetime(2026, 9, 10, 0, 5, tzinfo=timezone.utc)
MIDDAY = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)


def test_migrate_creates_core_tables(postgres_dsn: str) -> None:
    engine = make_engine(postgres_dsn)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {
        "source",
        "observation",
        "observation_link",
        "raw_object",
        "thesis",
        "thesis_evidence",
        "skeptic_review",
        "brief",
    } <= tables
    assert current_revision(postgres_dsn) == "0004_phase4"
    columns = {col["name"] for col in inspector.get_columns("observation")}
    assert "ingested_at" in columns
    assert "published_at" in columns
    assert "claim_hash" in columns
    assert "identity_hash" in columns
    assert "raw_object_checksum" in columns


def test_fixture_ingest_dedupe_quality_and_pit(db_session, fixture_window: dict) -> None:
    store = InMemoryObjectStore()
    stats = ingest_from_fixture(db_session, fixture_window, object_store=store)
    db_session.commit()

    assert stats.created >= 1
    assert stats.duplicates >= 1
    assert "BTC" in stats.instruments and "ETH" in stats.instruments

    sources = list(db_session.scalars(select(Source)).all())
    assert len(sources) == 1
    assert sources[0].name == "hyperliquid.info"

    funding_hashes = list(
        db_session.scalars(
            select(Observation.claim_hash).where(
                Observation.instrument == "BTC",
                Observation.metric == "funding",
                Observation.market_time == WINDOW_START,
            )
        ).all()
    )
    assert len(funding_hashes) == 1

    eth_oi = db_session.scalar(
        select(Observation).where(Observation.instrument == "ETH", Observation.metric == "open_interest")
    )
    assert eth_oi is not None
    assert eth_oi.data_quality == DataQuality.PARTIAL.value

    stale_mids = list(
        db_session.scalars(
            select(Observation).where(
                Observation.metric == "mid_px",
                Observation.data_quality == DataQuality.STALE.value,
            )
        ).all()
    )
    assert stale_mids

    known_before_snapshot = what_did_we_know(db_session, BEFORE_SNAPSHOT)
    known_after_snapshot = what_did_we_know(db_session, AFTER_SNAPSHOT)
    known_midday = what_did_we_know(db_session, MIDDAY)

    before_metrics = {(row.instrument, row.metric) for row in known_before_snapshot}
    after_metrics = {(row.instrument, row.metric) for row in known_after_snapshot}
    midday_metrics = {(row.instrument, row.metric) for row in known_midday}

    assert ("BTC", "mid_px") not in before_metrics
    assert ("BTC", "mid_px") in after_metrics
    assert ("BTC", "funding") in before_metrics
    assert ("BTC", "liquidation") in midday_metrics
    assert ("BTC", "candle_close") in midday_metrics
    assert len(known_after_snapshot) >= len(known_before_snapshot)

    raw_rows = list(db_session.scalars(select(RawObject)).all())
    assert raw_rows
    assert all(len(row.checksum_sha256) == 64 for row in raw_rows)
    assert store.objects

    # Re-ingest the same fixture: duplicates collapse, row count unchanged.
    first_count = db_session.scalar(select(func.count()).select_from(Observation))
    again = ingest_from_fixture(db_session, fixture_window, object_store=store)
    db_session.commit()
    second_count = db_session.scalar(select(func.count()).select_from(Observation))
    assert again.created == 0
    assert again.duplicates >= 1
    assert first_count == second_count


def test_contradictory_mids_are_linked(db_session) -> None:
    t = datetime(2026, 9, 11, tzinfo=timezone.utc)
    first = normalize_all_mids({"BTC": "1.0", "ETH": "2.0"}, instruments=["BTC"], ingested_at=t, published_at=t)
    second = normalize_all_mids({"BTC": "1.5", "ETH": "2.0"}, instruments=["BTC"], ingested_at=t, published_at=t)
    ingest_from_fixture(
        db_session,
        {
            "instruments": ["BTC"],
            "snapshot_published_at": t.isoformat(),
            "snapshot_ingested_at": t.isoformat(),
            "allMids": {"BTC": "1.0"},
        },
    )
    ingest_from_fixture(
        db_session,
        {
            "instruments": ["BTC"],
            "snapshot_published_at": t.isoformat(),
            "snapshot_ingested_at": t.isoformat(),
            "allMids": {"BTC": "1.5"},
        },
    )
    db_session.commit()
    rows = list(db_session.scalars(select(Observation).where(Observation.metric == "mid_px")).all())
    assert len(rows) == 2
    assert {row.data_quality for row in rows} == {DataQuality.CONTRADICTED.value}
    links = list(db_session.scalars(select(ObservationLink)).all())
    assert any(link.relation == ObservationRelation.CONTRADICTS.value for link in links)
    assert first[0].claim_hash != second[0].claim_hash


def test_fixture_file_exists() -> None:
    assert (ROOT / "tests" / "fixtures" / "hl_window.json").is_file()
