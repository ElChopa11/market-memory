"""Point-in-time query contract: as_of_knowledge, never published_at / market_time."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.dialects import postgresql

from mm_common.enums import DataQuality, EvidenceType, SourceKind
from mm_common.schemas import ClaimIdentity, ObservationEnvelope
from mm_memory.queries import what_did_we_know_statement
from mm_provenance.envelope import build_envelope


def test_what_did_we_know_filters_as_of_knowledge_not_published_or_market() -> None:
    ts = datetime(2026, 9, 10, tzinfo=timezone.utc)
    sql = str(
        what_did_we_know_statement(ts).compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).lower()
    where, _, _ = sql.partition("order by")
    predicate = where.split("where", 1)[1]
    assert "as_of_knowledge" in predicate
    assert "published_at" not in predicate
    assert "market_time" not in predicate
    # ingested_at is lockstep with as_of_knowledge but is not the query predicate.
    assert "ingested_at" not in predicate


def test_envelope_construction_forces_as_of_knowledge_equal_to_ingested_at() -> None:
    ingested = datetime(2026, 9, 10, 0, 5, tzinfo=timezone.utc)
    published = datetime(2026, 9, 10, 0, 0, tzinfo=timezone.utc)
    market = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
    identity = ClaimIdentity(
        source_name="hyperliquid.info",
        instrument="BTC",
        metric="funding",
        market_time=market,
        value="0.0001",
    )
    envelope = ObservationEnvelope(
        source_name="hyperliquid.info",
        source_kind=SourceKind.EXCHANGE,
        source_url_or_id="fundingHistory:BTC",
        published_at=published,
        ingested_at=ingested,
        market_time=market,
        claim_text="x",
        confidence=0.9,
        evidence_type=EvidenceType.METRIC,
        data_quality=DataQuality.OK,
        payload={},
        as_of_knowledge=published,
        instrument="BTC",
        metric="funding",
        identity=identity,
    )
    assert envelope.as_of_knowledge == ingested
    assert envelope.as_of_knowledge != envelope.published_at
    assert envelope.as_of_knowledge != envelope.market_time


def test_build_envelope_knowledge_watermark_is_ingested_at() -> None:
    ingested = datetime(2026, 9, 10, 0, 5, tzinfo=timezone.utc)
    published = datetime(2026, 9, 9, 23, 0, tzinfo=timezone.utc)
    market = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
    envelope = build_envelope(
        source_name="hyperliquid.info",
        source_kind=SourceKind.EXCHANGE,
        source_url_or_id="fundingHistory:BTC",
        instrument="BTC",
        metric="funding",
        value="0.0001",
        published_at=published,
        ingested_at=ingested,
        market_time=market,
        payload={"hl_type": "fundingHistory"},
        historical=True,
    )
    assert envelope.as_of_knowledge == ingested
    assert envelope.published_at == published
    assert envelope.market_time == market
