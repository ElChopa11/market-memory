"""A second history-backfill run does not duplicate an unchanged claim."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from mm_common.enums import EvidenceType, SourceKind
from mm_ingest.history_backfill import persist_history_envelopes
from mm_memory.models import Observation, ObservationLink, RawObject
from mm_memory.object_store import InMemoryObjectStore
from mm_provenance.envelope import build_envelope

MARKET = datetime(2026, 9, 1, tzinfo=timezone.utc)
INGESTED = datetime(2026, 9, 23, 1, 0, tzinfo=timezone.utc)


def _bar(value: str, ingested_at: datetime):
    return build_envelope(
        source_name="polygon",
        source_kind=SourceKind.EXCHANGE,
        source_url_or_id=f"aggs:SPY:day:1:{int(MARKET.timestamp())}",
        instrument="SPY",
        metric="ohlcv_close",
        value=value,
        published_at=MARKET,
        ingested_at=ingested_at,
        market_time=MARKET,
        payload={"raw": {"c": value}},
        extras={"timespan": "day", "multiplier": "1"},
        historical=True,
        venue="equity",
        evidence_type=EvidenceType.METRIC,
    )


def test_repeat_claim_is_not_a_second_row_or_raw_object(db_session) -> None:
    store = InMemoryObjectStore()
    first = persist_history_envelopes(db_session, [_bar("510.25", INGESTED)], object_store=store)
    db_session.flush()
    assert first.created == 1
    assert first.duplicates == 0
    raw_rows = db_session.scalar(select(func.count()).select_from(RawObject))
    object_keys = set(store.objects)
    assert raw_rows == 1
    assert object_keys

    later = INGESTED + timedelta(days=1)
    again = _bar("510.25", later)
    original = _bar("510.25", INGESTED)
    assert again.claim_hash == original.claim_hash
    second = persist_history_envelopes(db_session, [again], object_store=store)
    db_session.flush()
    assert second.created == 0
    assert second.duplicates == 1
    assert db_session.scalar(select(func.count()).select_from(Observation)) == 1
    assert db_session.scalar(select(func.count()).select_from(RawObject)) == raw_rows
    assert set(store.objects) == object_keys

    revised = persist_history_envelopes(db_session, [_bar("511.00", later)], object_store=store)
    db_session.flush()
    assert revised.created == 1
    assert db_session.scalar(select(func.count()).select_from(Observation)) == 2
    links = list(db_session.scalars(select(ObservationLink)).all())
    assert links
    assert {link.relation for link in links} == {"contradicts"}
