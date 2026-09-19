"""IMP-042 miss sweep: delta math, closed-window miss, CI fixture clock.

Miss detector is the scheduler control. Heartbeat-on-fire is a log.
Canaries are ignored.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from mm_desks.scheduler import (
    classify_delta,
    classify_fire,
    delta_seconds,
    load_catalog,
    load_fixture,
    miss_sweep,
    parse_utc,
    stamp_fire,
    window_closed,
)
from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
CI_CLOCK = ROOT / "tests" / "fixtures" / "scheduler" / "ci_clock.yaml"
MISS_CLOCK = ROOT / "tests" / "fixtures" / "scheduler" / "miss_clock.yaml"
UTC = timezone.utc


def test_delta_math_ok_late_and_early_off_anchor() -> None:
    anchor = datetime(2026, 9, 18, 13, 0, tzinfo=UTC)  # 23:00 AEST
    fired_on = datetime(2026, 9, 18, 13, 2, tzinfo=UTC)
    fired_early = datetime(2026, 9, 18, 12, 2, tzinfo=UTC)  # 22:02 AEST
    assert delta_seconds(anchor, fired_on) == 120
    assert classify_delta(120, 300) == "ok"
    delta, status = classify_fire(anchor, fired_early, 300)
    assert delta == -3480
    assert status == "late"
    assert window_closed(anchor, datetime(2026, 9, 18, 13, 16, tzinfo=UTC), 900) is True
    assert window_closed(anchor, datetime(2026, 9, 18, 13, 10, tzinfo=UTC), 900) is False


def test_miss_sweep_escalates_closed_window_without_completion() -> None:
    catalog, completions, now = load_fixture(MISS_CLOCK, root=ROOT)
    assert now is not None
    result = miss_sweep(catalog, completions, now)
    assert result.escalated is True
    missed_ids = {row.routine_id for row in result.misses}
    assert "grok.sydney_morning_digest_8am" in missed_ids
    assert all(row.reason == "closed_window_no_completion" for row in result.misses if row.routine_id == "grok.sydney_morning_digest_8am")
    assert any(row.incident == "SCHED-001" for row in result.misses)
    # NY sibling fired — not a miss for that Friday anchor.
    assert not any(
        row.routine_id == "lab.pulse.preopen" and row.scheduled_anchor_ts.isoformat() == "2026-09-18T12:00:00+00:00"
        for row in result.misses
    )


def test_miss_sweep_does_not_close_sched001_when_pending() -> None:
    """Pending next window is not a close. Friday 08:00 without a row stays a miss."""
    catalog, completions, now = load_fixture(MISS_CLOCK, root=ROOT)
    result = miss_sweep(catalog, completions, now)
    assert result.escalated is True
    assert any(row.incident == "SCHED-001" for row in result.misses)


def test_ci_fixture_clock_is_green() -> None:
    catalog, completions, now = load_fixture(CI_CLOCK, root=ROOT)
    result = miss_sweep(catalog, completions, now or parse_utc("2026-09-19T09:49:00Z"))
    assert result.escalated is False
    assert result.misses == ()


def test_cli_miss_check_ci_clock_exit_zero() -> None:
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
    assert rc == 0


def test_cli_miss_check_writes_open_artifact_and_exits_nonzero(tmp_path: Path) -> None:
    rc = main(
        [
            "schedule",
            "miss-check",
            "--fixture",
            str(MISS_CLOCK),
            "--now",
            "2026-09-19T09:49:00Z",
            "--no-db",
            "--out",
            str(tmp_path),
        ]
    )
    assert rc == 1
    artifact = tmp_path / "2026-09-19-miss.md"
    assert artifact.is_file()
    text = artifact.read_text(encoding="utf-8")
    assert "OPEN ops artifact" in text
    assert "SCHED-001" in text
    assert "grok.sydney_morning_digest_8am" in text
    assert "does not close" in text.lower() or "stays OPEN" in text


def test_heartbeat_check_is_alias_of_miss_sweep_not_a_log_dump(tmp_path: Path) -> None:
    rc = main(
        [
            "schedule",
            "heartbeat-check",
            "--fixture",
            str(MISS_CLOCK),
            "--now",
            "2026-09-19T09:49:00Z",
            "--no-db",
            "--out",
            str(tmp_path),
        ]
    )
    assert rc == 1
    assert (tmp_path / "2026-09-19-miss.md").is_file()


def test_cli_backfill_writes_report(tmp_path: Path) -> None:
    rc = main(
        [
            "schedule",
            "backfill",
            "--fixture",
            str(CI_CLOCK),
            "--now",
            "2026-09-19T09:49:00Z",
            "--no-db",
            "--report-out",
            str(tmp_path / "backfill-2026-09-19.md"),
        ]
    )
    assert rc == 0
    text = (tmp_path / "backfill-2026-09-19.md").read_text(encoding="utf-8")
    assert "ci.pulse.preopen" in text
    assert "miss_sweep" in text
    catalog = load_catalog(ROOT)
    for row in catalog.routines:
        assert "canary" not in row.routine_id.lower()
        assert "canary" not in row.display.lower()
    ids = catalog.by_id()
    assert "grok.sydney_morning_digest_8am" in ids
    assert "lab.pulse.preopen" in ids
    assert "lab.delivery.watchlist" in ids


def test_stamp_fire_is_secondary_log_not_a_pass() -> None:
    catalog = load_catalog(ROOT)
    routine = catalog.by_id()["grok.us_pre_market"]
    fired = datetime(2026, 9, 18, 12, 2, tzinfo=UTC)
    record = stamp_fire(routine, fired_at=fired, run_id="obs-2202", as_of_knowledge=fired, source="observed")
    assert record.delta_seconds == -3480
    assert record.status == "late"
    # A late fire is a completion (not a miss) — BRIEF-TAG class, not SCHED-001.
    result = miss_sweep(
        catalog.__class__(
            routines=(routine,),
            late_after_seconds=300,
            miss_after_seconds=900,
            lookback_days=1,
        ),
        (record,),
        datetime(2026, 9, 19, 9, 49, tzinfo=UTC),
        lookback_days=1,
    )
    assert not any(row.routine_id == "grok.us_pre_market" for row in result.misses)
