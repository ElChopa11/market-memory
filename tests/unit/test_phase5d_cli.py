"""lab desk run CLI: --no-send, deterministic content hash."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "phase5d" / "frozen_day.json"


def test_lab_desk_run_all_no_send_is_deterministic(tmp_path: Path, capsys) -> None:
    args = [
        "desk",
        "run",
        "--all",
        "--fixture",
        str(FIXTURE),
        "--repo-root",
        str(ROOT),
        "--out",
        str(tmp_path),
        "--no-send",
        "--no-db",
    ]
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert main(args) == 0
    second = json.loads(capsys.readouterr().out)
    assert first["content_hash"] == second["content_hash"]
    assert first["send"] is False
    assert first["no_send"] is True
    assert (tmp_path / "briefs" / "2026-09-18" / "desk-pack.md").is_file()
    sha = (tmp_path / "briefs" / "2026-09-18" / "desk-run.sha256").read_text(encoding="utf-8").strip()
    assert sha == first["content_hash"]
    pack = (tmp_path / "briefs" / "2026-09-18" / "desk-pack.md").read_text(encoding="utf-8")
    assert "as_of_knowledge" in pack
    assert "Not an order" in pack


def test_lab_desk_run_send_is_rejected(capsys) -> None:
    rc = main(
        [
            "desk",
            "run",
            "--all",
            "--fixture",
            str(FIXTURE),
            "--repo-root",
            str(ROOT),
            "--send",
        ]
    )
    captured = capsys.readouterr()
    blob = captured.out + captured.err
    assert rc == 2
    assert (
        "frozen" in blob.lower()
        or "step 5" in blob.lower()
        or "missing_env" in blob
        or "TELEGRAM_BOT_TOKEN" in blob
        or '"sent": false' in blob.lower()
        or '"sent": false' in blob
    )


def test_lab_status_mentions_desk_run(capsys) -> None:
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "desk run" in out.lower() or "Desk run" in out
    assert "HARD-GATED" in out
    assert "5e" in out or "no-send" in out
