"""IMP-046 Hybrid Step 4: Hive → lab CLI writes completion rows the miss detector can see.

Fixture clock. No live Telegram. Failed CLI run is a fire, not a miss.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from mm_desks.completions import load_disk_completions
from mm_desks.scheduler import load_fixture, miss_sweep
from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
CI_CLOCK = ROOT / "tests" / "fixtures" / "scheduler" / "ci_clock.yaml"
HIVE_CLOCK = ROOT / "tests" / "fixtures" / "scheduler" / "hive_fire_clock.yaml"
BRIEF_FIXTURE = ROOT / "tests" / "fixtures" / "briefing" / "frozen_day.json"
PACK_MD = ROOT / "tests" / "fixtures" / "phase5e" / "desk-pack.md"
UTC = timezone.utc


def _rows(dest: Path) -> list[dict]:
    out = []
    if not dest.is_dir():
        return out
    for path in sorted(dest.glob("*.json")):
        out.append(json.loads(path.read_text(encoding="utf-8")))
    return out


def test_cli_heartbeat_writes_completion_row_on_fixture_clock(tmp_path: Path, capsys) -> None:
    dest = tmp_path / "completions"
    rc = main(
        [
            "schedule",
            "heartbeat",
            "--routine-id",
            "grok.sydney_morning",
            "--fired-at",
            "2026-09-17T20:32:00Z",
            "--run-id",
            "hive-sydney-morning-fixture",
            "--exit-status",
            "0",
            "--payload-path",
            "briefs/2026-09-18/us-pre-market.md",
            "--cli",
            "lab brief preopen",
            "--repo-root",
            str(ROOT),
            "--completions-dir",
            str(dest),
            "--no-db",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["routine_id"] == "grok.sydney_morning"
    assert payload["run_id"] == "hive-sydney-morning-fixture"
    assert payload["fired_at_ts"].startswith("2026-09-17T20:32:00")
    assert payload["scheduled_anchor_ts"].startswith("2026-09-17T20:30:00")
    assert payload["delta_seconds"] == 120
    assert payload["status"] == "ok"
    assert payload["exit_status"] == 0
    assert payload["payload_path"].endswith("us-pre-market.md")
    rows = _rows(dest)
    assert len(rows) == 1
    assert rows[0]["run_id"] == "hive-sydney-morning-fixture"


def test_failed_cli_heartbeat_is_still_a_fire(tmp_path: Path, capsys) -> None:
    dest = tmp_path / "completions"
    rc = main(
        [
            "schedule",
            "heartbeat",
            "--routine-id",
            "grok.us_pre_market",
            "--fired-at",
            "2026-09-18T13:00:00Z",
            "--exit-status",
            "2",
            "--repo-root",
            str(ROOT),
            "--completions-dir",
            str(dest),
            "--no-db",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["exit_status"] == 2
    assert payload["status"] in {"ok", "late"}
    assert payload["fired_at_ts"] is not None


def test_brief_cli_path_writes_hive_routine_completion(tmp_path: Path, capsys) -> None:
    dest = tmp_path / "completions"
    rc = main(
        [
            "brief",
            "preopen",
            "--fixture",
            str(BRIEF_FIXTURE),
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
            "--no-db",
            "--as-of",
            "2026-09-18T13:00:00Z",
            "--routine-id",
            "grok.us_pre_market",
            "--run-id",
            "hive-preopen-cli",
            "--completions-dir",
            str(dest),
        ]
    )
    assert rc == 0
    capsys.readouterr()
    rows = _rows(dest)
    assert any(row["routine_id"] == "grok.us_pre_market" for row in rows)
    hit = next(row for row in rows if row["routine_id"] == "grok.us_pre_market")
    assert hit["run_id"] == "hive-preopen-cli"
    assert hit["exit_status"] == 0
    assert hit["payload_path"]
    assert hit["cli"] == "lab brief preopen"
    assert hit["delta_seconds"] is not None


def test_deliver_cli_path_writes_weekly_completion(tmp_path: Path, capsys) -> None:
    dest = tmp_path / "completions"
    rc = main(
        [
            "deliver",
            "pack",
            "--desk",
            "ops",
            "--from-markdown",
            str(PACK_MD),
            "--as-of",
            "2026-09-18T07:00:00Z",
            "--no-send",
            "--no-db",
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
            "--routine-id",
            "grok.weekly_investment_review",
            "--run-id",
            "hive-weekly-cli",
            "--completions-dir",
            str(dest),
        ]
    )
    assert rc == 0
    capsys.readouterr()
    rows = _rows(dest)
    assert any(row["routine_id"] == "grok.weekly_investment_review" for row in rows)
    hit = next(row for row in rows if row["routine_id"] == "grok.weekly_investment_review")
    assert hit["run_id"] == "hive-weekly-cli"
    assert hit["exit_status"] == 0
    assert hit["source"] == "lab.deliver"


def test_miss_detector_sees_fire_vs_miss(tmp_path: Path, capsys) -> None:
    dest = tmp_path / "completions"
    catalog, completions, now = load_fixture(HIVE_CLOCK, root=ROOT)
    assert now is not None
    before = miss_sweep(catalog, completions, now)
    assert before.escalated is True
    assert any(row.routine_id == "grok.us_pre_market" for row in before.misses)

    rc_miss = main(
        [
            "schedule",
            "miss-check",
            "--fixture",
            str(HIVE_CLOCK),
            "--now",
            "2026-09-18T13:20:00Z",
            "--no-db",
            "--out",
            str(tmp_path / "incidents-before"),
        ]
    )
    capsys.readouterr()
    assert rc_miss == 1

    rc_write = main(
        [
            "schedule",
            "heartbeat",
            "--routine-id",
            "grok.us_pre_market",
            "--fired-at",
            "2026-09-18T13:02:00Z",
            "--run-id",
            "hive-preopen-on-anchor",
            "--exit-status",
            "0",
            "--repo-root",
            str(ROOT),
            "--completions-dir",
            str(dest),
            "--no-db",
        ]
    )
    assert rc_write == 0
    capsys.readouterr()

    disk = load_disk_completions(dest, catalog=catalog)
    after = miss_sweep(catalog, [*completions, *disk], now)
    assert after.escalated is False
    assert not any(row.routine_id == "grok.us_pre_market" for row in after.misses)

    rc_check = main(
        [
            "schedule",
            "miss-check",
            "--fixture",
            str(HIVE_CLOCK),
            "--now",
            "2026-09-18T13:20:00Z",
            "--no-db",
            "--completions-dir",
            str(dest),
            "--out",
            str(tmp_path / "incidents-after"),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc_check == 0
    assert payload["escalated"] is False
    assert payload["n_missed"] == 0
    assert payload["heartbeat_is_not_the_check"] is True


def test_fixture_clock_without_completions_dir_stays_isolated(capsys) -> None:
    rc = main(
        [
            "schedule",
            "miss-check",
            "--fixture",
            str(CI_CLOCK),
            "--now",
            "2026-09-19T09:49:00Z",
            "--no-db",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["escalated"] is False


def test_deliver_send_stays_frozen(capsys) -> None:
    rc = main(["deliver", "test", "--desk", "ops", "--send", "--i-mean-it", "--repo-root", str(ROOT)])
    err = capsys.readouterr().err
    assert rc == 2
    assert "frozen" in err.lower()
    assert "step 5" in err.lower()


def test_delta_vs_sydney_morning_anchor() -> None:
    from mm_desks.scheduler import classify_fire, load_catalog, stamp_fire

    catalog = load_catalog(ROOT)
    routine = catalog.by_id()["grok.sydney_morning"]
    fired = datetime(2026, 9, 17, 20, 32, tzinfo=UTC)
    record = stamp_fire(routine, fired_at=fired, run_id="delta-check", as_of_knowledge=fired)
    assert record.delta_seconds == 120
    assert record.status == "ok"
    delta, status = classify_fire(record.scheduled_anchor_ts, fired, 300)
    assert delta == 120
    assert status == "ok"
