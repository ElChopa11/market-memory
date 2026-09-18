"""Phase 5a: illegal lifecycle transitions, Skeptic FAIL, Risk BLOCK, no self-approve."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mm_common.enums import RiskDecision, ThesisStatus
from mm_research_kit.errors import GateError
from mm_research_kit.state_machine import (
    ALLOWED_TRANSITIONS,
    build_transition_log,
    emit_transition,
    skeptic_fail_target,
    validate_transition,
)


def test_skeptic_fail_return_and_archive() -> None:
    assert skeptic_fail_target("return") == ThesisStatus.IN_RESEARCH.value
    assert skeptic_fail_target("revise") == ThesisStatus.IN_RESEARCH.value
    assert skeptic_fail_target("archive") == ThesisStatus.REJECTED.value
    assert skeptic_fail_target("reject") == ThesisStatus.REJECTED.value
    with pytest.raises(GateError, match="unknown skeptic FAIL"):
        skeptic_fail_target("pass")


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("draft", "in_skeptic"),
        ("draft", "paper"),
        ("draft", "live"),
        ("in_research", "paper"),
        ("in_research", "live"),
        ("in_skeptic", "live"),
        ("in_skeptic", "draft"),
        ("rejected", "in_research"),
        ("rejected", "paper"),
        ("retired", "paper"),
        ("paper", "in_research"),
        ("paper", "live"),
        ("live", "paper"),
    ],
)
def test_illegal_transitions_are_rejected(current: str, target: str) -> None:
    with pytest.raises(GateError):
        validate_transition(current, target)


def test_legal_graph_edges_still_exist() -> None:
    validate_transition("draft", "in_research")
    validate_transition("in_research", "in_skeptic")
    validate_transition("in_skeptic", "in_research")  # FAIL return
    validate_transition("in_skeptic", "rejected")  # FAIL archive
    validate_transition("in_skeptic", "paper")
    assert "live" not in ALLOWED_TRANSITIONS[ThesisStatus.PAPER.value]


def test_risk_block_is_terminal_without_principal_override() -> None:
    with pytest.raises(GateError, match="Risk BLOCK is terminal"):
        validate_transition(
            "in_skeptic",
            "paper",
            risk_decision=RiskDecision.BLOCK.value,
        )
    validate_transition(
        "in_skeptic",
        "paper",
        risk_decision=RiskDecision.BLOCK.value,
        principal_override=True,
        actor="Principal",
        author="Crypto Desk",
    )
    # FAIL return/archive still allowed under BLOCK (not promotion).
    validate_transition("in_skeptic", "in_research", risk_decision=RiskDecision.BLOCK.value)
    validate_transition("in_skeptic", "rejected", risk_decision=RiskDecision.BLOCK.value)


def test_proposing_desk_cannot_override_risk_block() -> None:
    with pytest.raises(GateError, match="only the Principal"):
        validate_transition(
            "in_skeptic",
            "paper",
            risk_decision=RiskDecision.BLOCK.value,
            principal_override=True,
            actor="Crypto Desk",
            author="Quant",
        )
    with pytest.raises(GateError, match="no self-approve"):
        validate_transition(
            "in_skeptic",
            "paper",
            risk_decision=RiskDecision.BLOCK.value,
            principal_override=True,
            actor="Crypto Desk",
            author="Crypto Desk",
        )


def test_no_self_approve_on_skeptic_gate() -> None:
    with pytest.raises(GateError, match="not the sole skeptic"):
        validate_transition(
            "in_research",
            "in_skeptic",
            actor="Research",
            author="Research",
            gate="skeptic",
        )


def test_live_remains_later_phase() -> None:
    with pytest.raises(GateError, match="later phase"):
        validate_transition("paper", "live")


def test_transition_log_hook_shape() -> None:
    captured: list = []
    log = build_transition_log(
        from_status="in_skeptic",
        to_status="rejected",
        actor="Skeptic",
        reason="FAIL archive: invalidation circular",
        ts=datetime(2026, 9, 18, tzinfo=timezone.utc),
        thesis_slug="THESIS-0001",
        risk_decision="pending",
    )
    emit_transition(log, captured.append)
    assert captured == [log]
    assert log.actor == "Skeptic"
    assert log.ts.tzinfo is not None
    assert log.reason.startswith("FAIL archive")
    assert log.from_status == "in_skeptic"
    assert log.to_status == "rejected"
