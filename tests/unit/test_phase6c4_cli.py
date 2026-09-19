"""Phase 6c-4 CLI: lab watchlist scan --no-send."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
LOCKED = ROOT / "tests" / "fixtures" / "phase6c4" / "locked_scan.json"


def test_lab_watchlist_scan_no_send(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "watchlist",
            "scan",
            "--fixture",
            str(LOCKED),
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
    assert payload["desk"] == "research"
    assert payload["n"] == 38
    sha = tmp_path / "research" / "watchlist" / "2026-09-18" / "watchlist.sha256"
    md = tmp_path / "research" / "watchlist" / "2026-09-18" / "watchlist.md"
    assert sha.is_file()
    assert md.is_file()
    assert sha.read_text(encoding="utf-8").strip() == payload["content_hash"]
    assert "Not a call" in md.read_text(encoding="utf-8")


def test_lab_status_mentions_watchlist(capsys) -> None:
    rc = main(["status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Watchlist:" in out
    assert "lab watchlist scan" in out
