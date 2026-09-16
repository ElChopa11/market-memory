"""lab brief / briefing-worker CLI smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

from mm_briefing_worker import main as worker_main
from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "briefing" / "frozen_day.json"
EXPECTED_PREOPEN = (ROOT / "tests" / "fixtures" / "briefing" / "frozen_preopen.sha256").read_text().strip()


def test_lab_status_mentions_phase3_and_hard_gate(capsys) -> None:
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "Phase 3" in out
    assert "HARD-GATED" in out
    assert "alert-check" in out
    assert "America/New_York" in out


def test_lab_brief_preopen_writes_markdown(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "brief",
            "preopen",
            "--fixture",
            str(FIXTURE),
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
            "--no-db",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "preopen"
    assert payload["session_date"] == "2026-03-10"
    assert payload["content_hash"] == EXPECTED_PREOPEN
    written = tmp_path / "briefs" / "2026" / "03" / "10" / "preopen.md"
    assert written.is_file()
    assert "US Pre-Open Brief" in written.read_text(encoding="utf-8")


def test_lab_alert_check_without_thresholds_does_not_push(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "brief",
            "alert-check",
            "--fixture",
            str(FIXTURE),
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
            "--no-db",
            "--no-thresholds",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["pushed"] is False
    assert payload["reason"] == "threshold_config_required"
    assert not (tmp_path / "briefs").exists()


def test_lab_alert_check_with_thresholds_can_push(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "brief",
            "alert-check",
            "--fixture",
            str(FIXTURE),
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
            "--no-db",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["pushed"] is True
    assert payload["count"] >= 1
    assert (tmp_path / "briefs" / "2026" / "03" / "10" / "alert.md").is_file()


def test_worker_next_lists_dst_transition_fires(capsys) -> None:
    rc = worker_main(["next", "--from", "2026-03-06T00:00:00Z", "--days", "4"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    kinds = {(row["kind"], row["session_date"], row["utc"]) for row in payload["fires"]}
    assert ("preopen", "2026-03-06", "2026-03-06T13:00:00+00:00") in kinds
    assert ("preopen", "2026-03-09", "2026-03-09T12:00:00+00:00") in kinds
