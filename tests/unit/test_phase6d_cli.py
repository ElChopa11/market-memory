"""Phase 6d CLI: lab listings scan --no-send."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
LISTING_DAY = ROOT / "tests" / "fixtures" / "phase6d" / "listing_day.json"


def test_lab_listings_scan_no_send(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "listings",
            "scan",
            "--fixture",
            str(LISTING_DAY),
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
    assert payload["promote"] is False
    sha = tmp_path / "research" / "listings" / "2026-09-18" / "listings.sha256"
    md = tmp_path / "research" / "listings" / "2026-09-18" / "listings.md"
    assert sha.is_file()
    assert md.is_file()
    assert sha.read_text(encoding="utf-8").strip() == payload["content_hash"]
    text = md.read_text(encoding="utf-8")
    assert "Not a sixth desk" in text or "listings / IPO" in text.lower() or "listings IPO" in text.lower()
    assert "CRCL" in text


def test_lab_status_mentions_listings(capsys) -> None:
    rc = main(["status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Listings:" in out
    assert "lab listings scan" in out
    assert "lab deliver" in out
