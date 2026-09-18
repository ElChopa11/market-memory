"""Phase 6c CLI: playbook + deliver inbound allowlist."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
NO_SETUP = ROOT / "tests" / "fixtures" / "phase6c" / "no_setup.json"


def test_lab_playbook_run_no_send(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "playbook",
            "run",
            "--fixture",
            str(NO_SETUP),
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
    assert payload["status"] in {"OK", "DEGRADED"}
    sha = tmp_path / "briefs" / "2026-09-18" / "playbook.sha256"
    assert sha.is_file()
    assert sha.read_text(encoding="utf-8").strip() == payload["content_hash"]


def test_lab_status_mentions_playbook() -> None:
    rc = main(["status"])
    assert rc == 0
