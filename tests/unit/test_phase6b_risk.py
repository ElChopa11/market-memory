"""Phase 6b risk stubs: UNTRADEABLE_AT_SIZE block + EVENT_RISK haircut."""

from __future__ import annotations

from pathlib import Path

from mm_desks.orchestrator import run_from_fixture
from mm_risk.engine import RULE_ALLOW, RULE_EVENT_RISK, RULE_UNTRADEABLE, evaluate
from mm_risk.models import RiskIntent

ROOT = Path(__file__).resolve().parents[2]
HAPPY = ROOT / "tests" / "fixtures" / "phase6b" / "frozen_day.json"
EVENT = ROOT / "tests" / "fixtures" / "phase6b" / "event_risk.json"
UNTRADE = ROOT / "tests" / "fixtures" / "phase6b" / "untradeable.json"


def test_untradeable_blocks_from_yaml() -> None:
    blocked = evaluate(
        RiskIntent(
            instrument="BTC",
            invalidation="funding flips negative",
            max_loss="2% of dedicated research budget",
            environment="paper",
            liquidity_verdict="UNTRADEABLE_AT_SIZE",
        ),
        repo_root=ROOT,
    )
    assert blocked.decision == "block"
    assert blocked.rule_id == RULE_UNTRADEABLE
    assert blocked.terminal is True


def test_event_risk_haircut_is_not_a_block() -> None:
    result = evaluate(
        RiskIntent(
            instrument="BTC",
            invalidation="funding flips negative",
            max_loss="2% of dedicated research budget",
            environment="paper",
            event_risk=True,
        ),
        repo_root=ROOT,
    )
    assert result.decision == "allow"
    assert result.rule_id == RULE_EVENT_RISK
    assert result.haircut_pct == 50.0
    assert result.terminal is False


def test_untradeable_beats_event_risk() -> None:
    result = evaluate(
        RiskIntent(
            instrument="BTC",
            invalidation="funding flips negative",
            max_loss="2%",
            environment="paper",
            liquidity_verdict="UNTRADEABLE_AT_SIZE",
            event_risk=True,
        ),
        repo_root=ROOT,
    )
    assert result.decision == "block"
    assert result.rule_id == RULE_UNTRADEABLE


def test_plain_allow_unchanged() -> None:
    result = evaluate(
        RiskIntent(
            instrument="BTC",
            invalidation="funding flips negative",
            max_loss="2% of dedicated research budget",
            environment="paper",
        ),
        repo_root=ROOT,
    )
    assert result.decision == "allow"
    assert result.rule_id == RULE_ALLOW
    assert result.haircut_pct is None


def test_desk_wires_untradeable_into_risk() -> None:
    result = run_from_fixture(UNTRADE, repo_root=ROOT)
    by = {row.slug: row for row in result.desks}
    assert by["flow"].payload["verdicts"]["BTC"] == "UNTRADEABLE_AT_SIZE"
    assert by["risk"].payload["decision"] == "block"
    assert by["risk"].payload["rule_id"] == RULE_UNTRADEABLE
    assert by["risk"].payload["terminal"] is True


def test_desk_wires_event_risk_haircut() -> None:
    result = run_from_fixture(EVENT, repo_root=ROOT)
    by = {row.slug: row for row in result.desks}
    assert by["macro"].payload["event_risk"]["tagged"] is True
    assert by["risk"].payload["event_risk"] is True
    assert by["risk"].payload["decision"] == "allow"
    assert by["risk"].payload["rule_id"] == RULE_EVENT_RISK
    assert by["risk"].payload["haircut_pct"] == 50.0
    assert "EVENT_RISK" in result.pack_markdown or "event_risk" in result.pack_markdown
