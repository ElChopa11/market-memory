"""Sydney Morning does not skip Australian public holidays.

Mon 5 Oct 2026 is NSW Labour Day (first Monday in October) and the first
weekday after the 4 Oct DST start. The host cron, the stamp, the brief's
session label, and the deliver gate treat it as a Monday.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from mm_briefing.schedule import us_session_status
from mm_desks.deliver_receipt import PROCEED, decide_deliver
from mm_desks.scheduler import load_catalog, local_anchor, scheduled_slot, stamp_fire

ROOT = Path(__file__).resolve().parents[2]
SYD = ZoneInfo("Australia/Sydney")
UTC = timezone.utc
CRONTAB = ROOT / "ops" / "host" / "crontab"
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
ROUTINE = "grok.sydney_morning"

# Paths that decide whether the morning job runs or what it stamps.
PATHS = (
    "ops/host/crontab",
    "ops/host/dispatch-sydney-morning.sh",
    ".github/workflows/hybrid-sydney-morning.yml",
    "config/schedules/routines.yaml",
    "packages/desks/src/mm_desks/scheduler.py",
    "packages/desks/src/mm_desks/deliver_receipt.py",
    "packages/briefing/src/mm_briefing/schedule.py",
    "packages/briefing/src/mm_briefing/engine.py",
    "packages/briefing/src/mm_briefing/calendar.py",
    "packages/delivery/src/mm_delivery/gates.py",
)


def _job_fields() -> list[str]:
    jobs = []
    for line in CRONTAB.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("CRON_TZ="):
            continue
        jobs.append(stripped.split())
    assert len(jobs) == 1
    return jobs[0]


def _cron_dow(local: datetime) -> int:
    """Cron day-of-week: Sunday 0, Monday 1, … Saturday 6."""
    return local.isoweekday() % 7


def host_cron_fires(local: datetime) -> bool:
    """True when the installed host crontab would fire at this Sydney wall time.

    CRON_TZ=Australia/Sydney, so the five fields are that zone's wall clock.
    ``*`` matches every day-of-month and month. ``1-5`` is Mon–Fri. There is
    no holiday field.
    """
    assert local.tzinfo == SYD
    minute, hour, dom, month, dow = _job_fields()[:5]
    assert minute == "30" and hour == "6" and dom == "*" and month == "*" and dow == "1-5"
    if local.hour != 6 or local.minute != 30 or local.second != 0:
        return False
    cron_dow = _cron_dow(local)
    return 1 <= cron_dow <= 5


def test_host_cron_fires_mon_5_oct_2026_at_sydney_anchor() -> None:
    routine = load_catalog(ROOT).by_id()[ROUTINE]
    labour = datetime(2026, 10, 5, 6, 30, tzinfo=SYD)
    assert labour.isoweekday() == 1
    assert date(2026, 10, 5).day <= 7
    assert "CRON_TZ=Australia/Sydney" in CRONTAB.read_text(encoding="utf-8")
    assert host_cron_fires(labour) is True
    anchor = local_anchor(routine, labour.date())
    assert labour.astimezone(UTC) == anchor
    assert anchor == datetime(2026, 10, 4, 19, 30, tzinfo=UTC)
    slot, weekday_ok, weekday = scheduled_slot(routine, labour)
    assert weekday_ok is True
    assert weekday == "Mon"
    assert slot == anchor
    record = stamp_fire(routine, fired_at=labour, run_id="host-labour-day-20261005", as_of_knowledge=labour)
    assert record.status == "ok"
    assert record.delta_seconds == 0
    assert record.scheduled_anchor_ts == anchor


def test_labour_day_stamp_matches_any_other_monday() -> None:
    routine = load_catalog(ROOT).by_id()[ROUTINE]
    ordinary = datetime(2026, 9, 28, 6, 30, tzinfo=SYD)
    labour = datetime(2026, 10, 5, 6, 30, tzinfo=SYD)
    assert ordinary.isoweekday() == labour.isoweekday() == 1
    assert host_cron_fires(ordinary) is True
    assert host_cron_fires(labour) is True
    left = stamp_fire(routine, fired_at=ordinary, run_id="monday-ordinary", as_of_knowledge=ordinary)
    right = stamp_fire(routine, fired_at=labour, run_id="monday-labour-day", as_of_knowledge=labour)
    assert left.status == right.status == "ok"
    assert left.delta_seconds == right.delta_seconds == 0
    assert scheduled_slot(routine, ordinary)[1:] == scheduled_slot(routine, labour)[1:] == (True, "Mon")
    # Offsets differ because DST has started. The weekday class does not.
    assert ordinary.utcoffset() == timedelta(hours=10)
    assert labour.utcoffset() == timedelta(hours=11)


def test_brief_and_deliver_do_not_special_case_labour_day(tmp_path) -> None:
    ordinary = datetime(2026, 9, 28, 6, 30, tzinfo=SYD)
    labour = datetime(2026, 10, 5, 6, 30, tzinfo=SYD)
    ordinary_session = us_session_status(ordinary)
    labour_session = us_session_status(labour)
    # Both instants are still Sunday afternoon in New York. Same label.
    assert ordinary_session.code == labour_session.code == "weekend_closed"
    routine = load_catalog(ROOT).by_id()[ROUTINE]
    anchor = local_anchor(routine, labour.date())
    assert decide_deliver(tmp_path, ROUTINE, anchor) == PROCEED
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "holiday" not in workflow.lower()
    assert "--ignore-quiet-hours" in workflow
    stage1, brief = workflow.split("\n  brief-and-deliver:\n", 1)
    assert "stage1-stamp:" in stage1
    assert "\n    if:" not in stage1.split("steps:", 1)[0]
    assert "github.event_name == 'schedule'" in brief
    assert "i_mean_it_deliver" in brief
    for rel in PATHS:
        assert "holiday" not in (ROOT / rel).read_text(encoding="utf-8").lower(), rel
