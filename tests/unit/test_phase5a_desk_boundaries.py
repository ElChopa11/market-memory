"""Phase 5a docs + skeletons + queue hygiene."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_phase5a_docs_and_skeletons_exist() -> None:
    for rel in (
        "ADR/0002-desk-delivery-architecture.md",
        "docs/runbooks/desks.md",
        "templates/output-contract.md",
        "ops/plans/IMP-009-phase5a-desk-boundaries.md",
        "ops/plans/IMP-010-phase5b-polygon-hl-structure.md",
        "scripts/check_import_boundaries.py",
        "packages/desks/src/mm_desks/crypto.py",
        "packages/desks/src/mm_desks/equities.py",
        "packages/quant/src/mm_quant/factors.py",
        "packages/delivery/src/mm_delivery/__init__.py",
    ):
        assert (ROOT / rel).is_file(), rel


def test_agents_and_charters_encode_tiers_and_escalation() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    charters = (ROOT / "ops" / "desk-charters.md").read_text(encoding="utf-8")
    for text in (agents, charters):
        assert "Tier 0" in text or "**0 Principal**" in text or "0 | Principal" in text
        assert "3a" in text
        assert "3b" in text
        assert "no self-approve" in text.lower()
        assert "FAIL" in text
        assert "BLOCK" in text
    assert "Intel" in agents
    assert "Paper Ledger" in agents
    assert "Risk BLOCK" in agents


def test_queue_marks_008_done_009_landed() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    assert "IMP-008" in queue
    assert "IMP-009" in queue
    assert "IMP-010" in queue
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-008" in line and "DONE" in line for line in board_lines)
    assert any("IMP-009" in line and "DONE" in line for line in board_lines)
    assert "Polygon" in queue


def test_readme_phase5_in_progress() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Phase 5" in readme
    assert "5a" in readme


def test_adr0002_defers_delivery_and_5b() -> None:
    adr = (ROOT / "ADR" / "0002-desk-delivery-architecture.md").read_text(encoding="utf-8")
    assert "5e" in adr
    assert "Polygon" in adr
    assert "Telegram" in adr
    assert "not implemented" in adr.lower() or "Defer" in adr
