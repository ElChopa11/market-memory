"""Definition-of-done gates for research workspaces.

Git artifacts are the human-review source. This module never reads trading
credentials and must not import execution or live signing.
"""

from __future__ import annotations

import sys
from pathlib import Path

from mm_common.enums import (
    PHASE2_STATUS_VALUES,
    STATUSES_REQUIRING_EVIDENCE,
    SKEPTIC_VERDICT_VALUES,
    THESIS_STATUS_VALUES,
    ThesisStatus,
)
from mm_research_kit.artifacts import read_text, write_text
from mm_research_kit.errors import (
    AUTHOR_CANNOT_BE_SOLE_SKEPTIC,
    IN_SKEPTIC_WITHOUT_EVIDENCE,
    NO_INTENT,
    PAPER_LIVE_LATER,
    REJECTED_IS_TERMINAL,
    GateError,
)
from mm_research_kit.evidence import has_evidence_links
from mm_research_kit.markdown import first_token, get_field, set_field

REQUIRED_TEMPLATES = [
    "intent.md",
    "thesis.md",
    "research-plan.md",
    "skeptic-review.md",
    "unicorn-card.md",
    "paper-trade.md",
    "promotion-decision.md",
    "post-mortem.md",
    "evidence-links.md",
]

SKIP_DIR_NAMES = {".git", "__pycache__", "evidence", "backtests", "paper"}

LATER_PHASE_STATUSES = {ThesisStatus.PAPER.value, ThesisStatus.LIVE.value}

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
    },
    ThesisStatus.REJECTED.value: set(),
    ThesisStatus.RETIRED.value: set(),
    ThesisStatus.PAPER.value: set(),
    ThesisStatus.LIVE.value: set(),
}


def _exists(workspace: Path, name: str) -> bool:
    return (workspace / name).is_file()


def _dir_nonempty(path: Path) -> bool:
    if not path.is_dir():
        return False
    return any(path.rglob("*"))


def _has_paper(workspace: Path) -> bool:
    if _exists(workspace, "paper-trade.md"):
        return True
    paper = workspace / "paper"
    if not paper.is_dir():
        return False
    return any(p.is_file() for p in paper.rglob("*"))


def _has_promotion(workspace: Path) -> bool:
    return _exists(workspace, "promotion-decision.md") or _exists(workspace, "promotion.md")


def is_thesis_workspace(path: Path) -> bool:
    if not path.is_dir():
        return False
    if path.name.startswith("THESIS-"):
        return True
    markers = (
        "intent.md",
        "thesis.md",
        "research-plan.md",
        "skeptic-review.md",
        "paper-trade.md",
        "promotion-decision.md",
        "promotion.md",
        "post-mortem.md",
        "unicorn-card.md",
    )
    return any(_exists(path, name) for name in markers)


def discover_workspaces(research_root: Path) -> list[Path]:
    if not research_root.is_dir():
        return []
    found: list[Path] = []
    for candidate in sorted(research_root.rglob("*")):
        if not candidate.is_dir():
            continue
        if candidate.name in SKIP_DIR_NAMES:
            continue
        if is_thesis_workspace(candidate):
            found.append(candidate)
    filtered: list[Path] = []
    for workspace in found:
        if any(other != workspace and other.is_relative_to(workspace) for other in found):
            continue
        filtered.append(workspace)
    return filtered


def check_templates(templates_root: Path) -> list[str]:
    errors: list[str] = []
    if not templates_root.is_dir():
        return [f"missing templates directory: {templates_root}"]
    for name in REQUIRED_TEMPLATES:
        if not (templates_root / name).is_file():
            errors.append(f"missing template: {templates_root / name}")
    return errors


def read_status(workspace: Path) -> str | None:
    thesis = workspace / "thesis.md"
    if thesis.is_file():
        token = first_token(get_field(thesis.read_text(encoding="utf-8"), "Status / version"))
        if not token:
            token = first_token(get_field(thesis.read_text(encoding="utf-8"), "Status"))
        if token:
            return token
    intent = workspace / "intent.md"
    if intent.is_file():
        token = first_token(get_field(intent.read_text(encoding="utf-8"), "Status"))
        if token:
            return token
    return None


def read_author_role(workspace: Path) -> str:
    thesis = workspace / "thesis.md"
    if thesis.is_file():
        value = get_field(thesis.read_text(encoding="utf-8"), "Author role")
        if value:
            return value
    intent = workspace / "intent.md"
    if intent.is_file():
        value = get_field(intent.read_text(encoding="utf-8"), "Owner")
        if value:
            return value
    return "Research"


def recorded_skeptic_verdict(workspace: Path) -> str | None:
    path = workspace / "skeptic-review.md"
    if not path.is_file():
        return None
    raw = get_field(path.read_text(encoding="utf-8"), "Verdict")
    if not raw or "|" in raw:
        return None
    token = first_token(raw)
    if token in SKEPTIC_VERDICT_VALUES:
        return token
    return None


def check_workspace(workspace: Path) -> list[str]:
    errors: list[str] = []
    rel = workspace.as_posix()

    if _exists(workspace, "thesis.md") and not _exists(workspace, "intent.md"):
        errors.append(f"{rel}: thesis without intent")

    if _exists(workspace, "research-plan.md") and not _exists(workspace, "thesis.md"):
        errors.append(f"{rel}: research-plan without thesis")

    if _exists(workspace, "skeptic-review.md") and not _exists(workspace, "research-plan.md"):
        errors.append(f"{rel}: skeptic-review without research-plan")

    evidence = workspace / "evidence"
    backtests = workspace / "backtests"
    if (_dir_nonempty(evidence) or _dir_nonempty(backtests)) and not _exists(workspace, "research-plan.md"):
        errors.append(f"{rel}: evidence/backtests without research-plan")

    if _has_paper(workspace) and not _exists(workspace, "skeptic-review.md"):
        errors.append(f"{rel}: paper without skeptic-review")

    if _has_promotion(workspace) and not _has_paper(workspace):
        errors.append(f"{rel}: promotion without paper")

    if _exists(workspace, "post-mortem.md") and not (_has_paper(workspace) or _has_promotion(workspace)):
        errors.append(f"{rel}: post-mortem without paper or promotion")

    status = read_status(workspace)
    if status in STATUSES_REQUIRING_EVIDENCE and not has_evidence_links(workspace):
        errors.append(f"{rel}: {IN_SKEPTIC_WITHOUT_EVIDENCE}")

    return errors


def assert_can_mark(workspace: Path, target: str) -> None:
    target = target.strip().lower()
    if target not in THESIS_STATUS_VALUES:
        raise GateError(f"unknown status {target!r}")
    if target in LATER_PHASE_STATUSES:
        raise GateError(PAPER_LIVE_LATER)
    if target not in PHASE2_STATUS_VALUES:
        raise GateError(f"status {target!r} is not available in Phase 2")
    if not _exists(workspace, "intent.md"):
        raise GateError(NO_INTENT)
    current = read_status(workspace) or ThesisStatus.DRAFT.value
    if current == ThesisStatus.REJECTED.value and target != ThesisStatus.REJECTED.value:
        raise GateError(REJECTED_IS_TERMINAL)
    if target == current:
        if target == ThesisStatus.IN_SKEPTIC.value and not has_evidence_links(workspace):
            raise GateError(IN_SKEPTIC_WITHOUT_EVIDENCE)
        return
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise GateError(f"cannot advance {current} → {target}")
    if target in {ThesisStatus.IN_RESEARCH.value, ThesisStatus.IN_SKEPTIC.value} and not _exists(
        workspace, "thesis.md"
    ):
        raise GateError(NO_INTENT)
    if target == ThesisStatus.IN_SKEPTIC.value:
        if not _exists(workspace, "research-plan.md"):
            raise GateError("cannot mark in_skeptic without research-plan")
        if not has_evidence_links(workspace):
            raise GateError(IN_SKEPTIC_WITHOUT_EVIDENCE)
    if target == ThesisStatus.IN_RESEARCH.value and not _exists(workspace, "thesis.md"):
        raise GateError("cannot mark in_research without thesis.md")


def write_status(workspace: Path, status: str) -> None:
    if _exists(workspace, "thesis.md"):
        write_text(workspace / "thesis.md", set_field(read_text(workspace / "thesis.md"), "Status / version", status))
    if _exists(workspace, "intent.md"):
        write_text(workspace / "intent.md", set_field(read_text(workspace / "intent.md"), "Status", status))
    if _exists(workspace, "research-plan.md"):
        text = read_text(workspace / "research-plan.md")
        try:
            write_text(workspace / "research-plan.md", set_field(text, "Status", status))
        except KeyError:
            pass


def advance_status(workspace: Path, target: str) -> str:
    target = target.strip().lower()
    assert_can_mark(workspace, target)
    write_status(workspace, target)
    return target


def assert_independent_skeptic(workspace: Path, reviewer: str) -> None:
    author = read_author_role(workspace).strip()
    if reviewer.strip().lower() == author.lower():
        raise GateError(AUTHOR_CANNOT_BE_SOLE_SKEPTIC)


def run(research_root: Path, templates_root: Path | None) -> int:
    errors: list[str] = []
    if templates_root is not None:
        errors.extend(check_templates(templates_root))
    workspaces = discover_workspaces(research_root)
    for workspace in workspaces:
        errors.extend(check_workspace(workspace))
    if errors:
        print("lifecycle check failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"lifecycle check passed ({len(workspaces)} thesis workspace(s))")
    return 0
