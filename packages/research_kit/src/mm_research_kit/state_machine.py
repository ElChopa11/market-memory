"""Lifecycle state-machine skeleton over existing thesis statuses.

Git artifacts remain the human-review source. This module never imports
execution, signing, or Market Memory (the persistence hook is injected).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from mm_common.enums import (
    PHASE4_STATUS_VALUES,
    RISK_DECISION_VALUES,
    THESIS_STATUS_VALUES,
    RiskDecision,
    SkepticFailMode,
    SkepticVerdict,
    ThesisStatus,
)
from mm_common.time import utcnow
from mm_research_kit.errors import (
    AUTHOR_CANNOT_BE_SOLE_SKEPTIC,
    ILLEGAL_TRANSITION,
    NO_SELF_APPROVE,
    PAPER_LIVE_LATER,
    REJECTED_IS_TERMINAL,
    RETIRED_IS_TERMINAL,
    RISK_BLOCK_TERMINAL,
    GateError,
)

# Same graph as Phase 4. live is listed but refused until a later phase.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    ThesisStatus.DRAFT.value: {
        ThesisStatus.IN_RESEARCH.value,
        ThesisStatus.REJECTED.value,
    },
    ThesisStatus.IN_RESEARCH.value: {
        ThesisStatus.IN_SKEPTIC.value,
        ThesisStatus.REJECTED.value,
        ThesisStatus.DRAFT.value,
    },
    ThesisStatus.IN_SKEPTIC.value: {
        ThesisStatus.IN_RESEARCH.value,
        ThesisStatus.REJECTED.value,
        ThesisStatus.RETIRED.value,
        ThesisStatus.PAPER.value,
    },
    ThesisStatus.REJECTED.value: set(),
    ThesisStatus.RETIRED.value: set(),
    ThesisStatus.PAPER.value: {
        ThesisStatus.REJECTED.value,
        ThesisStatus.RETIRED.value,
    },
    ThesisStatus.LIVE.value: set(),
}

PROGRESSION_TARGETS = frozenset(
    {
        ThesisStatus.IN_SKEPTIC.value,
        ThesisStatus.PAPER.value,
        ThesisStatus.LIVE.value,
    }
)


@dataclass(frozen=True)
class TransitionLog:
    """Hook shape to Market Memory: actor, ts, reason (+ status pair)."""

    actor: str
    ts: datetime
    reason: str
    from_status: str
    to_status: str
    thesis_slug: str | None = None
    risk_decision: str = RiskDecision.PENDING.value
    principal_override: bool = False


TransitionHook = Callable[[TransitionLog], None]


def skeptic_fail_target(mode: str) -> str:
    """Map Principal FAIL language onto existing statuses."""
    value = mode.strip().lower()
    if value in {SkepticFailMode.RETURN.value, SkepticVerdict.REVISE.value}:
        return ThesisStatus.IN_RESEARCH.value
    if value in {SkepticFailMode.ARCHIVE.value, SkepticVerdict.REJECT.value}:
        return ThesisStatus.REJECTED.value
    raise GateError(f"unknown skeptic FAIL mode {mode!r}")


def assert_not_self_approve(*, author: str, actor: str, gate: str) -> None:
    """Authoring desk cannot clear Skeptic, Risk, or Principal override."""
    if not author.strip() or not actor.strip():
        raise GateError(NO_SELF_APPROVE)
    if actor.strip().lower() == author.strip().lower():
        if gate == "skeptic":
            raise GateError(AUTHOR_CANNOT_BE_SOLE_SKEPTIC)
        raise GateError(NO_SELF_APPROVE)
    if gate == "principal_override" and actor.strip().lower() not in {"principal", "cio"}:
        raise GateError("only the Principal may override a Risk BLOCK")


def validate_transition(
    current: str,
    target: str,
    *,
    risk_decision: str = RiskDecision.PENDING.value,
    principal_override: bool = False,
    actor: str | None = None,
    author: str | None = None,
    gate: str | None = None,
) -> None:
    current = current.strip().lower()
    target = target.strip().lower()
    decision = (risk_decision or RiskDecision.PENDING.value).strip().lower()
    if target not in THESIS_STATUS_VALUES:
        raise GateError(f"unknown status {target!r}")
    if current not in THESIS_STATUS_VALUES:
        raise GateError(f"unknown status {current!r}")
    if decision not in RISK_DECISION_VALUES:
        raise GateError(f"unknown risk decision {risk_decision!r}")
    if current == ThesisStatus.REJECTED.value and target != ThesisStatus.REJECTED.value:
        raise GateError(REJECTED_IS_TERMINAL)
    if current == ThesisStatus.RETIRED.value and target != ThesisStatus.RETIRED.value:
        raise GateError(RETIRED_IS_TERMINAL)
    if target == ThesisStatus.LIVE.value:
        raise GateError(PAPER_LIVE_LATER)
    if target not in PHASE4_STATUS_VALUES and target != ThesisStatus.LIVE.value:
        raise GateError(f"status {target!r} is not available")
    if author and actor and gate:
        assert_not_self_approve(author=author, actor=actor, gate=gate)
    if decision == RiskDecision.BLOCK.value and target in PROGRESSION_TARGETS and not principal_override:
        raise GateError(RISK_BLOCK_TERMINAL)
    if principal_override and author and actor:
        assert_not_self_approve(author=author, actor=actor, gate="principal_override")
    if target == current:
        return
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise GateError(f"{ILLEGAL_TRANSITION}: cannot advance {current} → {target}")


def build_transition_log(
    *,
    from_status: str,
    to_status: str,
    actor: str,
    reason: str,
    ts: datetime | None = None,
    thesis_slug: str | None = None,
    risk_decision: str = RiskDecision.PENDING.value,
    principal_override: bool = False,
) -> TransitionLog:
    return TransitionLog(
        actor=actor,
        ts=ts or utcnow(),
        reason=reason,
        from_status=from_status,
        to_status=to_status,
        thesis_slug=thesis_slug,
        risk_decision=risk_decision,
        principal_override=principal_override,
    )


def emit_transition(log: TransitionLog, hook: TransitionHook | None) -> TransitionLog:
    if hook is not None:
        hook(log)
    return log
