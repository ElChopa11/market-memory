"""Phase 2 research_kit: workspace creation, gates, evidence, skeptic, boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from mm_research_kit.errors import GateError, IN_SKEPTIC_WITHOUT_EVIDENCE, NO_INTENT
from mm_research_kit.evidence import has_evidence_links, link_evidence, load_evidence_links
from mm_research_kit.lifecycle import advance_status, check_workspace, read_status
from mm_research_kit.markdown import get_field
from mm_research_kit.skeptic import open_skeptic_review, record_skeptic_verdict
from mm_research_kit.workspace import ThesisSpec, create_thesis_from_intent, spec_from_intent_file

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates"
RESEARCH_KIT_SRC = ROOT / "packages" / "research_kit" / "src" / "mm_research_kit"
FORBIDDEN_IMPORTS = {
    "mm_execution",
    "mm_paper",
    "mm_risk",
    "mm_briefing",
    "mm_backtest",
    "mm_unicorn",
    "mm_ingest",
    "mm_memory",
}
FORBIDDEN_SNIPPETS = (
    "private_key",
    "API_WALLET",
    "hl_trade",
    "sign_l1_action",
    "submit_order",
    "wallet.json",
)


def _create(tmp_path: Path, **kwargs) -> Path:
    spec = ThesisSpec(
        goal=kwargs.get("goal", "Funding mean-reversion after crowded BTC longs"),
        owner=kwargs.get("owner", "Research"),
        why_now=kwargs.get("why_now", "01ARZ3NDEKTSV4RRFFQ69G5FAV"),
        instrument=kwargs.get("instrument", "BTC"),
        horizon=kwargs.get("horizon", "5d"),
        hypothesis=kwargs.get("hypothesis", "Crowded longs unwind when funding spikes."),
    )
    created = create_thesis_from_intent(
        research_root=tmp_path / "research",
        templates_root=TEMPLATES,
        spec=spec,
        repo_root=tmp_path,
    )
    return created.path


def _imported_top_levels(root: Path) -> set[str]:
    names: set[str] = set()
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
    return names


def test_research_kit_does_not_import_execution_or_memory() -> None:
    imported = _imported_top_levels(RESEARCH_KIT_SRC)
    assert not (imported & FORBIDDEN_IMPORTS)


def test_research_kit_source_has_no_credential_surface() -> None:
    blob = "\n".join(path.read_text(encoding="utf-8") for path in RESEARCH_KIT_SRC.rglob("*.py"))
    for snippet in FORBIDDEN_SNIPPETS:
        assert snippet not in blob, snippet


def test_create_thesis_from_intent_one_command(tmp_path: Path) -> None:
    workspace = _create(tmp_path)
    assert workspace.name == "THESIS-0001"
    assert (workspace / "intent.md").is_file()
    assert (workspace / "thesis.md").is_file()
    assert (workspace / "research-plan.md").is_file()
    assert (workspace / "evidence" / "links.md").is_file()
    assert (workspace / "skeptic-review.md").is_file()
    assert get_field((workspace / "intent.md").read_text(encoding="utf-8"), "Goal (one sentence)")
    assert read_status(workspace) == "in_research"
    assert check_workspace(workspace) == []
    assert not has_evidence_links(workspace)


def test_cannot_create_thesis_without_intent(tmp_path: Path) -> None:
    with pytest.raises(GateError, match="cannot create/mark thesis without intent"):
        create_thesis_from_intent(
            research_root=tmp_path / "research",
            templates_root=TEMPLATES,
            spec=ThesisSpec(goal="  ", owner="Research"),
            repo_root=tmp_path,
        )


def test_create_from_existing_intent_file(tmp_path: Path) -> None:
    intent = tmp_path / "draft-intent.md"
    intent.write_text((TEMPLATES / "intent.md").read_text(encoding="utf-8"), encoding="utf-8")
    from mm_research_kit.markdown import set_field

    text = intent.read_text(encoding="utf-8")
    text = set_field(text, "Goal (one sentence)", "ETH funding fade")
    text = set_field(text, "Owner", "Research")
    intent.write_text(text, encoding="utf-8")
    spec = spec_from_intent_file(intent)
    created = create_thesis_from_intent(
        research_root=tmp_path / "research",
        templates_root=TEMPLATES,
        spec=spec,
        intent_path=intent,
        repo_root=tmp_path,
    )
    assert created.slug == "THESIS-0001"
    assert "ETH funding fade" in (created.path / "intent.md").read_text(encoding="utf-8")


def test_cannot_mark_in_skeptic_without_evidence(tmp_path: Path) -> None:
    workspace = _create(tmp_path)
    with pytest.raises(GateError, match="cannot mark in_skeptic without evidence links"):
        advance_status(workspace, "in_skeptic")
    with pytest.raises(GateError, match="cannot mark in_skeptic without evidence links"):
        open_skeptic_review(workspace, reviewer="Skeptic")


def test_link_evidence_then_in_skeptic_and_reject_retained(tmp_path: Path) -> None:
    workspace = _create(tmp_path)
    link_evidence(workspace, observation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV", role="supports", notes="funding spike")
    assert has_evidence_links(workspace)
    assert load_evidence_links(workspace)[0].observation_id == "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    open_skeptic_review(workspace, reviewer="Skeptic")
    assert read_status(workspace) == "in_skeptic"
    assert check_workspace(workspace) == []
    status = record_skeptic_verdict(
        workspace,
        verdict="reject",
        reviewer="Skeptic",
        findings="Invalidation is circular.",
    )
    assert status == "rejected"
    assert read_status(workspace) == "rejected"
    assert workspace.exists()
    assert (workspace / "thesis.md").is_file()
    assert check_workspace(workspace) == []
    with pytest.raises(GateError, match="learning records"):
        advance_status(workspace, "in_research")


def test_skeptic_pass_and_revise(tmp_path: Path) -> None:
    workspace = _create(tmp_path)
    link_evidence(workspace, observation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV", role="context")
    record_skeptic_verdict(workspace, verdict="pass", reviewer="Skeptic")
    assert read_status(workspace) == "in_skeptic"
    record_skeptic_verdict(workspace, verdict="revise", reviewer="Skeptic")
    assert read_status(workspace) == "in_research"


def test_author_cannot_be_sole_skeptic(tmp_path: Path) -> None:
    workspace = _create(tmp_path)
    link_evidence(workspace, observation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV", role="supports")
    with pytest.raises(GateError, match="not the sole skeptic"):
        open_skeptic_review(workspace, reviewer="Research")


def test_paper_blocked_until_ready_and_live_still_blocked(tmp_path: Path) -> None:
    workspace = _create(tmp_path)
    with pytest.raises(GateError, match="cannot advance"):
        advance_status(workspace, "paper")
    with pytest.raises(GateError, match="later phase"):
        advance_status(workspace, "live")
    link_evidence(workspace, observation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV", role="supports")
    record_skeptic_verdict(workspace, verdict="pass", reviewer="Skeptic")
    with pytest.raises(GateError, match="invalidation"):
        advance_status(workspace, "paper")


def test_in_skeptic_constants_used() -> None:
    assert "in_skeptic" in IN_SKEPTIC_WITHOUT_EVIDENCE
    assert "intent" in NO_INTENT
