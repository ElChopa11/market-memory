"""IC/Risk Skeptic gate. Adversarial checklist. FAIL return or FAIL archive. Not a desk."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mm_common.enums import SkepticVerdict, ThesisStatus
from mm_desks.lifecycle import current_status, record_transition
from mm_desks.protocol import DeskArtifact, DeskContext, DeskOutput, FAILED, OK
from mm_research_kit.errors import GateError
from mm_research_kit.state_machine import skeptic_fail_target

from mm_desks.naming import sleeve_display, sleeve_tier

SLUG = "skeptic"
TIER = sleeve_tier(SLUG)
DISPLAY_NAME = sleeve_display(SLUG)

_PLACEHOLDERS = frozenset({"", "-", "n/a", "na", "none", "null", "tbd", "todo", "?", "unknown"})


def _checklist(ctx: DeskContext) -> list[dict[str, Any]]:
    thesis = ctx.thesis
    items: list[dict[str, Any]] = []

    def add(code: str, ok: bool, detail: str, *, fail_mode: str | None = None) -> None:
        items.append({"code": code, "ok": ok, "detail": detail, "fail_mode": fail_mode})

    author = (thesis.author if thesis else "") or ""
    reviewer = (thesis.reviewer if thesis else "") or "Independent Skeptic"
    add(
        "independent_reviewer",
        bool(reviewer.strip()) and reviewer.strip().lower() != author.strip().lower(),
        "author cannot be the sole skeptic of record",
        fail_mode="return",
    )
    evidence = thesis.evidence_ids if thesis else ()
    add("evidence_present", bool(evidence), "in_skeptic requires evidence links", fail_mode="return")
    add(
        "look_ahead",
        not bool(thesis and thesis.look_ahead),
        "look-ahead / leakage vs as_of_knowledge",
        fail_mode="return",
    )
    add(
        "leakage",
        not bool(thesis and thesis.leakage),
        "feature leakage",
        fail_mode="return",
    )
    quality = (thesis.invalidation_quality if thesis else "ok") or "ok"
    circular = quality.strip().lower() in {"circular", "poor", "placeholder", "missing", "fail"}
    inv = (thesis.invalidation if thesis else "") or ""
    add(
        "invalidation_quality",
        (not circular) and inv.strip().lower() not in _PLACEHOLDERS,
        f"invalidation_quality={quality}",
        fail_mode="archive" if circular else "return",
    )
    add(
        "already_priced",
        not bool(thesis and thesis.already_priced),
        "already-priced / crowded without invalidation",
        fail_mode="return",
    )
    from mm_desks.invalidation import evaluate_invalidation

    for row in evaluate_invalidation(thesis):
        items.append(row)
    return items


def _forced(ctx: DeskContext) -> str | None:
    day = ctx.fixture
    force = getattr(day, "skeptic_force_verdict", None)
    if force in {SkepticVerdict.PASS.value, SkepticVerdict.REVISE.value, SkepticVerdict.REJECT.value}:
        return force
    if force in {"return", "archive"}:
        return SkepticVerdict.REVISE.value if force == "return" else SkepticVerdict.REJECT.value
    return None


def run(as_of: datetime, ctx: DeskContext) -> DeskOutput:
    items = _checklist(ctx)
    failed = [row for row in items if not row["ok"]]
    force = _forced(ctx)
    if force == SkepticVerdict.PASS.value and failed:
        # Forced pass cannot override a failed checklist (no rubber-stamp).
        force = None
    if force == SkepticVerdict.PASS.value:
        verdict = SkepticVerdict.PASS.value
        fail_mode = None
    elif force in {SkepticVerdict.REVISE.value, SkepticVerdict.REJECT.value}:
        verdict = force
        fail_mode = "return" if verdict == SkepticVerdict.REVISE.value else "archive"
    elif failed:
        archive = any(row["fail_mode"] == "archive" for row in failed)
        fail_mode = "archive" if archive else "return"
        verdict = SkepticVerdict.REJECT.value if archive else SkepticVerdict.REVISE.value
    else:
        verdict = SkepticVerdict.PASS.value
        fail_mode = None

    thesis = ctx.thesis
    author = thesis.author if thesis else "Research"
    reviewer = thesis.reviewer if thesis else DISPLAY_NAME
    from_status = current_status(ctx)
    notes: list[str] = [f"{row['code']}: {row['detail']}" for row in failed]
    events_payload: list[dict[str, str]] = []
    status = OK
    try:
        if verdict == SkepticVerdict.PASS.value:
            if from_status != ThesisStatus.IN_SKEPTIC.value:
                record_transition(
                    ctx,
                    from_status=from_status,
                    to_status=ThesisStatus.IN_SKEPTIC.value,
                    actor=reviewer,
                    reason="Skeptic pass; remain at in_skeptic (paper is not auto-opened)",
                    ts=as_of,
                    author=author,
                    gate="skeptic",
                )
            elif thesis is not None:
                # Same-status stamp still logged (Phase 5a hook).
                record_transition(
                    ctx,
                    from_status=from_status,
                    to_status=ThesisStatus.IN_SKEPTIC.value,
                    actor=reviewer,
                    reason="Skeptic pass",
                    ts=as_of,
                    author=author,
                    gate="skeptic",
                )
        else:
            assert fail_mode is not None
            target = skeptic_fail_target(fail_mode)
            reason = (
                f"Skeptic FAIL {fail_mode}: " + "; ".join(row["code"] for row in failed)
                if failed
                else f"Skeptic FAIL {fail_mode}"
            )
            record_transition(
                ctx,
                from_status=from_status,
                to_status=target,
                actor=reviewer,
                reason=reason,
                ts=as_of,
                author=author,
                gate="skeptic",
            )
            notes = (reason,) + tuple(notes)
    except GateError as exc:
        status = FAILED
        notes = (str(exc),) + tuple(notes)
        verdict = "failed_gate"
        fail_mode = fail_mode

    if ctx.events:
        last = ctx.events[-1]
        events_payload.append(
            {
                "actor": last.actor,
                "ts": last.ts.isoformat(),
                "reason": last.reason,
                "from_status": last.from_status,
                "to_status": last.to_status,
            }
        )

    lines = [
        f"# Skeptic checklist — {ctx.fixture.session_date}",
        "",
        f"- **Independent Skeptic of record:** {reviewer}",
        f"- **Authoring desk:** {author}",
        f"- **Verdict:** `{verdict}`"
        + (f" (FAIL {fail_mode})" if fail_mode else ""),
        f"- **Thesis status after:** `{ctx.thesis.status if ctx.thesis else from_status}`",
        "",
        "| code | ok | fail_mode | detail |",
        "| --- | --- | --- | --- |",
    ]
    for row in items:
        lines.append(
            f"| {row['code']} | {'yes' if row['ok'] else 'no'} | {row['fail_mode'] or '—'} | {row['detail']} |"
        )
    lines.append("")
    artifact = DeskArtifact(name="skeptic-checklist", kind="markdown", content="\n".join(lines), relpath="skeptic.md")
    completeness = 100.0 if status == OK else 0.0
    return DeskOutput(
        desk=DISPLAY_NAME,
        slug=SLUG,
        tier=TIER,
        status=status,
        completeness_pct=completeness,
        provenance_ids=tuple(thesis.evidence_ids) if thesis else (),
        artifacts=(artifact,),
        as_of_knowledge=as_of,
        notes=tuple(notes),
        payload={
            "verdict": verdict,
            "fail_mode": fail_mode,
            "checklist": items,
            "lifecycle": events_payload,
            "thesis_status": ctx.thesis.status if ctx.thesis else from_status,
        },
    )


class SkepticDesk:
    slug = SLUG
    tier = TIER
    display_name = DISPLAY_NAME

    def run(self, as_of: datetime, ctx: DeskContext) -> DeskOutput:
        return run(as_of, ctx)
