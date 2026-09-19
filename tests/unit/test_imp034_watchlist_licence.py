"""IMP-034 ticker resolutions + licence_verdict + FRED --no-db ELIGIBLE."""

from __future__ import annotations

from pathlib import Path

from mm_desks.monitor import UNRESOLVED_TICKERS, assert_monitor_invariants, monitor_names
from mm_ingest.fred_stack import CLOSURE_CLOSED, CLOSURE_ELIGIBLE, closure_for, run_fred_stack
from mm_ingest.licence import (
    STANDING_RULE,
    assert_licence_invariants,
    filter_published_values,
    may_publish_value,
    verdict_for,
)
from mm_ingest.pipeline import envelopes_from_fixture, load_fixture_file
from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
FRED_FIXTURE = ROOT / "tests" / "fixtures" / "phase5b" / "fred_series.json"


def test_principal_krx_resolutions_and_kept_ids() -> None:
    assert_monitor_invariants(ROOT)
    assert UNRESOLVED_TICKERS == ()
    by = {row.ticker: row for row in monitor_names(ROOT)}
    assert by["SAMSUN"].qualified_id == "KRX:005930"
    assert by["SAMSUN"].venue == "krx"
    assert by["SAMSUN"].cluster == "semis_ai"
    assert by["KOSDA"].qualified_id == "KRX:KQ11"
    assert by["KOSDA"].venue == "krx"
    assert by["KOSDA"].cluster == "index_futures"
    assert by["CHIPIUSD"].qualified_id == "HL:CHIP"
    assert by["VVVUSD"].qualified_id == "HL:VVV"
    assert by["PURR"].qualified_id == "HL:PURR"
    assert by["SPCX"].qualified_id == "NASDAQ:SPCX"
    assert by["CBRS"].qualified_id == "NASDAQ:CBRS"
    spec = (ROOT / "config" / "watchlist" / "monitor.yaml").read_text(encoding="utf-8")
    assert "Samsung Electronics" in spec
    assert "KOSDAQ Composite" in spec
    assert "unresolved: []" in spec


def test_licence_verdict_schema_and_standing_rule() -> None:
    assert_licence_invariants()
    assert "prohibit redistribution" in STANDING_RULE.lower()
    assert verdict_for("fred").verdict == "ok_gov"
    assert may_publish_value("fred") is True
    assert verdict_for("yahoo").verdict == "prohibited"
    assert may_publish_value("yahoo") is False
    assert verdict_for("finnhub").verdict == "pending_terms"
    assert may_publish_value("finnhub") is False
    assert verdict_for("coingecko").verdict == "restricted"
    assert may_publish_value("coingecko") is False
    assert verdict_for("edgar").verdict == "ok_gov"
    assert verdict_for("treasury").verdict == "ok_gov"
    assert verdict_for("tiingo").verdict == "restricted"
    ingest = (ROOT / "config" / "ingest.yaml").read_text(encoding="utf-8")
    assert "licence_verdict: ok_gov" in ingest
    assert "licence_verdict: prohibited" in ingest
    published = filter_published_values(
        [
            {"source": "fred", "value": "4.21"},
            {"source": "yahoo", "value": "1.23"},
            {"source": "coingecko", "value": "65000"},
        ]
    )
    by = {row["source"]: row for row in published}
    assert by["fred"]["value"] == "4.21"
    assert by["fred"]["value_redacted"] is False
    assert by["yahoo"]["value"] is None
    assert by["yahoo"]["value_redacted"] is True
    assert by["coingecko"]["value"] is None


def test_fred_no_db_is_eligible_never_closed(capsys) -> None:
    assert closure_for(no_db=True, persisted=False, run_id=None) == CLOSURE_ELIGIBLE
    assert closure_for(no_db=True, persisted=True, run_id="x") == CLOSURE_ELIGIBLE
    assert closure_for(no_db=False, persisted=False, run_id=None) != CLOSURE_CLOSED
    fixture = load_fixture_file(FRED_FIXTURE)
    envelopes = envelopes_from_fixture(fixture)
    stack = run_fred_stack(envelopes, no_db=True)
    assert stack.closure == CLOSURE_ELIGIBLE
    assert stack.persisted is False
    assert stack.run_id is None
    assert stack.as_public_dict()["auto_close"] is False
    us10y = next(row for row in stack.rows if row.instrument == "US10Y")
    assert us10y.value == "4.21"
    assert us10y.provenance_id
    assert us10y.licence_verdict == "ok_gov"
    assert "4.21" in stack.markdown
    rc = main(["ingest", "--fixture", str(FRED_FIXTURE), "--no-db"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ELIGIBLE" in out
    assert "CLOSED" not in out.split("fred_stack")[0] or '"closure": "ELIGIBLE"' in out
    assert "4.21" in out
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
