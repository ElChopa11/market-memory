"""IMP-024 SEC EDGAR adapter: CBRS/SPCX lockup observations, --no-db ELIGIBLE, no flat 180d."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import httpx

from mm_common.http import ERROR_PARSE
from mm_ingest.edgar import (
    FILING_METRIC,
    LOCKUP_METRIC,
    fetch_submissions,
    lockup_is_formula,
    normalize_lockup_observation,
    pad_cik,
)
from mm_ingest.edgar_stack import CLOSURE_CLOSED, CLOSURE_ELIGIBLE, closure_for, run_edgar_stack
from mm_ingest.licence import normalize_verdict, verdict_for
from mm_ingest.pipeline import envelopes_from_fixture, load_fixture_file
from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "edgar"
LOCKUP = FIXTURES / "cbrs_spcx_lockup.json"
MISSING = FIXTURES / "missing_feed.json"
FLAT = FIXTURES / "flat_180d_refused.json"
INGESTED = datetime(2026, 9, 19, 9, 0, tzinfo=timezone.utc)
BEFORE = datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc)


def test_licence_ok_gov_is_redistributable_official() -> None:
    assert verdict_for("edgar").verdict == "ok_gov"
    assert normalize_verdict("redistributable_official") == "ok_gov"
    ingest = (ROOT / "config" / "ingest.yaml").read_text(encoding="utf-8")
    assert "licence_verdict: ok_gov" in ingest
    assert "15 U.S.C." in ingest or "78ll" in ingest


def test_cbrs_spcx_lockup_formula_not_flat_180d() -> None:
    envelopes = envelopes_from_fixture(load_fixture_file(LOCKUP))
    lockups = [e for e in envelopes if e.metric == LOCKUP_METRIC]
    filings = [e for e in envelopes if e.metric == FILING_METRIC]
    by = {e.instrument: e for e in lockups}
    assert set(by) == {"NASDAQ:CBRS", "NASDAQ:SPCX"}
    cbrs = by["NASDAQ:CBRS"]
    spcx = by["NASDAQ:SPCX"]
    assert cbrs.identity.value == "2026-11-09"
    assert spcx.identity.value == "2027-06-12"
    assert cbrs.identity.extras.get("assume_180d") == "false"
    assert spcx.identity.extras.get("assume_180d") == "false"
    assert cbrs.as_of_knowledge == cbrs.ingested_at == INGESTED
    assert spcx.as_of_knowledge == spcx.ingested_at == INGESTED
    assert cbrs.market_time is not None and cbrs.market_time.date().isoformat() == "2026-05-13"
    assert spcx.market_time is not None and spcx.market_time.date().isoformat() == "2026-06-11"
    assert cbrs.as_of_knowledge != cbrs.market_time
    assert "2021728" in cbrs.source_url_or_id
    assert "1181412" in spcx.source_url_or_id
    assert cbrs.payload.get("licence_verdict") == "ok_gov"
    assert "earlier of" in str(cbrs.payload.get("formula") or "").lower()
    assert "extension" in str(spcx.payload.get("formula") or "").lower()
    assert len(filings) == 2
    assert all(e.source_name == "edgar" for e in envelopes)


def test_file_date_is_not_knowledge_clock() -> None:
    envelopes = envelopes_from_fixture(load_fixture_file(LOCKUP))
    visible = [e for e in envelopes if e.as_of_knowledge <= BEFORE]
    assert visible == []
    known = [e for e in envelopes if e.as_of_knowledge <= INGESTED]
    assert known
    for envelope in envelopes:
        assert envelope.as_of_knowledge == envelope.ingested_at


def test_flat_180d_lockup_is_refused() -> None:
    assert lockup_is_formula(assume_180d=True, excerpt="180 days", terms="180 days") is False
    assert lockup_is_formula(assume_180d=False, excerpt="180 days after the prospectus", terms="") is False
    envelopes = envelopes_from_fixture(load_fixture_file(FLAT))
    lockups = [e for e in envelopes if e.metric == LOCKUP_METRIC]
    assert lockups
    assert all(e.payload.get("error_class") == ERROR_PARSE for e in lockups)
    assert all(e.identity.value == "unavailable" for e in lockups)


def test_missing_edgar_feed_degrades() -> None:
    envelopes = envelopes_from_fixture(load_fixture_file(MISSING))
    assert envelopes
    assert all(e.payload.get("error_class") == "http_404" for e in envelopes)
    assert all(e.identity.value == "unavailable" for e in envelopes)


def test_edgar_no_db_is_eligible_never_closed(capsys) -> None:
    assert closure_for(no_db=True, persisted=False, run_id=None) == CLOSURE_ELIGIBLE
    assert closure_for(no_db=True, persisted=True, run_id="x") == CLOSURE_ELIGIBLE
    assert closure_for(no_db=False, persisted=False, run_id=None) != CLOSURE_CLOSED
    envelopes = envelopes_from_fixture(load_fixture_file(LOCKUP))
    stack = run_edgar_stack(envelopes, no_db=True)
    assert stack.closure == CLOSURE_ELIGIBLE
    assert stack.persisted is False
    assert stack.run_id is None
    assert stack.as_public_dict()["auto_close"] is False
    cbrs = next(row for row in stack.rows if row.instrument == "NASDAQ:CBRS" and row.metric == LOCKUP_METRIC)
    assert cbrs.value == "2026-11-09"
    assert cbrs.licence_verdict == "ok_gov"
    assert cbrs.assume_180d is False
    assert "2026-11-09" in stack.markdown
    rc = main(["ingest", "--fixture", str(LOCKUP), "--no-db"])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"closure": "ELIGIBLE"' in out
    assert "edgar_stack" in out
    assert "CLOSED" not in out.split("edgar_stack")[0] or '"closure": "ELIGIBLE"' in out
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live


def test_live_submissions_uses_declared_ua_and_degrades() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["ua"] = request.headers.get("user-agent", "")
        return httpx.Response(403, text="Undeclared Automated Tool")

    client = httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)
    envelopes, error = fetch_submissions(
        "2021728",
        ingested_at=INGESTED,
        http_client=client,
        instrument="NASDAQ:CBRS",
        sleep=lambda _: None,
    )
    assert pad_cik("2021728") == "0002021728"
    assert error == "tos_or_blocked"
    assert envelopes
    assert all(e.payload.get("error_class") == "tos_or_blocked" for e in envelopes)
    assert "market-memory" in seen["ua"].lower() or "ElChopa11" in seen["ua"]


def test_live_submissions_parses_424b4() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "CIK0002021728.json" in str(request.url)
        return httpx.Response(
            200,
            json={
                "cik": "0002021728",
                "filings": {
                    "recent": {
                        "form": ["424B4", "8-K"],
                        "accessionNumber": ["0001628280-26-035214", "0001628280-26-099999"],
                        "filingDate": ["2026-05-13", "2026-09-01"],
                        "primaryDocument": ["cerebras-424b4.htm", "ex99.htm"],
                    }
                },
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)
    envelopes, error = fetch_submissions(
        "2021728",
        ingested_at=INGESTED,
        http_client=client,
        instrument="NASDAQ:CBRS",
        sleep=lambda _: None,
    )
    assert error == "none"
    forms = {e.identity.value for e in envelopes if e.metric == FILING_METRIC}
    assert "424B4" in forms
    assert "8-K" in forms


def test_normalize_lockup_requires_url_and_bound() -> None:
    envelope = normalize_lockup_observation(
        instrument="NASDAQ:CBRS",
        cik="2021728",
        lockup={
            "assume_180d": False,
            "excerpt": "earlier of earnings or 180 days",
            "fail_closed_blackout_until": "",
            "url": "",
        },
        ingested_at=INGESTED,
    )
    assert envelope.payload.get("error_class") == ERROR_PARSE
