"""IMP-039 CLI: lab base-rate compute --no-db."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "tests" / "fixtures" / "phase1_base_rates" / "panel.json"


def test_lab_base_rate_compute_no_db(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "base-rate",
            "compute",
            "--fixture",
            str(PANEL),
            "--repo-root",
            str(ROOT),
            "--no-db",
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
    assert payload["no_db"] is True
    assert payload["desk"] == "quant"
    assert payload["promote"] is False
    assert payload["sizing"] is False
    assert payload["scan_gate"] is False
    assert payload["paper_only"] is True
    assert payload["params_hash"]
    assert payload["content_hash"]
    assert payload["persisted_ids"] == []
    day = tmp_path / "research" / "quant" / "base-rates" / "2026-09-19"
    sha = day / "unconditional.sha256"
    md = day / "unconditional.md"
    js = day / "unconditional.json"
    assert sha.is_file()
    assert md.is_file()
    assert js.is_file()
    assert sha.read_text(encoding="utf-8").strip() == payload["content_hash"]
    text = md.read_text(encoding="utf-8")
    assert "dip_touch" in text
    assert "zone_boundary_touch" in text
    assert "pullback_ema_touch" in text
    assert "C-001" in text
    assert "C-002" in text
    assert "C-003" in text
    assert "DO NOT SIZE" in text
    assert "buy" not in text.lower()
    assert "sell" not in text.lower()


def test_lab_status_mentions_base_rate(capsys) -> None:
    rc = main(["status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Base rates:" in out
    assert "lab base-rate compute" in out


def test_deterministic_content_hash(tmp_path: Path, capsys) -> None:
    args = [
        "base-rate",
        "compute",
        "--fixture",
        str(PANEL),
        "--repo-root",
        str(ROOT),
        "--no-db",
        "--out",
        str(tmp_path / "a"),
    ]
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)["content_hash"]
    assert main(args[:-1] + [str(tmp_path / "b")]) == 0
    second = json.loads(capsys.readouterr().out)["content_hash"]
    assert first == second
