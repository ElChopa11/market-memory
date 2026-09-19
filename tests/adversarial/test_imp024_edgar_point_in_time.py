"""Adversarial PIT: EDGAR file_date is not the knowledge clock."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from mm_ingest.pipeline import envelopes_from_fixture, load_fixture_file

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "edgar" / "cbrs_spcx_lockup.json"
BEFORE = datetime(2026, 5, 14, 0, 0, tzinfo=timezone.utc)
AT_INGEST = datetime(2026, 9, 19, 9, 0, tzinfo=timezone.utc)


def test_edgar_lockup_hidden_until_ingested() -> None:
    envelopes = envelopes_from_fixture(load_fixture_file(FIXTURE))
    assert envelopes
    for envelope in envelopes:
        assert envelope.as_of_knowledge == envelope.ingested_at
        if envelope.market_time is not None:
            assert envelope.market_time != envelope.as_of_knowledge
    leaked_if_file_date = [
        e for e in envelopes if e.market_time is not None and e.market_time <= BEFORE
    ]
    assert leaked_if_file_date, "fixture must include a 424B4 whose file_date is before ingest"
    assert [e for e in envelopes if e.as_of_knowledge <= BEFORE] == []
    known = [e for e in envelopes if e.as_of_knowledge <= AT_INGEST]
    assert {e.instrument for e in known} >= {"NASDAQ:CBRS", "NASDAQ:SPCX"}
