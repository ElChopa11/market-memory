"""IMP-056: heartbeat table, Sydney slot/anchor, known-missed baseline.

Paper only. No Telegram. No C-00x compute.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from mm_desks.completions import completion_filename
from mm_desks.scheduler import (
    WRONG_ANCHOR_REASON,
    load_catalog,
    load_known_missed_baseline,
    miss_sweep,
    parse_baseline_before,
    scheduled_slot,
    stamp_fire,
    sydney_calendar_date,
)
from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
UTC = timezone.utc
MISS_CLOCK = ROOT / "tests" / "fixtures" / "scheduler" / "miss_clock.yaml"


def test_sunday_sydney_morning_is_wrong_anchor_not_late() -> None:
    catalog = load_catalog(ROOT)
    routine = catalog.by_id()["grok.sydney_morning"]
    # Sun 2026-09-20 06:30 AEST == 2026-09-19T20:30:00Z
    fired = datetime(2026, 9, 19, 20, 30, tzinfo=UTC)
    record = stamp_fire(routine, fired_at=fired, run_id="sunday-dry-run")
    assert record.scheduled_anchor_ts == datetime(2026, 9, 19, 20, 30, tzinfo=UTC)
    assert record.delta_seconds == 0
    assert record.status == "wrong_anchor"
    assert record.status != "late"
    assert record.reason == WRONG_ANCHOR_REASON
    assert completion_filename(record) == "grok.sydney_morning__20260919T203000Z.json"
    weekday_ok = scheduled_slot(routine, fired)[1]
    assert weekday_ok is False
    # Must not reuse Friday 18 Sep 06:30 AEST (2026-09-17T20:30:00Z).
    assert not record.scheduled_anchor_ts.isoformat().startswith("2026-09-17T20:30:00")


def test_cli_sunday_heartbeat_does_not_write_friday_filename(tmp_path: Path, capsys) -> None:
    dest = tmp_path / "completions"
    rc = main(
        [
            "schedule",
            "heartbeat",
            "--routine-id",
            "grok.sydney_morning",
            "--fired-at",
            "2026-09-19T20:30:00Z",
            "--run-id",
            "sunday-dry-run",
            "--exit-status",
            "0",
            "--repo-root",
            str(ROOT),
            "--completions-dir",
            str(dest),
            "--no-db",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "wrong_anchor"
    assert payload["scheduled_anchor_ts"].startswith("2026-09-19T20:30:00")
    assert payload["delta_seconds"] == 0
    names = sorted(p.name for p in dest.glob("*.json"))
    assert names == ["grok.sydney_morning__20260919T203000Z.json"]
    assert "grok.sydney_morning__20260917T203000Z.json" not in names


def test_wrong_anchor_does_not_cover_friday_slot() -> None:
    catalog = load_catalog(ROOT)
    routine = catalog.by_id()["grok.sydney_morning"]
    sunday = stamp_fire(
        routine,
        fired_at=datetime(2026, 9, 19, 20, 30, tzinfo=UTC),
        run_id="sunday-dry-run",
    )
    slim = catalog.__class__(
        routines=(routine,),
        late_after_seconds=300,
        miss_after_seconds=900,
        lookback_days=7,
        lab_timezone="Australia/Sydney",
    )
    now = datetime(2026, 9, 20, 1, 0, tzinfo=UTC)  # Sun 11:00 AEST; Friday 06:30 closed
    result = miss_sweep(slim, (sunday,), now, lookback_days=7)
    friday = datetime(2026, 9, 17, 20, 30, tzinfo=UTC)
    assert any(
        row.routine_id == "grok.sydney_morning" and row.scheduled_anchor_ts == friday for row in result.misses
    )
    assert result.wrong_anchor
    assert result.wrong_anchor[0]["status"] == "wrong_anchor"


def test_weekday_on_anchor_still_ok() -> None:
    catalog = load_catalog(ROOT)
    routine = catalog.by_id()["grok.sydney_morning"]
    fired = datetime(2026, 9, 17, 20, 32, tzinfo=UTC)  # Fri 06:32 AEST
    record = stamp_fire(routine, fired_at=fired, run_id="friday-ok")
    assert record.status == "ok"
    assert record.delta_seconds == 120
    assert record.scheduled_anchor_ts.isoformat().startswith("2026-09-17T20:30:00")


def test_baseline_before_today_labels_history_and_leaves_monday_visible(tmp_path: Path, capsys) -> None:
    dest = tmp_path / "baseline.yaml"
    # Monday 21 Sep 2026 09:00 AEST — Monday 06:30 is closed; pre-Mon windows exist.
    now = "2026-09-20T23:00:00Z"
    rc = main(
        [
            "schedule",
            "miss-check",
            "--repo-root",
            str(ROOT),
            "--now",
            now,
            "--no-db",
            "--lookback-days",
            "14",
            "--baseline-before",
            "today",
            "--baseline-file",
            str(dest),
            "--out",
            str(tmp_path / "incidents"),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert dest.is_file()
    baseline = load_known_missed_baseline(dest)
    assert baseline
    assert payload["n_known_missed"] == len(baseline)
    assert payload["baseline_before"] == "2026-09-21"
    assert sydney_calendar_date(datetime(2026, 9, 20, 23, 0, tzinfo=UTC)).isoformat() == "2026-09-21"
    monday_anchors = [
        row
        for row in payload["misses"]
        if row["scheduled_anchor_ts"].startswith("2026-09-20T20:30:00")
        or row["scheduled_anchor_ts"].startswith("2026-09-20T22:00:00")
    ]
    assert monday_anchors, payload["misses"]
    assert payload["n_missed"] == len(payload["misses"])
    assert payload["n_missed"] < payload["n_known_missed"]
    assert rc == 1
    text = dest.read_text(encoding="utf-8")
    assert "known-missed" in text
    assert "labeled, not deleted" in text.lower() or "labeled, not deleted" in payload.get("notes", "").lower() or "History is labeled" in text

    capsys.readouterr()
    rc2 = main(
        [
            "schedule",
            "miss-check",
            "--repo-root",
            str(ROOT),
            "--now",
            now,
            "--no-db",
            "--lookback-days",
            "14",
            "--baseline-file",
            str(dest),
            "--out",
            str(tmp_path / "incidents-reload"),
        ]
    )
    reload_payload = json.loads(capsys.readouterr().out)
    assert reload_payload["n_known_missed"] >= payload["n_known_missed"]
    assert reload_payload["n_missed"] == payload["n_missed"]
    assert rc2 == 1


def test_parse_baseline_before_today_is_sydney_date() -> None:
    now = datetime(2026, 9, 20, 23, 0, tzinfo=UTC)
    assert parse_baseline_before("today", now).isoformat() == "2026-09-21"
    assert parse_baseline_before("2026-09-21", now).isoformat() == "2026-09-21"


def test_fixture_clock_stays_isolated_from_baseline(capsys) -> None:
    rc = main(
        [
            "schedule",
            "miss-check",
            "--fixture",
            str(MISS_CLOCK),
            "--now",
            "2026-09-19T09:49:00Z",
            "--no-db",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert payload["n_known_missed"] == 0
    assert payload["n_missed"] >= 1
