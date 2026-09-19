"""IMP-024 Postgres persist path for EDGAR lockup observations."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from mm_ingest.edgar import LOCKUP_METRIC
from mm_ingest.edgar_stack import CLOSURE_ELIGIBLE, run_edgar_stack
from mm_ingest.pipeline import envelopes_from_fixture, load_fixture_file
from mm_memory.models import Observation

ROOT = Path(__file__).resolve().parents[2]
LOCKUP = ROOT / "tests" / "fixtures" / "edgar" / "cbrs_spcx_lockup.json"


def test_edgar_lockup_persists_with_as_of_knowledge(db_session) -> None:
    envelopes = envelopes_from_fixture(load_fixture_file(LOCKUP))
    stack = run_edgar_stack(envelopes, no_db=False, session=db_session)
    db_session.commit()
    assert stack.closure == CLOSURE_ELIGIBLE
    assert stack.persisted is True
    assert stack.run_id
    assert stack.as_public_dict()["auto_close"] is False
    rows = list(
        db_session.scalars(select(Observation).where(Observation.metric == LOCKUP_METRIC)).all()
    )
    by = {row.instrument: row for row in rows}
    assert "NASDAQ:CBRS" in by
    assert "NASDAQ:SPCX" in by
    cbrs = by["NASDAQ:CBRS"]
    assert cbrs.as_of_knowledge == cbrs.ingested_at
    assert cbrs.source_url_or_id and "2021728" in (cbrs.source_url_or_id or "")
    assert cbrs.claim_hash
    assert "2026-11-09" in cbrs.claim_text
    payload = cbrs.payload_json or {}
    assert payload.get("assume_180d") is False
    assert payload.get("fail_closed_blackout_until") == "2026-11-09"
