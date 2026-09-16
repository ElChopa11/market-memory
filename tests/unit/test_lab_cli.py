"""CLI smoke: lab status stays hard-gated."""

from __future__ import annotations

from mm_lab_cli.cli import main


def test_lab_status_mentions_phase1_and_hard_gate(capsys) -> None:
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "Phase 1" in out
    assert "HARD-GATED" in out
    assert "ingested_at" in out
