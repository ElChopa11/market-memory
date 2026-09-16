"""Paper ledger gates: cannot open without invalidation + max loss."""

from __future__ import annotations

from pathlib import Path

import pytest

from mm_paper.errors import PaperGateError
from mm_paper.gates import parse_max_loss, require_invalidation, require_open_fields
from mm_paper.ledger import close_paper_trade, open_paper_trade
from mm_research_kit.evidence import link_evidence
from mm_research_kit.lifecycle import read_status
from mm_research_kit.skeptic import record_skeptic_verdict
from mm_research_kit.workspace import ThesisSpec, create_thesis_from_intent

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates"


def _workspace(tmp_path: Path, *, pass_skeptic: bool = True) -> Path:
    created = create_thesis_from_intent(
        research_root=tmp_path / "research",
        templates_root=TEMPLATES,
        spec=ThesisSpec(goal="BTC funding fade", owner="Research", instrument="BTC"),
        repo_root=tmp_path,
    )
    link_evidence(created.path, observation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV", role="supports")
    if pass_skeptic:
        record_skeptic_verdict(created.path, verdict="pass", reviewer="Skeptic")
    return created.path


def test_require_open_fields_rejects_missing_invalidation_and_max_loss() -> None:
    with pytest.raises(PaperGateError, match="without invalidation"):
        require_invalidation("")
    with pytest.raises(PaperGateError, match="without invalidation"):
        require_open_fields(invalidation="tbd", max_loss="500 USDC")
    with pytest.raises(PaperGateError, match="without max loss"):
        parse_max_loss("")
    with pytest.raises(PaperGateError, match="without max loss"):
        parse_max_loss("n/a")
    with pytest.raises(PaperGateError, match="greater than zero"):
        parse_max_loss("0 USDC")
    text, amount = parse_max_loss("500 USDC")
    assert text == "500 USDC"
    assert amount > 0


def test_open_refuses_without_invalidation(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    with pytest.raises(PaperGateError, match="without invalidation"):
        open_paper_trade(
            research_root=tmp_path / "research",
            templates_root=TEMPLATES,
            repo_root=tmp_path,
            slug=workspace.name,
            size="0.01",
            max_loss="500 USDC",
            invalidation="  ",
        )


def test_open_refuses_without_max_loss(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    with pytest.raises(PaperGateError, match="without max loss"):
        open_paper_trade(
            research_root=tmp_path / "research",
            templates_root=TEMPLATES,
            repo_root=tmp_path,
            slug=workspace.name,
            size="0.01",
            max_loss="",
            invalidation="Close < 60k daily",
        )


def test_open_refuses_without_skeptic_pass(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path, pass_skeptic=False)
    with pytest.raises(PaperGateError, match="skeptic pass"):
        open_paper_trade(
            research_root=tmp_path / "research",
            templates_root=TEMPLATES,
            repo_root=tmp_path,
            slug=workspace.name,
            size="0.01",
            max_loss="500 USDC",
            invalidation="Close < 60k daily",
        )


def test_open_and_close_writes_paper_artifacts(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    record = open_paper_trade(
        research_root=tmp_path / "research",
        templates_root=TEMPLATES,
        repo_root=tmp_path,
        slug=workspace.name,
        size="0.01",
        max_loss="500 USDC",
        invalidation="Close < 60000 on the daily",
        expected_path=["funding mean-reverts in 48h"],
        fill_price="65000",
        mark_price="64980",
    )
    assert record.invalidation
    assert record.max_loss_amount > 0
    assert record.slippage_bps is not None
    assert (workspace / "paper" / f"{record.id}.md").is_file()
    assert (workspace / "paper" / f"{record.id}.json").is_file()
    assert read_status(workspace) == "paper"
    closed = close_paper_trade(
        research_root=tmp_path / "research",
        templates_root=TEMPLATES,
        repo_root=tmp_path,
        slug=workspace.name,
        trade_id=record.id,
        exit_reason="invalidation hit",
        pnl="-120",
        fill_price="59900",
        mark_price="60000",
    )
    assert closed.status == "closed"
    assert closed.exit_reason == "invalidation hit"
    assert closed.pnl is not None
