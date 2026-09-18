"""Phase 6c-5 CLI: lab deliver watchlist --no-send. Never hits live Telegram."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
LOCKED = ROOT / "tests" / "fixtures" / "phase6c4" / "locked_scan.json"


def test_lab_deliver_watchlist_no_send(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "deliver",
            "watchlist",
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
    assert payload["publisher"] == "ops"
    assert payload["desk"] == "research"
    assert payload["no_send"] is True
    assert payload["send"] is False
    assert payload["n_llm_calls"] == 0
    assert payload["watchlist_content_hash"] == payload["content_hash"]
    assert payload["ops_mirror"] is not None
    sha = tmp_path / "research" / "watchlist" / "2026-09-18" / "watchlist.sha256"
    md = tmp_path / "research" / "watchlist" / "2026-09-18" / "watchlist.md"
    telegram = tmp_path / "briefs" / "2026-09-18" / "telegram-payload.json"
    assert sha.is_file()
    assert md.is_file()
    assert telegram.is_file()
    assert sha.read_text(encoding="utf-8").strip() == payload["content_hash"]
    assert "TELEGRAM_BOT_TOKEN" not in telegram.read_text(encoding="utf-8")
    assert "Not a call" in md.read_text(encoding="utf-8")


def test_lab_status_mentions_ops_delivery(capsys) -> None:
    rc = main(["status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "lab deliver" in out
    assert "watchlist" in out.lower()
    assert "Ops publishes" in out or "6c-5" in out
