"""Standing Gate 5 earnings limitation on the brief GAPS line. Paper only."""

from __future__ import annotations

from pathlib import Path

from mm_desks.fixture import load_frozen_day
from mm_desks.gaps import GATE5_EARNINGS_GAPS_LINE, with_gate5_gaps_line
from mm_desks.pack import render_output_contract
from mm_desks.playbook import run_playbook_from_fixture
from mm_desks.protocol import DeskContext

ROOT = Path(__file__).resolve().parents[2]
NO_SETUP = ROOT / "tests" / "fixtures" / "phase6c" / "no_setup.json"
FROZEN = ROOT / "tests" / "fixtures" / "phase5d" / "frozen_day.json"


def test_gaps_line_names_the_earnings_source_gap() -> None:
    assert "0/15 Polygon confirmation" in GATE5_EARNINGS_GAPS_LINE
    assert "Benzinga 403" in GATE5_EARNINGS_GAPS_LINE
    assert "events=ticker_change only" in GATE5_EARNINGS_GAPS_LINE
    assert "lockup + macro only" in GATE5_EARNINGS_GAPS_LINE
    text = with_gate5_gaps_line("no actionable setup\n")
    assert text.startswith("GAPS: ")
    assert GATE5_EARNINGS_GAPS_LINE in text
    assert text.count("GAPS: ") == 1
    assert with_gate5_gaps_line(text) == text


def test_official_brief_carries_the_gaps_line_with_zero_llm() -> None:
    run = run_playbook_from_fixture(NO_SETUP, repo_root=ROOT)
    assert run.llm_calls == ()
    brief = next(a for a in run.artifacts if a.artifact_type == "OFFICIAL_BRIEF")
    cut = str(brief.payload["executive_cut"])
    assert cut.startswith("GAPS: ")
    assert GATE5_EARNINGS_GAPS_LINE in cut
    assert "no actionable setup" in cut.lower()
    lowered = cut.lower()
    assert "yield" not in lowered
    assert "10y" not in lowered


def test_desk_pack_data_gaps_includes_the_same_line() -> None:
    day = load_frozen_day(FROZEN, repo_root=ROOT)
    ctx = DeskContext(repo_root=ROOT, fixture=day, thesis=day.thesis)
    markdown = render_output_contract(day.as_of_knowledge, ctx, calendar_lines=("none",))
    assert "## DATA GAPS" in markdown
    assert GATE5_EARNINGS_GAPS_LINE in markdown
    assert "standing source gap on the brief" in markdown
