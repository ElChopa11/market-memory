"""Sydney Morning does not skip Australian public holidays.

Mon 5 Oct 2026 is NSW Labour Day (first Monday in October) and the first
weekday after the 4 Oct DST start. The host cron, the stamp, the brief's
session label, and the deliver gate treat it as a Monday.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from mm_briefing.schedule import us_session_status
from mm_desks.deliver_receipt import PROCEED, decide_deliver
from mm_desks.scheduler import load_catalog, local_anchor, scheduled_slot, stamp_fire

ROOT = Path(__file__).resolve().parents[2]
SYD = ZoneInfo("Australia/Sydney")
UTC = timezone.utc
CRONTAB = ROOT / "ops" / "host" / "crontab"
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
ROUTINE = "grok.sydney_morning"
# True for schedule and for every dispatch except mode=capture_proof,
# mode=render_proof, or mode=send_proof. The host payload omits mode, so the
# workflow default (normal) still stamps. No holiday, date, or quiet-hours clause.
STAGE1_IF = (
    "github.event_name != 'workflow_dispatch' || "
    "(inputs.mode != 'capture_proof' && inputs.mode != 'render_proof') && "
    "inputs.mode != 'send_proof'"
)


def _stage1_stamp_runs(expr: str, *, event_name: str, mode: str | None) -> bool:
    """Evaluate the one allowed stage1 if. Any other expression is refused.

    ``mode is None`` is an omitted workflow_dispatch input. That is not
    capture_proof, render_proof, or send_proof, so the stamp runs. A schedule
    event ignores mode.
    """
    left, sep, right = expr.partition(" || ")
    assert sep == " || ", expr
    assert left == "github.event_name != 'workflow_dispatch'", expr
    assert right == (
        "(inputs.mode != 'capture_proof' && inputs.mode != 'render_proof') && "
        "inputs.mode != 'send_proof'"
    ), expr
    return event_name != "workflow_dispatch" or mode not in {
        "capture_proof",
        "render_proof",
        "send_proof",
    }


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
        if not stripped or stripped.startswith("#") or "=" in stripped.split()[0]:
            continue
        jobs.append(stripped.split())
    assert len(jobs) == 1
    return jobs[0]


def _cron_dow(local: datetime) -> int:
    """Cron day-of-week: Sunday 0, Monday 1, … Saturday 6."""
    return local.isoweekday() % 7


def host_cron_fires(local: datetime) -> bool:
    """True when the installed host crontab would fire at this Sydney wall time.

    The five fields are Australia/Sydney wall clock when the system timezone
    is Australia/Sydney. Debian/Ubuntu vixie cron ignores CRON_TZ and uses
    system time. ``*`` matches every day-of-month and month. ``1-5`` is
    Mon–Fri. There is no holiday field.
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
    # Host dispatch does not send mode. Omitted mode is the workflow default
    # (normal), so this cron reaches stage1-stamp. capture_proof is not sent.
    dispatch = (ROOT / "ops" / "host" / "dispatch-sydney-morning.sh").read_text(encoding="utf-8")
    payload_lines = [line for line in dispatch.splitlines() if line.startswith("PAYLOAD=")]
    assert payload_lines == [
        """PAYLOAD="$(printf '{"ref":"%s","inputs":{"i_mean_it_deliver":"true"}}' "$REF")\""""
    ]
    assert "capture_proof" not in dispatch
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
    # The only stage1 gate skips capture_proof and render_proof. A second if,
    # or any extra clause (calendar, holiday, date, weekday, quiet hours), fails.
    header = stage1.split("steps:", 1)[0]
    if_lines = [line.strip() for line in header.splitlines() if line.strip().startswith("if:")]
    assert if_lines == [f"if: {STAGE1_IF}"]
    parsed = yaml.safe_load(workflow)
    job = parsed["jobs"]["stage1-stamp"]
    assert job["if"] == STAGE1_IF
    assert [step for step in job["steps"] if "if" in step] == []
    # Schedule is not workflow_dispatch, so the left clause stamps every cron
    # fire. A dispatch stamps unless mode is capture_proof or render_proof.
    # Omitted mode is the workflow default, normal, which is neither.
    # PyYAML loads the GitHub `on:` key as boolean True.
    on_block = parsed[True] if True in parsed else parsed["on"]
    assert on_block["workflow_dispatch"]["inputs"]["mode"]["default"] == "normal"
    assert _stage1_stamp_runs(job["if"], event_name="schedule", mode=None) is True
    assert _stage1_stamp_runs(job["if"], event_name="workflow_dispatch", mode="normal") is True
    assert _stage1_stamp_runs(job["if"], event_name="workflow_dispatch", mode=None) is True
    assert _stage1_stamp_runs(job["if"], event_name="workflow_dispatch", mode="capture_proof") is False
    assert _stage1_stamp_runs(job["if"], event_name="workflow_dispatch", mode="render_proof") is False
    assert _stage1_stamp_runs(job["if"], event_name="workflow_dispatch", mode="send_proof") is False
    assert "github.event_name == 'schedule'" in brief
    assert "i_mean_it_deliver" in brief
    for rel in PATHS:
        assert "holiday" not in (ROOT / rel).read_text(encoding="utf-8").lower(), rel
