"""Frozen AEST and AEDT clocks for the Sydney 06:30 ±900s decision.

AEST is UTC+10 (after the first Sunday of April, before the first Sunday of October).
AEDT is UTC+11 (after the first Sunday of October, before the first Sunday of April).
In-window instants must decide stamp. The Actions workflow does not call this module.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from mm_common.time import as_utc, parse_utc
from mm_desks.scheduler import DEFAULT_MISS_AFTER, load_catalog, scheduled_slot
from mm_desks.sydney_anchor import (
    DEFAULT_MISS_AFTER_SECONDS,
    KNOWN_BUG_A_ANCHOR,
    KNOWN_BUG_A_DELTA,
    KNOWN_BUG_A_FIRE,
    KNOWN_BUG_A_RUN_ID,
    KNOWN_BUG_A_WEDNESDAY_SLOT,
    KNOWN_BUG_B_ACTIONS_RUN,
    KNOWN_BUG_B_ANCHOR,
    KNOWN_BUG_B_CREATED,
    KNOWN_BUG_B_DELTA,
    KNOWN_BUG_B_NOW,
    OBSERVED_DRIFT_DELTA,
    OBSERVED_DRIFT_NOW,
    OBSERVED_DRIFT_RUN_ID,
    REASON_FORCE,
    REASON_OUTSIDE,
    REASON_WEEKEND,
    REASON_WITHIN,
    ROUTINE_ID,
    decide_sydney_morning_anchor,
    main,
    sydney_morning_anchor,
)

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
HOUSE = ROOT / "config" / "knowledge" / "house-lessons.md"

# (now_iso, delta, season, offset, anchor_iso) — |delta| <= 900 must stamp.
IN_WINDOW = [
    pytest.param("2026-09-21T20:15:00Z", -900, "AEST", "+10:00", "2026-09-21T20:30:00Z", id="aest-sep-minus-900"),
    pytest.param("2026-09-21T20:30:00Z", 0, "AEST", "+10:00", "2026-09-21T20:30:00Z", id="aest-sep-on-anchor"),
    pytest.param("2026-09-21T20:45:00Z", 900, "AEST", "+10:00", "2026-09-21T20:30:00Z", id="aest-sep-plus-900"),
    pytest.param("2026-09-22T20:30:00Z", 0, "AEST", "+10:00", "2026-09-22T20:30:00Z", id="aest-wed-on-anchor"),
    pytest.param("2026-04-05T20:15:00Z", -900, "AEST", "+10:00", "2026-04-05T20:30:00Z", id="aest-apr-minus-900"),
    pytest.param("2026-04-05T20:30:00Z", 0, "AEST", "+10:00", "2026-04-05T20:30:00Z", id="aest-apr-on-anchor"),
    pytest.param("2026-04-05T20:45:00Z", 900, "AEST", "+10:00", "2026-04-05T20:30:00Z", id="aest-apr-plus-900"),
    pytest.param("2026-11-01T19:15:00Z", -900, "AEDT", "+11:00", "2026-11-01T19:30:00Z", id="aedt-nov-minus-900"),
    pytest.param("2026-11-01T19:30:00Z", 0, "AEDT", "+11:00", "2026-11-01T19:30:00Z", id="aedt-nov-on-anchor"),
    pytest.param("2026-11-01T19:45:00Z", 900, "AEDT", "+11:00", "2026-11-01T19:30:00Z", id="aedt-nov-plus-900"),
    pytest.param("2026-10-04T19:15:00Z", -900, "AEDT", "+11:00", "2026-10-04T19:30:00Z", id="aedt-oct-minus-900"),
    pytest.param("2026-10-04T19:30:00Z", 0, "AEDT", "+11:00", "2026-10-04T19:30:00Z", id="aedt-oct-on-anchor"),
    pytest.param("2026-10-04T19:45:00Z", 900, "AEDT", "+11:00", "2026-10-04T19:30:00Z", id="aedt-oct-plus-900"),
]

# Just outside ±900, plus the one-hour DST offset of the other season's UTC wall.
OUTSIDE = [
    pytest.param("2026-09-21T20:14:59Z", -901, "AEST", "+10:00", id="aest-sep-minus-901"),
    pytest.param("2026-09-21T20:45:01Z", 901, "AEST", "+10:00", id="aest-sep-plus-901"),
    pytest.param("2026-09-21T19:30:00Z", -3600, "AEST", "+10:00", id="aest-sep-one-hour-early"),
    pytest.param("2026-11-01T19:14:59Z", -901, "AEDT", "+11:00", id="aedt-nov-minus-901"),
    pytest.param("2026-11-01T19:45:01Z", 901, "AEDT", "+11:00", id="aedt-nov-plus-901"),
    pytest.param("2026-11-01T20:30:00Z", 3600, "AEDT", "+11:00", id="aedt-nov-one-hour-late"),
]

WEEKEND = [
    pytest.param("2026-09-25T20:30:00Z", "+10:00", id="aest-saturday"),
    pytest.param("2026-10-03T19:30:00Z", "+11:00", id="aedt-sunday"),
]


def test_tolerance_matches_scheduler_catalog() -> None:
    assert DEFAULT_MISS_AFTER_SECONDS == 900
    assert DEFAULT_MISS_AFTER_SECONDS == DEFAULT_MISS_AFTER


@pytest.mark.parametrize("now_iso,delta,season,offset,anchor_iso", IN_WINDOW)
def test_in_window_frozen_clock_stamps(
    now_iso: str,
    delta: int,
    season: str,
    offset: str,
    anchor_iso: str,
) -> None:
    now = parse_utc(now_iso)
    decision = decide_sydney_morning_anchor(now, force=False)
    assert decision.stamp is True
    assert decision.skip is False
    assert decision.reason == REASON_WITHIN
    assert decision.delta_seconds == delta
    assert abs(decision.delta_seconds) <= 900
    assert decision.force is False
    assert decision.anchor_utc == parse_utc(anchor_iso)
    assert decision.local_iso.endswith(offset)
    assert season in {"AEST", "AEDT"}
    code, payload = _run_cli(["--now", now_iso])
    assert code == 0
    assert payload["stamp"] is True
    assert payload["skip"] is False
    assert payload["reason"] == REASON_WITHIN
    assert payload["delta_seconds"] == delta
    assert payload["routine_id"] == ROUTINE_ID


@pytest.mark.parametrize("now_iso,delta,season,offset,anchor_iso", IN_WINDOW)
def test_in_window_anchor_matches_live_scheduled_slot(
    now_iso: str,
    delta: int,
    season: str,
    offset: str,
    anchor_iso: str,
) -> None:
    now = parse_utc(now_iso)
    routine = load_catalog(ROOT).by_id()[ROUTINE_ID]
    anchor, weekday_ok, _weekday = scheduled_slot(routine, now)
    assert weekday_ok is True
    assert as_utc(anchor) == parse_utc(anchor_iso)
    assert sydney_morning_anchor(now) == as_utc(anchor)
    assert delta == int((now - as_utc(anchor)).total_seconds())
    assert season in {"AEST", "AEDT"}
    assert offset in {"+10:00", "+11:00"}


@pytest.mark.parametrize("now_iso,delta,season,offset", OUTSIDE)
def test_outside_window_does_not_stamp(now_iso: str, delta: int, season: str, offset: str) -> None:
    decision = decide_sydney_morning_anchor(parse_utc(now_iso), force=False)
    assert decision.stamp is False
    assert decision.skip is True
    assert decision.reason == REASON_OUTSIDE
    assert decision.delta_seconds == delta
    assert abs(decision.delta_seconds) > 900
    assert decision.local_iso.endswith(offset)
    assert season in {"AEST", "AEDT"}
    code, payload = _run_cli(["--now", now_iso])
    assert code == 0
    assert payload["stamp"] is False
    assert payload["reason"] == REASON_OUTSIDE


@pytest.mark.parametrize("now_iso,offset", WEEKEND)
def test_weekend_on_anchor_does_not_stamp(now_iso: str, offset: str) -> None:
    decision = decide_sydney_morning_anchor(parse_utc(now_iso), force=False)
    assert decision.reason == REASON_WEEKEND
    assert decision.stamp is False
    assert decision.skip is True
    assert decision.delta_seconds == 0
    assert decision.local_iso.endswith(offset)


def test_known_bug_a_tuesday_anchor_on_wednesday_run() -> None:
    """Known bug (a). The extract keeps today's behaviour so the defect stays visible.

    Fire 2026-09-22T12:32:21Z is Tuesday 22:32 AEST. Same-calendar-date 06:30
    yields Tuesday 06:30 AEST (2026-09-21T20:30:00Z), delta 57741. Principal
    records that as the Tuesday anchor on a Wednesday run. Wednesday 06:30
    Australia/Sydney is 2026-09-22T20:30:00Z. Future tolerance work owns the fix.
    """
    now = parse_utc(KNOWN_BUG_A_FIRE)
    decision = decide_sydney_morning_anchor(now, force=False)
    tuesday = parse_utc(KNOWN_BUG_A_ANCHOR)
    wednesday = parse_utc(KNOWN_BUG_A_WEDNESDAY_SLOT)
    assert decision.anchor_utc == tuesday
    assert decision.anchor_utc != wednesday
    assert decision.delta_seconds == KNOWN_BUG_A_DELTA
    assert decision.stamp is False
    assert decision.reason == REASON_OUTSIDE
    routine = load_catalog(ROOT).by_id()[ROUTINE_ID]
    live_anchor, weekday_ok, weekday = scheduled_slot(routine, now)
    assert weekday_ok is True
    assert weekday == "Tue"
    assert as_utc(live_anchor) == tuesday
    forced = decide_sydney_morning_anchor(now, force=True)
    assert forced.stamp is True
    assert forced.reason == REASON_FORCE
    assert forced.anchor_utc == tuesday
    assert KNOWN_BUG_A_RUN_ID == "actions-b1-35727756341"


def test_known_bug_b_observed_drift_is_outside_900() -> None:
    """Known bug (b). ±900s rejects the observed ~1h51m Actions drift.

    Schedule run created 2026-09-22T22:21:07Z (actions run 35791891126) versus
    the 20:30Z cron. Skip log now_utc 2026-09-22T22:21:22Z, delta_seconds=6682.
    That instant's Sydney date is Wednesday, so the anchor is the Wednesday
    slot; the defect is the tolerance. The later unguarded stamp
    (actions-b1-35795814246, delta 9428) is outside 900 as well. Wiring this
    module back would skip both.
    """
    skipped = decide_sydney_morning_anchor(parse_utc(KNOWN_BUG_B_NOW), force=False)
    assert skipped.anchor_utc == parse_utc(KNOWN_BUG_B_ANCHOR)
    assert skipped.delta_seconds == KNOWN_BUG_B_DELTA
    assert skipped.delta_seconds == 6682
    assert skipped.stamp is False
    assert skipped.reason == REASON_OUTSIDE
    assert KNOWN_BUG_B_CREATED == "2026-09-22T22:21:07Z"
    assert KNOWN_BUG_B_ACTIONS_RUN == "35791891126"
    later = decide_sydney_morning_anchor(parse_utc(OBSERVED_DRIFT_NOW), force=False)
    assert later.anchor_utc == parse_utc(KNOWN_BUG_B_ANCHOR)
    assert later.delta_seconds == OBSERVED_DRIFT_DELTA
    assert later.stamp is False
    assert OBSERVED_DRIFT_RUN_ID == "actions-b1-35795814246"


def test_naive_now_is_rejected() -> None:
    with pytest.raises(ValueError):
        decide_sydney_morning_anchor(datetime(2026, 9, 23, 6, 30, 0))


def test_house_lesson_records_both_bugs_and_drift() -> None:
    text = HOUSE.read_text(encoding="utf-8")
    assert KNOWN_BUG_A_RUN_ID in text
    assert "2026-09-21T20:30:00Z" in text
    assert "2026-09-22T20:30:00Z" in text
    assert "6682" in text
    assert "2026-09-22T22:21:07Z" in text
    assert "mm_desks.sydney_anchor" in text
    assert "9428" in text


def test_workflow_does_not_call_sydney_anchor() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "sydney_anchor" not in text
    assert "decide_sydney_morning_anchor" not in text
    assert "outside_anchor_window" not in text
    assert "FORCE_STAMP" not in text
    assert 'cron: "30 19 * * 0-4"' not in text
    assert 'cron: "30 20 * * 0-4"' in text
    assert text.count("cron:") == 1
    assert "lab" in text and "heartbeat" in text


def test_module_does_not_write_a_completion_or_send() -> None:
    src = (ROOT / "packages" / "desks" / "src" / "mm_desks" / "sydney_anchor.py").read_text(encoding="utf-8")
    assert "stamp_fire" not in src
    assert "TELEGRAM" not in src
    assert "send_message" not in src
    assert "hybrid-sydney-morning.yml" in src


def _run_cli(argv: list[str]) -> tuple[int, dict]:
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(argv)
    return code, json.loads(buf.getvalue())
