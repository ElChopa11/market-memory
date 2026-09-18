"""Phase 5d / IMP-012 desk runners: protocol, happy path, DEGRADED, FAIL, BLOCK."""

from __future__ import annotations

from pathlib import Path

import pytest

from mm_desks.lifecycle import record_transition
from mm_desks.orchestrator import PIPELINE, run_from_fixture
from mm_desks.protocol import DEGRADED, OK, DeskContext
from mm_research_kit.errors import GateError
from mm_risk.engine import RULE_NOT_ALLOWLISTED, evaluate
from mm_risk.models import RiskIntent

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "phase5d"


def _run(name: str, slugs: tuple[str, ...] | None = None):
    return run_from_fixture(FIXTURES / name, repo_root=ROOT, slugs=slugs)


def _by_slug(result):
    return {row.slug: row for row in result.desks}


def test_happy_path_all_desks_ok_and_hash_stable() -> None:
    first = _run("frozen_day.json")
    second = _run("frozen_day.json")
    assert first.content_hash == second.content_hash
    assert len(first.content_hash) == 64
    assert first.canonical() == second.canonical()
    assert [row.slug for row in first.desks] == list(PIPELINE)
    by_slug = _by_slug(first)
    for slug in PIPELINE:
        assert by_slug[slug].status == OK, slug
        assert by_slug[slug].completeness_pct == 100.0, slug
    assert "HEADER" in first.pack_markdown
    assert "TAPE" in first.pack_markdown
    assert "TRADE IDEAS (intent-only)" in first.pack_markdown
    assert "SKEPTIC FLAGS" in first.pack_markdown
    assert "RISK STATUS" in first.pack_markdown
    assert "CALENDAR (stub)" in first.pack_markdown
    assert "US session open (stub)" in first.pack_markdown
    assert "`pass`" in first.pack_markdown or "`pass`" in by_slug["skeptic"].artifacts[0].content
    assert by_slug["risk"].payload["decision"] == "allow"
    assert by_slug["skeptic"].payload["verdict"] == "pass"
    assert by_slug["quant"].payload["verdict"] in {
        "RESEARCH_PRIORITY",
        "MONITOR",
        "DEFER",
        "REJECT",
        "INSUFFICIENT_DATA",
    }
    assert "fx-BTC-funding-0001" in by_slug["intel"].provenance_ids
    assert first.send is False


def test_missing_feed_is_degraded_never_invent() -> None:
    result = _run("missing_feed.json")
    by_slug = _by_slug(result)
    assert by_slug["intel"].status == DEGRADED
    assert by_slug["intel"].completeness_pct < 100.0
    assert "polygon" in by_slug["intel"].payload["required_missing"]
    intel_md = by_slug["intel"].artifacts[0].content
    assert "polygon" in intel_md
    assert "unavailable" in intel_md
    assert by_slug["equities"].status == DEGRADED
    pack = result.pack_markdown
    assert "polygon" in pack
    assert "unavailable" in pack
    assert by_slug["coord"].status == DEGRADED
    # Double-run still stable while degraded.
    again = _run("missing_feed.json")
    assert again.content_hash == result.content_hash


def test_skeptic_fail_returns_to_in_research() -> None:
    result = _run("skeptic_fail.json")
    by_slug = _by_slug(result)
    assert by_slug["skeptic"].payload["verdict"] == "revise"
    assert by_slug["skeptic"].payload["fail_mode"] == "return"
    assert by_slug["skeptic"].payload["thesis_status"] == "in_research"
    events = [event for event in result.events if event.to_status == "in_research"]
    assert events
    assert events[0].actor == "Independent Skeptic"
    assert events[0].reason.startswith("Skeptic FAIL return")
    assert "FAIL return" in result.pack_markdown or "revise (FAIL return)" in result.pack_markdown


def test_skeptic_fail_archive_on_circular_invalidation() -> None:
    from mm_desks.fixture import load_frozen_day
    from mm_desks.orchestrator import run_desks
    from mm_desks.protocol import DeskContext

    day = load_frozen_day(FIXTURES / "frozen_day.json", repo_root=ROOT)
    day.thesis.invalidation_quality = "circular"
    day.thesis.invalidation = "price is wrong because the thesis says so"
    ctx = DeskContext(repo_root=ROOT, fixture=day, thesis=day.thesis)
    result = run_desks(as_of=day.as_of_knowledge, ctx=ctx, slugs=PIPELINE)
    skeptic = {row.slug: row for row in result.desks}["skeptic"]
    assert skeptic.payload["verdict"] == "reject"
    assert skeptic.payload["fail_mode"] == "archive"
    assert day.thesis.status == "rejected"
    assert any(event.to_status == "rejected" for event in result.events)


def test_risk_block_is_terminal() -> None:
    result = _run("risk_block.json")
    by_slug = _by_slug(result)
    assert by_slug["risk"].payload["decision"] == "block"
    assert by_slug["risk"].payload["rule_id"] == RULE_NOT_ALLOWLISTED
    assert by_slug["risk"].payload["terminal"] is True
    assert "BLOCK" in result.pack_markdown
    assert any("Risk BLOCK" in event.reason for event in result.events)
    # Paper was requested and refused.
    assert any("terminal" in event.reason.lower() or "BLOCK" in event.reason for event in result.events)


def test_illegal_transition_rejected() -> None:
    from mm_desks.fixture import load_frozen_day

    day = load_frozen_day(FIXTURES / "frozen_day.json", repo_root=ROOT)
    ctx = DeskContext(repo_root=ROOT, fixture=day, thesis=day.thesis)
    with pytest.raises(GateError, match="illegal lifecycle transition"):
        record_transition(
            ctx,
            from_status="draft",
            to_status="paper",
            actor="Coordinator",
            reason="skip gates",
            ts=day.as_of_knowledge,
        )
    with pytest.raises(GateError, match="Risk BLOCK is terminal"):
        record_transition(
            ctx,
            from_status="in_skeptic",
            to_status="paper",
            actor="Risk (independent veto)",
            reason="should not promote",
            ts=day.as_of_knowledge,
            risk_decision="block",
            author="Crypto Desk",
        )


def test_risk_engine_allow_and_block_from_config() -> None:
    allow = evaluate(
        RiskIntent(
            instrument="BTC",
            invalidation="funding flips negative",
            max_loss="2% of dedicated research budget",
            environment="paper",
        ),
        repo_root=ROOT,
    )
    assert allow.decision == "allow"
    assert allow.live_trading_enabled is False
    blocked = evaluate(
        RiskIntent(
            instrument="SOL",
            invalidation="funding flips negative",
            max_loss="2% of dedicated research budget",
            environment="paper",
        ),
        repo_root=ROOT,
    )
    assert blocked.decision == "block"
    assert blocked.rule_id == RULE_NOT_ALLOWLISTED
    live = evaluate(
        RiskIntent(
            instrument="BTC",
            invalidation="funding flips negative",
            max_loss="2%",
            environment="live",
        ),
        repo_root=ROOT,
    )
    assert live.decision == "block"
    missing = evaluate(
        RiskIntent(instrument="BTC", invalidation="", max_loss="2%", environment="paper"),
        repo_root=ROOT,
    )
    assert missing.decision == "block"


def test_single_desk_intel_runs() -> None:
    result = _run("frozen_day.json", slugs=("intel",))
    assert [row.slug for row in result.desks] == ["intel"]
    assert result.desks[0].status == OK
