"""IMP-024 SEC EDGAR adapter: stored 424B4 lockups, PIT, 403, 8-K 2.02."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from mm_common.enums import DataQuality
from mm_common.http import ERROR_PARSE, ERROR_TOS_OR_BLOCKED
from mm_ingest.config import load_ingest_settings
from mm_ingest.edgar import (
    FORBIDDEN_HOSTS,
    METRIC_EARNINGS,
    METRIC_FILING,
    METRIC_LOCKUP,
    assert_allowed_url,
    declared_user_agent,
    extract_lockup_facts,
    fetch_filing,
    filing_observation_id,
    load_lockup_targets,
    pull_lockup_targets,
)
from mm_ingest.edgar_stack import CLOSURE_ELIGIBLE, run_edgar_stack
from mm_ingest.licence import assert_licence_invariants, may_publish_value, verdict_for
from mm_ingest.pipeline import envelopes_from_fixture, load_fixture_file
from mm_ingest.rate_limit import RpsLimiter
from mm_ingest.sources import EDGAR_SOURCE_NAME
from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "edgar"
LOCKUP_FIXTURE = FIXTURES / "cbrs-spcx-lockup.json"
UNAVAILABLE = FIXTURES / "unavailable.json"
EXPECTED = json.loads((FIXTURES / "expected_lockups.json").read_text(encoding="utf-8"))
INGESTED = datetime.fromisoformat("2026-09-19T09:56:30+10:00")


def test_licence_and_user_agent() -> None:
    assert_licence_invariants()
    assert verdict_for("edgar").verdict == "ok_gov"
    assert may_publish_value("edgar") is True
    ua = declared_user_agent()
    assert "MarketMemory" in ua
    assert ua.strip()
    settings = load_ingest_settings()
    assert settings["rate_limits"]["edgar"]["max_requests_per_second"] == 10
    assert settings["adapters"]["edgar"]["licence_verdict"] == "ok_gov"
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live


def test_watchlist_lockup_targets_cbrs_spcx() -> None:
    targets = {row.instrument: row for row in load_lockup_targets()}
    assert set(targets) >= {"CBRS", "SPCX"}
    assert targets["CBRS"].cik == "2021728"
    assert targets["SPCX"].cik == "1181412"
    assert "424" in targets["CBRS"].form.upper()
    assert "sec.gov" in targets["CBRS"].url
    assert assert_allowed_url(targets["CBRS"].url) is None
    assert assert_allowed_url("https://api.nasdaq.com/api/ipo/calendar") == ERROR_TOS_OR_BLOCKED
    assert assert_allowed_url("https://feeds.finance.yahoo.com/rss/2.0/headline") == ERROR_TOS_OR_BLOCKED
    src = (ROOT / "packages" / "ingest" / "src" / "mm_ingest" / "edgar.py").read_text(encoding="utf-8")
    assert "api.nasdaq.com" in src
    assert "FORBIDDEN_HOSTS" in src
    for host in FORBIDDEN_HOSTS:
        assert host in src


def test_lockup_facts_from_stored_424b4_match_intel_golden() -> None:
    for symbol, gold in EXPECTED.items():
        html = (FIXTURES / f"{symbol.lower()}-424b4-shares-eligible.html").read_text(encoding="utf-8")
        facts = extract_lockup_facts(html)
        assert facts.found is True
        assert facts.assume_180d is False
        assert facts.section
        assert facts.prospectus_dated == gold["prospectus_dated"]
        assert facts.delivery_expected == gold["delivery_expected"]
        staged = set(facts.staged_calendar_dates)
        for day in gold["must_include_dates"]:
            assert day in staged or day == facts.prospectus_dated, (symbol, day, staged)
        blob = " ".join(
            [
                facts.lock_up_period or "",
                facts.first_earnings_release_date or "",
                facts.excerpt,
            ]
        )
        for needle in gold["lock_up_period_needles"]:
            assert needle.lower() in blob.lower(), (symbol, needle)


def test_fixture_envelopes_pit_and_observation_ids() -> None:
    fixture = load_fixture_file(LOCKUP_FIXTURE)
    envelopes = envelopes_from_fixture(fixture)
    assert envelopes
    assert all(e.source_name == EDGAR_SOURCE_NAME for e in envelopes)
    assert all(e.as_of_knowledge == e.ingested_at for e in envelopes)
    lockups = {e.instrument: e for e in envelopes if e.metric == METRIC_LOCKUP}
    filings = {e.instrument: e for e in envelopes if e.metric == METRIC_FILING and e.instrument in {"CBRS", "SPCX"}}
    assert set(lockups) == {"CBRS", "SPCX"}
    for symbol, gold in EXPECTED.items():
        row = lockups[symbol]
        assert row.payload.get("observation_id") == gold["observation_id"]
        assert row.source_url_or_id == gold["observation_id"]
        assert filing_observation_id(symbol, gold["form"], gold["file_date"]) == gold["observation_id"]
        assert row.payload.get("file_date") == gold["file_date"]
        assert row.payload.get("assume_180d") is False
        assert row.as_of_knowledge == INGESTED
        assert row.ingested_at == INGESTED
        assert row.published_at.date().isoformat() == gold["file_date"]
        assert row.as_of_knowledge != row.published_at
        assert row.payload.get("file_date") != row.as_of_knowledge.date().isoformat()
        assert row.claim_hash
        assert "0" not in {row.payload.get("file_date"), row.identity.value} or row.identity.value == gold["observation_id"]
        staged = set(row.payload.get("staged_calendar_dates") or [])
        for day in gold["must_include_dates"]:
            assert day in staged
        filing = filings[symbol]
        assert filing.payload.get("filing_content_hash")
        assert filing.payload.get("raw", {}).get("html")
    earnings = [e for e in envelopes if e.metric == METRIC_EARNINGS]
    assert earnings
    assert earnings[0].identity.value == "item_2.02"
    assert earnings[0].payload.get("estimates") is None
    assert earnings[0].payload.get("item") == "2.02"


def test_missing_and_403_are_unavailable_never_invented() -> None:
    empty = extract_lockup_facts("")
    assert empty.found is False
    assert empty.error_class == ERROR_PARSE
    fixture = load_fixture_file(UNAVAILABLE)
    envelopes = envelopes_from_fixture(fixture)
    assert envelopes
    assert all(e.payload.get("error_class") == ERROR_TOS_OR_BLOCKED for e in envelopes)
    assert all(e.identity.value == "unavailable" for e in envelopes)
    assert all(e.data_quality is DataQuality.PARTIAL for e in envelopes)

    calls = {"n": 0, "ua": ""}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        calls["ua"] = request.headers.get("User-Agent", "")
        return httpx.Response(403, text="Your request has been blocked")

    client = httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)
    fetched = fetch_filing(
        "https://www.sec.gov/Archives/edgar/data/2021728/000162828026035214/cerebras-424b4.htm",
        http_client=client,
        sleep=lambda _: None,
    )
    assert fetched.ok is False
    assert fetched.error_class == ERROR_TOS_OR_BLOCKED
    assert fetched.html == ""
    assert "MarketMemory" in calls["ua"]

    refused = fetch_filing("https://api.nasdaq.com/api/ipo/calendar", sleep=lambda _: None)
    assert refused.ok is False
    assert refused.error_class == ERROR_TOS_OR_BLOCKED
    assert refused.html == ""


def test_live_403_lockup_pull_degrades() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="blocked")

    client = httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)
    envelopes = pull_lockup_targets(
        ingested_at=INGESTED,
        http_client=client,
        sleep=lambda _: None,
    )
    assert envelopes
    assert all(e.payload.get("error_class") == ERROR_TOS_OR_BLOCKED for e in envelopes)
    assert all(e.identity.value == "unavailable" for e in envelopes)
    assert not any((e.payload.get("lock_up_period") or e.payload.get("html")) for e in envelopes)


def test_rps_limiter_caps_at_ten() -> None:
    slept: list[float] = []
    clock = {"t": 0.0}

    def now() -> float:
        return clock["t"]

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        clock["t"] += seconds

    limiter = RpsLimiter(name="edgar", max_rps=10.0)
    limiter.wait(sleep, now=now)
    clock["t"] += 0.01
    waited = limiter.wait(sleep, now=now)
    assert waited >= 0.09
    assert slept
    assert slept[0] >= 0.09


def test_lab_ingest_and_data_edgar_no_db(capsys) -> None:
    fixture = load_fixture_file(LOCKUP_FIXTURE)
    envelopes = envelopes_from_fixture(fixture)
    stack = run_edgar_stack(envelopes, no_db=True)
    assert stack.closure == CLOSURE_ELIGIBLE
    assert stack.persisted is False
    assert stack.run_id is None
    assert stack.as_public_dict()["auto_close"] is False
    by_id = {row.observation_id: row for row in stack.rows if row.metric == METRIC_LOCKUP}
    assert "edgar-CBRS-424b4-20260513" in by_id
    assert "edgar-SPCX-424b4-20260611" in by_id
    assert by_id["edgar-CBRS-424b4-20260513"].assume_180d is False
    assert by_id["edgar-CBRS-424b4-20260513"].claim_hash
    assert by_id["edgar-SPCX-424b4-20260611"].file_date == "2026-06-11"
    rc = main(["ingest", "--fixture", str(LOCKUP_FIXTURE), "--no-db"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ELIGIBLE" in out
    assert "edgar-CBRS-424b4-20260513" in out
    assert "edgar-SPCX-424b4-20260611" in out
    rc = main(["data", "edgar", "--fixture", str(LOCKUP_FIXTURE), "--no-db"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "edgar-CBRS-424b4-20260513" in out
    assert '"closure": "ELIGIBLE"' in out
