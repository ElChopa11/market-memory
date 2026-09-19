"""Phase 6c-4 watchlist monitor: locked universe daily scan, provenance, no calls."""

from __future__ import annotations

from pathlib import Path

from mm_common.naming import RESEARCH, WATCHLIST, desk_display, sleeve_display
from mm_desks.universe import locked_instruments, locked_watchlist
from mm_desks.watchlist import ENGINE_VERSION, run_watchlist_from_fixture
from mm_research_kit.quant_review.language import language_violations

ROOT = Path(__file__).resolve().parents[2]
NO_SETUP = ROOT / "tests" / "fixtures" / "phase6c" / "no_setup.json"
LOCKED = ROOT / "tests" / "fixtures" / "phase6c4" / "locked_scan.json"
IDEAS = ROOT / "tests" / "fixtures" / "phase6c" / "ideas.json"

LOCKED_NAMES = (
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
DEFERRED = ("HYPE", "SOL", "XRP", "ARB", "NEAR", "LINK", "GLD", "LLY")


def test_locked_watchlist_is_in_universe_union_watch_only() -> None:
    names = locked_instruments(ROOT)
    assert names == LOCKED_NAMES
    rows = locked_watchlist(ROOT)
    membership = {row.instrument: row.membership for row in rows}
    assert membership["BTC"] == "in_universe"
    assert membership["ETH"] == "watch_only"
    assert membership["NVDA"] == "in_universe"
    assert membership["SMH"] == "watch_only"
    assert membership["XLF"] == "watch_only"
    assert set(names).isdisjoint(DEFERRED)


def test_scan_covers_locked_universe_only() -> None:
    result = run_watchlist_from_fixture(LOCKED, repo_root=ROOT)
    instruments = tuple(row.instrument for row in result.rows)
    assert "BTCUSD" in instruments
    assert "NVDA" in instruments
    assert "AAVE" not in instruments
    assert "AVGO" not in instruments
    by_name = {row.instrument: row for row in result.rows}
    assert by_name["BTCUSD"].membership == "in_universe"
    assert by_name["BTCUSD"].monitor_state == "COVERED"
    assert by_name["BTCUSD"].playbook_setup is True
    assert by_name["ETHUSD"].membership == "watch_only"
    assert by_name["ETHUSD"].monitor_state == "COVERED"
    assert by_name["NVDA"].monitor_state == "COVERED"
    assert by_name["UNIUSD"].monitor_state == "UNAVAILABLE"
    assert result.status == "DEGRADED"
    assert result.llm_calls == 0
    assert result.as_public_dict()["n_llm_calls"] == 0


def test_scan_is_deterministic() -> None:
    first = run_watchlist_from_fixture(LOCKED, repo_root=ROOT)
    second = run_watchlist_from_fixture(LOCKED, repo_root=ROOT)
    assert first.content_hash == second.content_hash
    assert first.run_id == second.run_id
    assert first.envelopes[0].content_hash == second.envelopes[0].content_hash
    assert len(first.content_hash) == 64


def test_scan_uses_naming_and_research_envelope() -> None:
    result = run_watchlist_from_fixture(LOCKED, repo_root=ROOT)
    assert result.output.slug == RESEARCH
    assert result.output.desk == desk_display(RESEARCH)
    assert sleeve_display(WATCHLIST) in result.markdown
    assert result.output.as_of_knowledge.isoformat().startswith("2026-09-18")
    env = result.envelopes[0]
    assert env.desk == RESEARCH
    assert env.channel == "desk.research.output"
    assert env.cadence == "daily"
    assert env.op == "observation"
    assert env.content_hash
    assert result.engine_version == ENGINE_VERSION


def test_scan_never_invents_prints_or_calls() -> None:
    result = run_watchlist_from_fixture(NO_SETUP, repo_root=ROOT)
    by_name = {row.instrument: row for row in result.rows}
    assert by_name["UNIUSD"].metrics == ()
    assert by_name["UNIUSD"].freshness == "unavailable"
    assert "not invented" in by_name["UNIUSD"].notes
    assert language_violations(result.markdown) == []
    assert "Not a call" in result.markdown
    assert "Not a Quant verdict" in result.markdown
    lowered = result.markdown.lower()
    assert "buy" not in lowered
    assert "sell" not in lowered
    assert "active call" not in lowered
    assert result.llm_calls == 0


def test_playbook_setup_flag_does_not_inherit_trade_math() -> None:
    result = run_watchlist_from_fixture(IDEAS, repo_root=ROOT)
    btc = next(row for row in result.rows if row.instrument == "BTCUSD")
    assert btc.playbook_setup is True
    payload = result.output.payload
    assert payload["promote"] is False
    assert payload["llm"] is False
    assert "trade_math" not in payload
    assert "size_pct" not in result.markdown
    assert "R_target" not in result.markdown
    assert "lab playbook run" in btc.notes
