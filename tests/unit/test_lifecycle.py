"""Lifecycle checker: refuse thesis without intent."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts" / "check_lifecycle.py"


def _run(research: Path, *, skip_templates: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(CHECKER), "--research-root", str(research)]
    if skip_templates:
        cmd.append("--skip-templates")
    else:
        cmd.extend(["--templates-root", str(ROOT / "templates")])
    return subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=ROOT)


def test_empty_research_passes(tmp_path: Path) -> None:
    research = tmp_path / "research"
    research.mkdir()
    completed = _run(research)
    assert completed.returncode == 0, completed.stderr


def test_refuses_thesis_without_intent(tmp_path: Path) -> None:
    workspace = tmp_path / "research" / "2026" / "THESIS-0001"
    workspace.mkdir(parents=True)
    (workspace / "thesis.md").write_text("# Thesis\n", encoding="utf-8")
    completed = _run(tmp_path / "research")
    assert completed.returncode != 0
    assert "thesis without intent" in completed.stderr


def test_intent_then_thesis_passes(tmp_path: Path) -> None:
    workspace = tmp_path / "research" / "2026" / "THESIS-0001"
    workspace.mkdir(parents=True)
    (workspace / "intent.md").write_text("# Intent\n", encoding="utf-8")
    (workspace / "thesis.md").write_text("# Thesis\n", encoding="utf-8")
    completed = _run(tmp_path / "research")
    assert completed.returncode == 0, completed.stderr


def test_paper_without_skeptic_fails(tmp_path: Path) -> None:
    workspace = tmp_path / "research" / "2026" / "THESIS-0001"
    workspace.mkdir(parents=True)
    (workspace / "intent.md").write_text("# Intent\n", encoding="utf-8")
    (workspace / "thesis.md").write_text("# Thesis\n", encoding="utf-8")
    (workspace / "research-plan.md").write_text("# Plan\n", encoding="utf-8")
    (workspace / "paper-trade.md").write_text("# Paper\n", encoding="utf-8")
    completed = _run(tmp_path / "research")
    assert completed.returncode != 0
    assert "paper without skeptic-review" in completed.stderr


def test_repo_research_tree_passes() -> None:
    completed = _run(ROOT / "research")
    assert completed.returncode == 0, completed.stderr


def test_in_skeptic_without_evidence_links_fails(tmp_path: Path) -> None:
    workspace = tmp_path / "research" / "2026" / "THESIS-0001"
    workspace.mkdir(parents=True)
    (workspace / "intent.md").write_text("# Intent\n- **Status:** in_skeptic\n", encoding="utf-8")
    (workspace / "thesis.md").write_text("# Thesis\n- **Status / version:** in_skeptic\n", encoding="utf-8")
    (workspace / "research-plan.md").write_text("# Plan\n", encoding="utf-8")
    completed = _run(tmp_path / "research")
    assert completed.returncode != 0
    assert "cannot mark in_skeptic without evidence links" in completed.stderr


def test_in_skeptic_with_evidence_links_passes(tmp_path: Path) -> None:
    workspace = tmp_path / "research" / "2026" / "THESIS-0001"
    workspace.mkdir(parents=True)
    (workspace / "intent.md").write_text("# Intent\n- **Status:** in_skeptic\n", encoding="utf-8")
    (workspace / "thesis.md").write_text("# Thesis\n- **Status / version:** in_skeptic\n", encoding="utf-8")
    (workspace / "research-plan.md").write_text("# Plan\n", encoding="utf-8")
    evidence = workspace / "evidence"
    evidence.mkdir()
    (evidence / "links.md").write_text(
        "| observation_id | role | notes | linked_at |\n"
        "| --- | --- | --- | --- |\n"
        "| 01ARZ3NDEKTSV4RRFFQ69G5FAV | supports | crowding | 2026-09-16T00:00:00+00:00 |\n",
        encoding="utf-8",
    )
    (workspace / "skeptic-review.md").write_text("# Skeptic\n- **Verdict:** pass | revise | reject\n", encoding="utf-8")
    completed = _run(tmp_path / "research")
    assert completed.returncode == 0, completed.stderr


def test_rejected_thesis_remains_a_learning_record(tmp_path: Path) -> None:
    workspace = tmp_path / "research" / "2026" / "THESIS-0001"
    workspace.mkdir(parents=True)
    (workspace / "intent.md").write_text("# Intent\n- **Status:** rejected\n", encoding="utf-8")
    (workspace / "thesis.md").write_text("# Thesis\n- **Status / version:** rejected\n", encoding="utf-8")
    completed = _run(tmp_path / "research")
    assert completed.returncode == 0, completed.stderr
    assert workspace.is_dir()
    assert (workspace / "thesis.md").is_file()
