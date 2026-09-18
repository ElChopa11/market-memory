"""Phase 6f CLI: lab decay watch --no-send."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
MATCH = ROOT / "tests" / "fixtures" / "phase6f" / "match.json"
MISMATCH = ROOT / "tests" / "fixtures" / "phase6f" / "mismatch.json"


def test_lab_decay_watch_no_send(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "decay",
            "watch",
            "--fixture",
            str(MATCH),
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
    assert payload["decay_watch_enabled"] is True
    assert payload["overall"] == "MATCH"
    sha = tmp_path / "research" / "decay" / "2026-09-18" / "decay.sha256"
    md = tmp_path / "research" / "decay" / "2026-09-18" / "decay.md"
    assert sha.is_file()
    assert md.is_file()
    assert sha.read_text(encoding="utf-8").strip() == payload["content_hash"]
    text = md.read_text(encoding="utf-8")
    assert "MATCH" in text
    assert "decay" in text.lower()


def test_lab_decay_watch_refuses_waiver(capsys) -> None:
    rc = main(
        [
            "decay",
            "watch",
            "--fixture",
            str(MATCH),
            "--repo-root",
            str(ROOT),
            "--waive",
        ]
    )
    err = capsys.readouterr().err
    assert rc == 2
    assert "waive" in err.lower() or "refuses" in err.lower()


def test_lab_status_mentions_decay(capsys) -> None:
    rc = main(["status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Decay:" in out
    assert "lab decay watch" in out
    assert "lab deliver" in out
