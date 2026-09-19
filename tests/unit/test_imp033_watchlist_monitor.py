"""IMP-033: Principal-locked monitor.yaml review list, resolution, lockups, scan."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from mm_desks.monitor import (
    UNRESOLVED_TICKERS,
    UNSIZED_REASON,
    assert_monitor_invariants,
    idea_eligible,
    lockup_inside_horizon,
    monitor_names,
    monitor_tickers,
    name_by_ticker,
    net_sized_ideas,
    sma200_display,
    watchlist_tier_for,
)
from mm_desks.universe import locked_instruments
from mm_desks.watchlist import run_watchlist_from_fixture
from mm_research_kit.quant_review.language import language_violations

ROOT = Path(__file__).resolve().parents[2]
LOCKED = ROOT / "tests" / "fixtures" / "phase6c4" / "locked_scan.json"
AS_OF = datetime(2026, 9, 19, tzinfo=timezone.utc)

CRYPTO = (
    "BTCUSD",
    "ETHUSD",
    "SOLUSD",
    "HYPEUSD",
    "NEARUSD",
    "ARBUSD",
    "UNIUSD",
    "VVVUSD",
    "ZECUSD",
    "XMRUSD",
    "LTCUSD",
    "CASHCAT",
    "PONSUSD",
    "CHIPIUSD",
    "DOGEUSD",
)
BASE = (
    "SPX",
    "NQ1!",
    "QQQ",
    "CL1!",
    "CRCL",
    "TSLA",
    "SPCX",
    "NVDA",
    "SAMSUN",
    "BB",
    "GLXY",
    "IBIT",
    "BMNR",
    "PURR",
    "MRNA",
    "BTC1!",
    "KOSDA",
    "GOOG",
    "HOOD",
    "NOW",
    "CBRS",
    "MSTR",
    "STRC",
    "AMD",
)


def test_monitor_yaml_is_the_complete_review_list() -> None:
    assert_monitor_invariants(ROOT)
    tickers = monitor_tickers(ROOT)
    assert tickers == CRYPTO + BASE
    assert len(tickers) == 39
    by = {row.ticker: row for row in monitor_names(ROOT)}
    assert by["BTCUSD"].tier == "universe"
    assert by["BTCUSD"].membership == "in_universe"
    assert by["NVDA"].tier == "universe"
    assert by["NVDA"].membership == "in_universe"
    assert by["ETHUSD"].tier == "monitor"
    assert by["ETHUSD"].membership == "watch_only"
    assert by["CASHCAT"].tier == "blocked"
    assert by["PONSUSD"].tier == "blocked"
    for name in ("HYPEUSD", "SOLUSD", "NEARUSD", "ARBUSD"):
        assert by[name].tier == "monitor"
        assert by[name].archive is True
        assert by[name].membership == "deferred_must_cut"


def test_universe_yaml_not_promoted() -> None:
    locked = locked_instruments(ROOT)
    assert locked == (
        "BTC",
        "ETH",
        "UNI",
        "AAVE",
        "NVDA",
        "AVGO",
        "SMH",
        "MSFT",
        "META",
        "JPM",
        "XLF",
        "XOM",
    )
    assert "CBRS" not in locked
    assert "SPCX" not in locked
    assert "DOGE" not in locked


def test_resolution_hl_and_nasdaq_and_unresolved() -> None:
    by = {row.ticker: row for row in monitor_names(ROOT)}
    spec_text = (ROOT / "config" / "watchlist" / "monitor.yaml").read_text(encoding="utf-8")
    assert by["VVVUSD"].qualified_id == "HL:VVV"
    assert "coin VVV present on HL" in spec_text
    assert by["PURR"].qualified_id == "HL:PURR"
    assert "HL:PURR" in spec_text and "kind: perp" in spec_text
    assert by["CHIPIUSD"].qualified_id == "HL:CHIP"
    assert "CHIPIUSD display → HL:CHIP" in spec_text
    assert "Do not invent a CHIPI listing" in spec_text
    assert "qualified_id: HL:CHIPI" not in spec_text
    assert by["SPCX"].qualified_id == "NASDAQ:SPCX"
    assert by["SPCX"].cluster == "idio"
    assert by["CBRS"].qualified_id == "NASDAQ:CBRS"
    assert by["CBRS"].cluster == "semis_ai"
    assert by["CBRS"].new_listing is True
    assert UNRESOLVED_TICKERS == ()
    assert by["SAMSUN"].resolution_status == "resolved"
    assert by["SAMSUN"].qualified_id == "KRX:005930"
    assert by["KOSDA"].resolution_status == "resolved"
    assert by["KOSDA"].qualified_id == "KRX:KQ11"


def test_lockup_confirmed_not_flat_180d() -> None:
    text = (ROOT / "config" / "watchlist" / "monitor.yaml").read_text(encoding="utf-8")
    assert "assume_180d: false" in text
    assert "2021728" in text
    assert "1181412" in text
    assert "cerebras-424b4.htm" in text
    assert "spaceexplorationtechnologi.htm" in text
    assert lockup_inside_horizon("CBRS", AS_OF, ROOT) is True
    assert lockup_inside_horizon("SPCX", AS_OF, ROOT) is True
    later = datetime(2027, 6, 13, tzinfo=timezone.utc)
    assert lockup_inside_horizon("CBRS", later, ROOT) is False
    assert lockup_inside_horizon("SPCX", later, ROOT) is False


def test_sma200_never_question_or_substitute() -> None:
    assert sma200_display(None) == "n/a (insufficient history: unavailable bars)"
    assert sma200_display(0) == "n/a (insufficient history: 0 bars)"
    assert sma200_display(127) == "n/a (insufficient history: 127 bars)"
    assert "?" not in sma200_display(50)
    assert "SMA50" not in sma200_display(50)
    assert sma200_display(200).startswith("available")


def test_ideas_exclude_unresolved_blocked_new_listing() -> None:
    samsun = name_by_ticker("SAMSUN", ROOT)
    cashcat = name_by_ticker("CASHCAT", ROOT)
    cbrs = name_by_ticker("CBRS", ROOT)
    btc = name_by_ticker("BTCUSD", ROOT)
    eth = name_by_ticker("ETHUSD", ROOT)
    ok_kr, reason_kr = idea_eligible(samsun, as_of=AS_OF, repo_root=ROOT)  # type: ignore[arg-type]
    assert ok_kr is True
    assert reason_kr == UNSIZED_REASON
    assert cashcat is not None and idea_eligible(cashcat, as_of=AS_OF, repo_root=ROOT)[0] is False
    assert cbrs is not None and idea_eligible(cbrs, as_of=AS_OF, repo_root=ROOT)[0] is False
    ok, reason = idea_eligible(btc, as_of=AS_OF, repo_root=ROOT)  # type: ignore[arg-type]
    assert ok is True
    ok_eth, reason_eth = idea_eligible(eth, as_of=AS_OF, repo_root=ROOT)  # type: ignore[arg-type]
    assert ok_eth is True
    assert reason_eth == UNSIZED_REASON
    assert watchlist_tier_for("BTC", ROOT) == "universe"
    assert watchlist_tier_for("ETHUSD", ROOT) == "monitor"


def test_cluster_netting_caps() -> None:
    ideas = (
        {"instrument": "BTCUSD"},
        {"instrument": "NVDA"},
        {"instrument": "AMD"},
        {"instrument": "DOGEUSD"},
        {"instrument": "SAMSUN"},
        {"instrument": "CASHCAT"},
    )
    netted = net_sized_ideas(ideas, repo_root=ROOT, as_of=AS_OF, corr=None)
    by = {row["ticker"]: row for row in netted}
    assert by["SAMSUN"]["size_policy"] == "UNSIZED"
    assert by["SAMSUN"]["reason"] == UNSIZED_REASON
    assert "CASHCAT" not in by
    assert by["BTCUSD"]["size_policy"] == "cluster_capped"
    assert by["NVDA"]["size_policy"] == "cluster_capped"
    assert by["AMD"]["size_policy"] == "UNSIZED"
    assert by["AMD"]["reason"] == UNSIZED_REASON
    assert by["DOGEUSD"]["size_policy"] == "zero"


def test_scan_covers_monitor_list_and_renders_unresolved() -> None:
    result = run_watchlist_from_fixture(LOCKED, repo_root=ROOT)
    instruments = tuple(row.instrument for row in result.rows)
    assert instruments == CRYPTO + BASE
    by = {row.instrument: row for row in result.rows}
    assert by["BTCUSD"].membership == "in_universe"
    assert by["BTCUSD"].tier == "universe"
    assert by["BTCUSD"].monitor_state == "COVERED"
    assert by["BTCUSD"].playbook_setup is True
    assert by["ETHUSD"].membership == "watch_only"
    assert by["NVDA"].monitor_state == "COVERED"
    assert by["UNIUSD"].monitor_state == "UNAVAILABLE"
    assert by["SAMSUN"].monitor_state == "UNAVAILABLE"
    assert by["KOSDA"].monitor_state == "UNAVAILABLE"
    assert by["SAMSUN"].qualified_id == "KRX:005930"
    assert by["KOSDA"].qualified_id == "KRX:KQ11"
    assert by["SAMSUN"].idea_eligible is True
    assert by["CASHCAT"].monitor_state == "BLOCKED"
    assert by["CBRS"].new_listing is True
    assert by["CBRS"].scan_pod == "listings"
    assert "n/a (insufficient history:" in by["CBRS"].sma200
    assert "?" not in by["CBRS"].sma200
    assert by["CBRS"].lockup_inside_horizon is True
    assert by["SPCX"].qualified_id == "NASDAQ:SPCX"
    assert result.llm_calls == 0
    assert language_violations(result.markdown) == []
    assert "Not a call" in result.markdown
    first = run_watchlist_from_fixture(LOCKED, repo_root=ROOT)
    assert first.content_hash == result.content_hash
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
