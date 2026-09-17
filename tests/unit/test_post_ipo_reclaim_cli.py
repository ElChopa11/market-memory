"""CLI smoke for lab equities reclaim-screen."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]


def test_lab_equities_reclaim_screen_writes_artifact(tmp_path: Path, capsys) -> None:
    research = tmp_path / "research"
    rc = main(
        [
            "equities",
            "reclaim-screen",
            "--fixture",
            str(ROOT / "tests/fixtures/equities/post_ipo_reclaim_snapshot.yaml"),
            "--universe",
            str(ROOT / "config/equities/post_ipo_reclaim.yaml"),
            "--repo-root",
            str(ROOT),
            "--research-root",
            str(research),
            "--as-of",
            "2026-09-17T02:42:00Z",
            "--screen-date",
            "2026-09-17",
            "--no-db",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    screen = Path(payload["screen"])
    assert screen.is_file()
    text = screen.read_text(encoding="utf-8")
    assert "Informational research triage only" in text
    assert "Principal gate still required" in text
    assert "MAKE" not in text
    assert "active call" not in text.lower()
    assert payload["row_count"] == 2
    assert payload["verdicts"]["CRCL"] != "RESEARCH_PRIORITY"
    assert payload["verdicts"]["HOOD"] != "RESEARCH_PRIORITY"
    assert payload["data_quality"]["CRCL"] in {"fresh", "stale", "partial", "unavailable"}
    assert (research / "screens" / "post-ipo-reclaim" / "2026-09-17.md").is_file()
    assert (research / "screens" / "post-ipo-reclaim" / "2026-09-17.meta.json").is_file()


def test_lab_equities_reclaim_screen_empty_snapshot_unavailable(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "equities",
            "reclaim-screen",
            "--universe",
            str(ROOT / "config/equities/post_ipo_reclaim.yaml"),
            "--repo-root",
            str(ROOT),
            "--research-root",
            str(tmp_path / "research"),
            "--as-of",
            "2026-09-17T02:42:00Z",
            "--screen-date",
            "2099-01-01",
            "--no-db",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["row_count"] == 2
    assert set(payload["verdicts"].values()) == {"INSUFFICIENT_DATA"}
    assert set(payload["data_quality"].values()) == {"unavailable"}


def test_lab_equities_without_subcommand_is_usage() -> None:
    rc = main(["equities"])
    assert rc == 2
