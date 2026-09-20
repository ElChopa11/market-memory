"""IMP-056: heartbeat table, Sydney slot/anchor, known-missed baseline.

Wrong-anchor writes NO completion row. Paper only. No Telegram. No C-00x compute.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mm_desks.completions import load_disk_completions
from mm_memory.migrate import alembic_head
from mm_desks.scheduler import (
    WRONG_ANCHOR_REASON,
    WrongAnchorError,
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


def test_sunday_sydney_morning_refuses_stamp_no_row() -> None:
    catalog = load_catalog(ROOT)
    routine = catalog.by_id()["grok.sydney_morning"]
    # Sun 2026-09-20 06:30 AEST == 2026-09-19T20:30:00Z
    fired = datetime(2026, 9, 19, 20, 30, tzinfo=UTC)
    weekday_ok = scheduled_slot(routine, fired)[1]
    assert weekday_ok is False
    with pytest.raises(WrongAnchorError) as exc:
        stamp_fire(routine, fired_at=fired, run_id="sunday-dry-run")
    payload = exc.value.as_public_dict()
    assert payload["error"] == "wrong_anchor"
    assert payload["wrote"] is False
    assert payload["reason"] == WRONG_ANCHOR_REASON
    assert payload["local_weekday"] == "Sun"
    assert "late" not in payload["error"]
    # Must not walk back to Friday 18 Sep 06:30 AEST.
    assert not str(payload.get("would_be_anchor_ts") or "").startswith("2026-09-17T20:30:00")


def test_cli_sunday_heartbeat_writes_no_completion_row(tmp_path: Path, capsys) -> None:
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
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 2
    assert payload["error"] == "wrong_anchor"
    assert payload["wrote"] is False
    assert payload["status"] != "late" if "status" in payload else True
    assert list(dest.glob("*.json")) == []


def test_old_friday_keyed_sunday_stamp_is_skipped_and_friday_stays_miss(tmp_path: Path) -> None:
    dest = tmp_path / "completions"
    dest.mkdir()
    (dest / "grok.sydney_morning__20260917T203000Z.json").write_text(
        json.dumps(
            {
                "routine_id": "grok.sydney_morning",
                "run_id": "sunday-dry-run",
                "scheduled_anchor_ts": "2026-09-17T20:30:00+00:00",
                "fired_at_ts": "2026-09-19T20:30:00+00:00",
                "delta_seconds": 172800,
                "status": "late",
                "as_of_knowledge": "2026-09-19T20:30:00+00:00",
                "source": "lab.cli",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    catalog = load_catalog(ROOT)
    disk = load_disk_completions(dest, catalog=catalog)
    assert disk == []
    routine = catalog.by_id()["grok.sydney_morning"]
    slim = catalog.__class__(
        routines=(routine,),
        late_after_seconds=300,
        miss_after_seconds=900,
        lookback_days=7,
        lab_timezone="Australia/Sydney",
    )
    now = datetime(2026, 9, 20, 1, 0, tzinfo=UTC)
    result = miss_sweep(slim, disk, now, lookback_days=7)
    friday = datetime(2026, 9, 17, 20, 30, tzinfo=UTC)
    assert any(
        row.routine_id == "grok.sydney_morning" and row.scheduled_anchor_ts == friday for row in result.misses
    )


def test_weekday_on_anchor_still_ok() -> None:
    catalog = load_catalog(ROOT)
    routine = catalog.by_id()["grok.sydney_morning"]
    fired = datetime(2026, 9, 17, 20, 32, tzinfo=UTC)  # Fri 06:32 AEST
    record = stamp_fire(routine, fired_at=fired, run_id="friday-ok")
    assert record.status == "ok"
    assert record.delta_seconds == 120
    assert record.scheduled_anchor_ts.isoformat().startswith("2026-09-17T20:30:00")


def test_failed_cli_on_scheduled_day_still_writes_a_fire(tmp_path: Path, capsys) -> None:
    dest = tmp_path / "completions"
    rc = main(
        [
            "schedule",
            "heartbeat",
            "--routine-id",
            "grok.sydney_morning",
            "--fired-at",
            "2026-09-17T20:32:00Z",
            "--exit-status",
            "2",
            "--repo-root",
            str(ROOT),
            "--completions-dir",
            str(dest),
            "--no-db",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["exit_status"] == 2
    assert payload["status"] == "ok"
    assert payload.get("wrote") is not False
    assert list(dest.glob("*.json"))


def test_baseline_before_today_labels_history_and_leaves_monday_visible(tmp_path: Path, capsys) -> None:
    dest = tmp_path / "baseline.yaml"
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
    assert "History is labeled" in text

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


def test_alembic_revision_ids_fit_version_num_varchar32() -> None:
    """Alembic version_num is varchar(32). The 0012 long id broke `lab migrate` in CI."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from mm_memory.migrate import MIGRATIONS_DIR

    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    script = ScriptDirectory.from_config(cfg)
    for rev in script.walk_revisions():
        assert len(rev.revision) <= 32, rev.revision
    head = alembic_head()
    assert head == "0012_heartbeat_if_not_exists"
    assert len(head) <= 32
