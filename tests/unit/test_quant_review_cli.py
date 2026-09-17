"""CLI smoke for lab quant-review."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]


def test_lab_quant_review_writes_board(tmp_path: Path, capsys) -> None:
    research = tmp_path / "research"
    rc = main(
        [
            "quant-review",
            "--fixture",
            str(ROOT / "tests/fixtures/quant_review/watchlist_snapshot_20260917.yaml"),
            "--universe",
            str(ROOT / "config/quant_review_universe.yaml"),
            "--quant-pack",
            str(ROOT / "research/queue/quant-20260917"),
            "--repo-root",
            str(ROOT),
            "--research-root",
            str(research),
            "--as-of",
            "2026-09-17T02:42:00Z",
            "--review-date",
            "2026-09-17",
            "--no-db",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    board = Path(payload["board"])
    assert board.is_file()
    text = board.read_text(encoding="utf-8")
    assert "Research only. Not a trade instruction, allocation decision, or execution approval." in text
    assert "MAKE" not in text
    assert "active call" not in text.lower()
    assert "buy" not in text.lower().split()
    assert "sell" not in text.lower().split()
    assert payload["card_count"] == 36
    assert (research / "quant" / "2026-09-17" / "cards" / "BTC.md").is_file()
    assert (research / "quant" / "2026-09-17" / "cards" / "CRCL.md").is_file()
    assert payload["verdicts"]["CRCL"] != "RESEARCH_PRIORITY"


def test_lab_quant_review_empty_snapshot_insufficient(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "quant-review",
            "--universe",
            str(ROOT / "config/quant_review_universe.yaml"),
            "--repo-root",
            str(ROOT),
            "--research-root",
            str(tmp_path / "research"),
            "--as-of",
            "2026-09-17T02:42:00Z",
            "--review-date",
            "2099-01-01",
            "--no-db",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["card_count"] == 36
    assert set(payload["verdicts"].values()) == {"INSUFFICIENT_DATA"}
