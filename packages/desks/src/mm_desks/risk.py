"""Risk desk (Tier 6): deterministic allow/block from versioned config. No LLM."""

from __future__ import annotations

from datetime import datetime

from mm_common.enums import RiskDecision, ThesisStatus
from mm_desks.lifecycle import current_status, record_event, record_transition
from mm_desks.protocol import DeskArtifact, DeskContext, DeskOutput, FAILED, OK
from mm_research_kit.errors import GateError
from mm_risk.config import load_risk_config
from mm_risk.engine import evaluate
from mm_risk.models import RiskIntent

SLUG = "risk"
TIER = "6"
DISPLAY_NAME = "Risk (independent veto)"


def run(as_of: datetime, ctx: DeskContext) -> DeskOutput:
    day = ctx.fixture
    spec = day.risk
    thesis = ctx.thesis
    author = thesis.author if thesis else "Crypto Desk"
    cfg = load_risk_config(ctx.repo_root, environment=spec.environment)
    flow = ctx.prior.get("flow")
    macro = ctx.prior.get("macro")
    instrument = spec.instrument
    liquidity_verdict = None
    if flow is not None:
        verdicts = (flow.payload or {}).get("verdicts") or {}
        liquidity_verdict = verdicts.get(instrument) or verdicts.get(instrument.upper())
    event_risk = False
    if macro is not None:
        event_risk = bool(((macro.payload or {}).get("event_risk") or {}).get("tagged"))
    intent = RiskIntent(
        instrument=spec.instrument,
        invalidation=spec.invalidation,
        max_loss=spec.max_loss,
        leverage=spec.leverage,
        environment=spec.environment,
        thesis_slug=None if thesis is None else thesis.slug,
        author=author,
        requested_target=spec.requested_target,
        halt=spec.halt,
        liquidity_verdict=None if liquidity_verdict is None else str(liquidity_verdict),
        event_risk=event_risk,
    )
    result = evaluate(intent, repo_root=ctx.repo_root, config=cfg, halt=spec.halt)
    notes = result.reasons
    status = OK
    from_status = current_status(ctx)
    lifecycle: list[dict[str, str]] = []

    if result.decision == RiskDecision.BLOCK.value and spec.requested_target == ThesisStatus.PAPER.value:
        try:
            record_transition(
                ctx,
                from_status=from_status,
                to_status=ThesisStatus.PAPER.value,
                actor=DISPLAY_NAME,
                reason="Risk BLOCK refuses paper",
                ts=as_of,
                risk_decision=result.decision,
                author=author,
                gate="risk",
            )
            status = FAILED
            notes = ("Risk BLOCK should have refused paper",) + notes
        except GateError as exc:
            notes = (str(exc),) + notes
            record_event(
                ctx,
                from_status=from_status,
                to_status=from_status,
                actor=DISPLAY_NAME,
                reason=f"Risk BLOCK terminal: {result.rule_id}",
                ts=as_of,
                risk_decision=result.decision,
            )
    elif result.decision == RiskDecision.BLOCK.value:
        record_event(
            ctx,
            from_status=from_status,
            to_status=from_status,
            actor=DISPLAY_NAME,
            reason=f"Risk BLOCK terminal: {result.rule_id}",
            ts=as_of,
            risk_decision=result.decision,
        )
    else:
        record_event(
            ctx,
            from_status=from_status,
            to_status=from_status,
            actor=DISPLAY_NAME,
            reason=f"Risk allow ({result.rule_id}); paper still requires Principal",
            ts=as_of,
            risk_decision=result.decision,
        )

    if ctx.events:
        last = ctx.events[-1]
        lifecycle.append(
            {
                "actor": last.actor,
                "ts": last.ts.isoformat(),
                "reason": last.reason,
                "from_status": last.from_status,
                "to_status": last.to_status,
                "risk_decision": last.risk_decision,
            }
        )

    lines = [
        f"# Risk decision — {day.session_date}",
        "",
        f"- **Decision:** `{result.decision}`",
        f"- **rule_id:** `{result.rule_id}`",
        f"- **config_version:** `{result.config_version}`",
        f"- **BLOCK terminal?** {'yes' if result.terminal else 'no'}",
        f"- **live_trading_enabled:** {str(result.live_trading_enabled).lower()}",
        f"- **liquidity_verdict:** `{liquidity_verdict or 'unset'}`",
        f"- **EVENT_RISK:** {'yes' if event_risk else 'no'}",
        f"- **size haircut_pct:** {result.haircut_pct if result.haircut_pct is not None else 'none'}",
        f"- **LLM at decision time:** false",
        "",
        "Reasons:",
        "",
    ]
    for reason in result.reasons:
        lines.append(f"- {reason}")
    lines.append("")
    artifact = DeskArtifact(name="risk-decision", kind="markdown", content="\n".join(lines), relpath="risk.md")
    return DeskOutput(
        desk=DISPLAY_NAME,
        slug=SLUG,
        tier=TIER,
        status=status,
        completeness_pct=100.0 if status == OK else 0.0,
        provenance_ids=(),
        artifacts=(artifact,),
        as_of_knowledge=as_of,
        notes=notes,
        payload={
            "decision": result.decision,
            "rule_id": result.rule_id,
            "config_version": result.config_version,
            "terminal": result.terminal,
            "reasons": list(result.reasons),
            "live_trading_enabled": result.live_trading_enabled,
            "haircut_pct": result.haircut_pct,
            "liquidity_verdict": liquidity_verdict,
            "event_risk": event_risk,
            "lifecycle": lifecycle,
        },
    )


class RiskDesk:
    slug = SLUG
    tier = TIER
    display_name = DISPLAY_NAME

    def run(self, as_of: datetime, ctx: DeskContext) -> DeskOutput:
        return run(as_of, ctx)
