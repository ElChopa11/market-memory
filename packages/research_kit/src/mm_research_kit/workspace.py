"""Create thesis workspaces from intent. No credentials, no execution imports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from mm_common.enums import ThesisStatus
from mm_common.time import in_ops_tz, utcnow
from mm_research_kit.artifacts import (
    artifact_content_hash,
    copy_template,
    fill_intent,
    fill_research_plan,
    fill_skeptic_review,
    fill_thesis,
    isoformat_now,
    write_text,
)
from mm_research_kit.errors import NO_INTENT, GateError, ResearchKitError
from mm_research_kit.markdown import get_field
from mm_research_kit.thesis_cards import attach_desk_thesis_card

SLUG_RE = re.compile(r"^THESIS-(\d+)$")
DEFAULT_DOD = "Hypothesis, instrument, invalidation, and why-now are written in thesis.md."


@dataclass
class ThesisSpec:
    goal: str
    owner: str
    why_now: str = "no observation yet"
    out_of_scope: str = "live trading; execution; Market Pulse"
    definition_of_done: str = DEFAULT_DOD
    instrument: str = "BTC"
    horizon: str = ""
    deadline: str = ""
    hypothesis: str = ""
    author_role: str = "Research"
    opened_at: str = ""


@dataclass(frozen=True)
class CreatedWorkspace:
    path: Path
    slug: str
    status: str
    year: int
    artifact_git_path: str
    artifact_content_hash: str


def workspace_year(now=None) -> int:
    return in_ops_tz(now or utcnow()).year


def next_thesis_slug(research_root: Path) -> str:
    numbers: list[int] = []
    if research_root.is_dir():
        for path in research_root.rglob("THESIS-*"):
            if not path.is_dir():
                continue
            match = SLUG_RE.fullmatch(path.name)
            if match:
                numbers.append(int(match.group(1)))
    return f"THESIS-{max(numbers, default=0) + 1:04d}"


def find_workspace(research_root: Path, slug_or_path: str) -> Path:
    candidate = Path(slug_or_path)
    if candidate.is_dir() and (candidate / "intent.md").is_file():
        return candidate
    slug = candidate.name if candidate.name.startswith("THESIS-") else slug_or_path
    matches = [path for path in research_root.rglob(slug) if path.is_dir() and path.name == slug]
    if not matches:
        raise FileNotFoundError(f"thesis workspace not found: {slug_or_path}")
    return sorted(matches)[-1]


def spec_from_intent_file(path: Path) -> ThesisSpec:
    if not path.is_file():
        raise GateError(f"{NO_INTENT}: missing {path}")
    text = path.read_text(encoding="utf-8")
    goal = (get_field(text, "Goal (one sentence)") or get_field(text, "Goal") or "").strip()
    if not goal:
        raise GateError(f"{NO_INTENT}: goal is empty")
    owner = (get_field(text, "Owner") or "Research").strip()
    return ThesisSpec(
        goal=goal,
        owner=owner,
        why_now=(get_field(text, "Why now / trigger observation ids") or "no observation yet").strip(),
        out_of_scope=(get_field(text, "Out of scope") or "").strip(),
        definition_of_done=(
            get_field(text, "Definition of done for moving to thesis") or DEFAULT_DOD
        ).strip(),
        instrument=(get_field(text, "Instrument universe (v1 default BTC + ETH perps)") or "BTC").strip(),
        deadline=(get_field(text, "deadline") or "").strip(),
        opened_at=(get_field(text, "opened_at") or "").strip(),
        author_role=owner or "Research",
    )


def git_path(workspace: Path, repo_root: Path) -> str:
    try:
        return workspace.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return workspace.as_posix()


def create_thesis_from_intent(
    *,
    research_root: Path,
    templates_root: Path,
    spec: ThesisSpec | None = None,
    intent_path: Path | None = None,
    repo_root: Path | None = None,
    status: str = ThesisStatus.IN_RESEARCH.value,
) -> CreatedWorkspace:
    """Create a THESIS-XXXX workspace from an intent in one step.

    Writes intent → thesis → research-plan → evidence/links.md → skeptic-review.
    Refuses to write thesis.md unless intent can be produced.
    """
    if intent_path is not None and spec is None:
        spec = spec_from_intent_file(intent_path)
    if spec is None or not spec.goal.strip():
        raise GateError(NO_INTENT)

    workspace: Path | None = None
    slug: str | None = None
    if intent_path is not None:
        parent = intent_path.parent
        if parent.name.startswith("THESIS-") and not (parent / "thesis.md").is_file():
            workspace = parent
            slug = parent.name

    if workspace is None:
        year = workspace_year()
        slug = next_thesis_slug(research_root)
        workspace = research_root / str(year) / slug
        if workspace.exists() and any(workspace.iterdir()):
            raise ResearchKitError(f"workspace already exists: {workspace}")
        workspace.mkdir(parents=True, exist_ok=True)
        year = int(workspace.parent.name) if workspace.parent.name.isdigit() else year
    else:
        year = int(workspace.parent.name) if workspace.parent.name.isdigit() else workspace_year()

    assert slug is not None
    if (workspace / "thesis.md").is_file():
        raise ResearchKitError(f"thesis already exists in {workspace}")

    (workspace / "evidence").mkdir(exist_ok=True)
    opened_at = spec.opened_at or isoformat_now()
    write_text(
        workspace / "intent.md",
        fill_intent(
            copy_template(templates_root, "intent.md", workspace / "intent.md"),
            slug=slug,
            goal=spec.goal.strip(),
            why_now=spec.why_now,
            out_of_scope=spec.out_of_scope,
            definition_of_done=spec.definition_of_done,
            owner=spec.owner,
            opened_at=opened_at,
            deadline=spec.deadline,
            instrument=spec.instrument,
            status=status,
        ),
    )
    if not (workspace / "intent.md").is_file():
        raise GateError(NO_INTENT)

    write_text(
        workspace / "thesis.md",
        fill_thesis(
            copy_template(templates_root, "thesis.md", workspace / "thesis.md"),
            slug=slug,
            status=status,
            author_role=spec.author_role or spec.owner,
            instrument=spec.instrument,
            horizon=spec.horizon,
            hypothesis=spec.hypothesis,
        ),
    )
    attach_desk_thesis_card(
        workspace=workspace,
        templates_root=templates_root,
        instrument=spec.instrument,
        slug=slug,
        status=status,
        author_role=spec.author_role or spec.owner,
        horizon=spec.horizon,
        opened_at=opened_at,
    )
    write_text(
        workspace / "research-plan.md",
        fill_research_plan(
            copy_template(templates_root, "research-plan.md", workspace / "research-plan.md"),
            slug=slug,
            owner=spec.owner,
            status=status,
        ),
    )
    copy_template(templates_root, "evidence-links.md", workspace / "evidence" / "links.md")
    write_text(
        workspace / "skeptic-review.md",
        fill_skeptic_review(
            copy_template(templates_root, "skeptic-review.md", workspace / "skeptic-review.md"),
            slug=slug,
        ),
    )

    root = repo_root or research_root.parent
    return CreatedWorkspace(
        path=workspace,
        slug=slug,
        status=status,
        year=year,
        artifact_git_path=git_path(workspace, root),
        artifact_content_hash=artifact_content_hash(workspace),
    )
