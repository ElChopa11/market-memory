"""Open and record independent skeptic reviews (pass | revise | reject)."""

from __future__ import annotations

from pathlib import Path

from mm_common.enums import SkepticVerdict, ThesisStatus
from mm_research_kit.artifacts import fill_skeptic_review, isoformat_now, read_text, write_text
from mm_research_kit.errors import REJECTED_IS_TERMINAL, GateError
from mm_research_kit.evidence import has_evidence_links
from mm_research_kit.lifecycle import (
    IN_SKEPTIC_WITHOUT_EVIDENCE,
    advance_status,
    assert_can_mark,
    assert_independent_skeptic,
    read_status,
)
from mm_research_kit.markdown import append_bullet_under_heading, get_field
from mm_research_kit.state_machine import skeptic_fail_target

VALID_VERDICTS = {item.value for item in SkepticVerdict}


def _slug(workspace: Path) -> str:
    thesis = workspace / "thesis.md"
    if thesis.is_file():
        return get_field(read_text(thesis), "Thesis id") or workspace.name
    return workspace.name


def _write_review(workspace: Path, *, reviewer: str, verdict: str | None, created_at: str | None) -> None:
    path = workspace / "skeptic-review.md"
    if not path.is_file():
        raise GateError("skeptic-review.md is missing")
    current = read_text(path)
    stamp_created = created_at or get_field(current, "Created at") or isoformat_now()
    write_text(
        path,
        fill_skeptic_review(
            current,
            slug=_slug(workspace),
            reviewer=reviewer,
            created_at=stamp_created,
            verdict=verdict,
        ),
    )


def open_skeptic_review(workspace: Path, *, reviewer: str) -> str:
    """Mark in_skeptic and stamp reviewer metadata. Requires evidence links."""
    reviewer = reviewer.strip()
    if not reviewer:
        raise GateError("skeptic reviewer is required")
    assert_independent_skeptic(workspace, reviewer)
    if not has_evidence_links(workspace):
        raise GateError(IN_SKEPTIC_WITHOUT_EVIDENCE)
    advance_status(workspace, ThesisStatus.IN_SKEPTIC.value)
    _write_review(workspace, reviewer=reviewer, verdict=None, created_at=isoformat_now())
    return ThesisStatus.IN_SKEPTIC.value


def record_skeptic_verdict(
    workspace: Path,
    *,
    verdict: str,
    reviewer: str,
    findings: str = "",
) -> str:
    verdict_value = verdict.strip().lower()
    if verdict_value not in VALID_VERDICTS:
        allowed = ", ".join(sorted(VALID_VERDICTS))
        raise GateError(f"verdict must be one of: {allowed}")
    reviewer = reviewer.strip()
    if not reviewer:
        raise GateError("skeptic reviewer is required")
    assert_independent_skeptic(workspace, reviewer)

    current = read_status(workspace) or ThesisStatus.DRAFT.value
    if current == ThesisStatus.REJECTED.value and verdict_value != SkepticVerdict.REJECT.value:
        raise GateError(REJECTED_IS_TERMINAL)

    if verdict_value == SkepticVerdict.PASS.value:
        if not has_evidence_links(workspace):
            raise GateError(IN_SKEPTIC_WITHOUT_EVIDENCE)
        assert_can_mark(workspace, ThesisStatus.IN_SKEPTIC.value)
        advance_status(workspace, ThesisStatus.IN_SKEPTIC.value)
    elif verdict_value == SkepticVerdict.REVISE.value:
        if current == ThesisStatus.IN_SKEPTIC.value:
            advance_status(workspace, skeptic_fail_target("return"))
    else:
        if current != ThesisStatus.REJECTED.value:
            assert_can_mark(workspace, skeptic_fail_target("archive"))
            advance_status(workspace, skeptic_fail_target("archive"))

    _write_review(workspace, reviewer=reviewer, verdict=verdict_value, created_at=None)
    path = workspace / "skeptic-review.md"
    if findings.strip():
        text = read_text(path)
        try:
            text = append_bullet_under_heading(text, "Required fixes before paper", f"- {findings.strip()}")
        except KeyError:
            text = text.rstrip() + f"\n\n## Findings\n\n{findings.strip()}\n"
        from mm_research_kit.artifacts import write_text as _write

        _write(path, text)
    return read_status(workspace) or current
