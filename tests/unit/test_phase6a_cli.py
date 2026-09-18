"""lab mesh dry CLI: fixture double-run hashes, kill-desk FAILED."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "phase5d" / "frozen_day.json"


def test_lab_mesh_dry_double_run_identical(tmp_path: Path, capsys) -> None:
    args = [
        "mesh",
        "dry",
        "--fixture",
        str(FIXTURE),
        "--repo-root",
        str(ROOT),
        "--out",
        str(tmp_path),
        "--no-db",
    ]
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["double_run_identical"] is True
    assert first["content_hash"] == first["second_content_hash"]
    assert first["redis"] is False
    assert first["bus"] == "in-memory"
    sha = (tmp_path / "briefs" / "2026-09-18" / "mesh-run.sha256").read_text(encoding="utf-8").strip()
    assert sha == first["content_hash"]
    pack = (tmp_path / "briefs" / "2026-09-18" / "mesh-pack.md").read_text(encoding="utf-8")
    assert "HEADER" in pack


def test_lab_mesh_dry_kill_desk(capsys) -> None:
    rc = main(
        [
            "mesh",
            "dry",
            "--fixture",
            str(FIXTURE),
            "--repo-root",
            str(ROOT),
            "--kill-desk",
            "quant",
            "--no-db",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["desks"]["quant"]["status"] == "FAILED"
    assert payload["desks"]["quant"]["error_class"] == "desk_killed"
    assert payload["status"] == "FAILED"
    assert payload["double_run_identical"] is True


def test_lab_mesh_channels(capsys) -> None:
    assert main(["mesh", "channels", "--repo-root", str(ROOT)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["redis"] is False
    assert payload["bus"] == "postgres-listen-notify"
    assert "coord.assemble" in payload["channels"]
    assert "dq.event" in payload["channels"]


def test_lab_status_mentions_mesh(capsys) -> None:
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "mesh" in out.lower()
    assert "HARD-GATED" in out
    assert "6a" in out or "6b" in out or "NOTIFY" in out
