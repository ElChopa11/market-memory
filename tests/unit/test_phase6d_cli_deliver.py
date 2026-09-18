"""Phase 6d CLI: lab deliver listings --no-send. Never hits live Telegram."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
LISTING_DAY = ROOT / "tests" / "fixtures" / "phase6d" / "listing_day.json"


def test_lab_deliver_listings_no_send(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "deliver",
            "listings",
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
    assert payload["publisher"] == "ops"
    assert payload["desk"] == "research"
    assert payload["no_send"] is True
    assert payload["send"] is False
    assert payload["n_llm_calls"] == 0
    assert payload["listings_content_hash"] == payload["content_hash"]
    assert payload["ops_mirror"] is not None
    sha = tmp_path / "research" / "listings" / "2026-09-18" / "listings.sha256"
    md = tmp_path / "research" / "listings" / "2026-09-18" / "listings.md"
    telegram = tmp_path / "briefs" / "2026-09-18" / "telegram-payload.json"
    assert sha.is_file()
    assert md.is_file()
    assert telegram.is_file()
    assert sha.read_text(encoding="utf-8").strip() == payload["content_hash"]
    assert "TELEGRAM_BOT_TOKEN" not in telegram.read_text(encoding="utf-8")
