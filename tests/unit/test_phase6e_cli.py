"""Phase 6e CLI: lab scorecard compare --no-send."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
PACKS = ROOT / "tests" / "fixtures" / "phase6e" / "packs.json"


def test_lab_scorecard_compare_no_send(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "scorecard",
            "compare",
            "--fixture",
            str(PACKS),
            "--repo-root",
            str(ROOT),
            "--no-send",
            "--out",
            str(tmp_path),
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["n_llm_calls"] == 0
    assert payload["send"] is False
    assert payload["no_send"] is True
    assert payload["desk"] == "quant"
    assert payload["promote"] is False
    assert payload["decay_watch_enabled"] is False
    sha = tmp_path / "research" / "scorecards" / "2026-09-18" / "scorecard.sha256"
    md = tmp_path / "research" / "scorecards" / "2026-09-18" / "scorecard.md"
    assert sha.is_file()
    assert md.is_file()
    assert sha.read_text(encoding="utf-8").strip() == payload["content_hash"]
    text = md.read_text(encoding="utf-8")
    assert "BRIEF-TAG-20260918" in text
    assert "NOT_COMPARABLE" in text


def test_lab_status_mentions_scorecard(capsys) -> None:
    rc = main(["status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Scorecard:" in out
    assert "lab scorecard compare" in out
    assert "lab queue check" in out
    assert "lab deliver" in out
