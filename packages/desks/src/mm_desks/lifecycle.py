"""Apply Phase 5a lifecycle transitions from desk runners. Illegal edges fail."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from mm_common.enums import ThesisStatus
from mm_desks.protocol import DeskContext
from mm_research_kit.errors import GateError
from mm_research_kit.lifecycle import advance_status
from mm_research_kit.state_machine import (
    TransitionLog,
    build_transition_log,
    emit_transition,
    validate_transition,
)


def record_transition(
    ctx: DeskContext,
    *,
    from_status: str,
    to_status: str,
    actor: str,
    reason: str,
    ts: datetime,
    risk_decision: str = "pending",
    principal_override: bool = False,
    author: str | None = None,
    gate: str | None = None,
) -> TransitionLog:
    """Validate, optionally write git artifacts, and append the Phase 5a log hook."""
    validate_transition(
        from_status,
        to_status,
        risk_decision=risk_decision,
        principal_override=principal_override,
        actor=actor,
        author=author,
        gate=gate,
    )
    log = build_transition_log(
        from_status=from_status,
        to_status=to_status,
        actor=actor,
        reason=reason,
        ts=ts,
        thesis_slug=None if ctx.thesis is None else ctx.thesis.slug,
        risk_decision=risk_decision,
        principal_override=principal_override,
    )
    emit_transition(log, ctx.events.append)
    if ctx.workspace is not None:
        _apply_workspace(
            ctx.workspace,
            to_status,
            actor=actor,
            reason=reason,
            risk_decision=risk_decision,
            principal_override=principal_override,
        )
    if ctx.thesis is not None:
        ctx.thesis.status = to_status
    return log


def record_event(
    ctx: DeskContext,
    *,
    from_status: str,
    to_status: str,
    actor: str,
    reason: str,
    ts: datetime,
    risk_decision: str = "pending",
    principal_override: bool = False,
) -> TransitionLog:
    """Append a Phase 5a log row without changing status (stamps / BLOCK notes)."""
    log = build_transition_log(
        from_status=from_status,
        to_status=to_status,
        actor=actor,
        reason=reason,
        ts=ts,
        thesis_slug=None if ctx.thesis is None else ctx.thesis.slug,
        risk_decision=risk_decision,
        principal_override=principal_override,
    )
    emit_transition(log, ctx.events.append)
    return log


def _apply_workspace(
    workspace: Path,
    target: str,
    *,
    actor: str,
    reason: str,
    risk_decision: str,
    principal_override: bool,
) -> None:
    if not workspace.is_dir():
        raise GateError(f"workspace missing: {workspace}")
    advance_status(
        workspace,
        target,
        actor=actor,
        reason=reason,
        risk_decision=risk_decision,
        principal_override=principal_override,
    )


def current_status(ctx: DeskContext) -> str:
    if ctx.thesis is not None and ctx.thesis.status:
        return ctx.thesis.status.strip().lower()
    return ThesisStatus.DRAFT.value
