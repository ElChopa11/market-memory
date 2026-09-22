"""Frozen-clock tests for the Sydney 06:30 ±900s dual-cron guard.

AEST = UTC+10 (before first Sunday of October; after first Sunday of April).
AEDT = UTC+11 (after first Sunday of October; before first Sunday of April).
Both Actions crons always schedule; the off-season companion must no-op.
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from mm_common.time import parse_utc
from mm_desks.scheduler import DEFAULT_MISS_AFTER
from mm_desks.sydney_anchor import (
    DEFAULT_MISS_AFTER_SECONDS,
    OUTSIDE_NOTE,
    REASON_FORCE,
    REASON_OUTSIDE,
    REASON_WEEKEND,
    REASON_WITHIN,
    decide_sydney_morning_anchor,
    main,
)

# In-window crons: |delta| <= 900 around Sydney 06:30. These must stamp.
IN_WINDOW = [
    pytest.param("2026-09-21T20:30:00Z", 0, "AEST", id="aest-sep-on-anchor"),
    pytest.param("2026-09-21T20:15:00Z", -900, "AEST", id="aest-sep-minus-900"),
    pytest.param("2026-09-21T20:45:00Z", 900, "AEST", id="aest-sep-plus-900"),
    pytest.param("2026-04-06T20:30:00Z", 0, "AEST", id="aest-apr-on-anchor"),
    pytest.param("2026-04-06T20:15:00Z", -900, "AEST", id="aest-apr-minus-900"),
    pytest.param("2026-04-06T20:45:00Z", 900, "AEST", id="aest-apr-plus-900"),
    pytest.param("2026-11-02T19:30:00Z", 0, "AEDT", id="aedt-nov-on-anchor"),
    pytest.param("2026-11-02T19:15:00Z", -900, "AEDT", id="aedt-nov-minus-900"),
    pytest.param("2026-11-02T19:45:00Z", 900, "AEDT", id="aedt-nov-plus-900"),
    pytest.param("2026-10-05T19:30:00Z", 0, "AEDT", id="aedt-oct-on-anchor"),
    pytest.param("2026-10-05T19:15:00Z", -900, "AEDT", id="aedt-oct-minus-900"),
    pytest.param("2026-10-05T19:45:00Z", 900, "AEDT", id="aedt-oct-plus-900"),
]

# Off-season companion cron, plus the 901s edge just outside the window.
OFF_SEASON = [
    pytest.param("2026-09-21T19:30:00Z", -3600, "AEST", id="aest-sep-companion-1930"),
    pytest.param("2026-09-21T20:14:59Z", -901, "AEST", id="aest-sep-minus-901"),
    pytest.param("2026-09-21T20:45:01Z", 901, "AEST", id="aest-sep-plus-901"),
    pytest.param("2026-04-06T19:30:00Z", -3600, "AEST", id="aest-apr-companion-1930"),
    pytest.param("2026-11-02T20:30:00Z", 3600, "AEDT", id="aedt-nov-companion-2030"),
    pytest.param("2026-11-02T19:14:59Z", -901, "AEDT", id="aedt-nov-minus-901"),
    pytest.param("2026-11-02T19:45:01Z", 901, "AEDT", id="aedt-nov-plus-901"),
    pytest.param("2026-10-05T20:30:00Z", 3600, "AEDT", id="aedt-oct-companion-2030"),
]


@pytest.fixture(autouse=True)
def _clear_force_stamp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FORCE_STAMP", raising=False)


def test_tolerance_matches_scheduler_catalog() -> None:
    assert DEFAULT_MISS_AFTER_SECONDS == 900
    assert DEFAULT_MISS_AFTER_SECONDS == DEFAULT_MISS_AFTER


@pytest.mark.parametrize("now_iso,delta,season", IN_WINDOW)
def test_in_window_cron_stamps(now_iso: str, delta: int, season: str) -> None:
    now = parse_utc(now_iso)
    decision = decide_sydney_morning_anchor(now, force=False)
    assert decision.stamp is True
    assert decision.skip is False
    assert decision.reason == REASON_WITHIN
    assert decision.delta_seconds == delta
    assert abs(decision.delta_seconds) <= 900
    assert decision.force is False
    offset = decision.local_iso[-6:]
    if season == "AEST":
        assert offset == "+10:00"
    else:
        assert offset == "+11:00"
    # CLI agrees and exits 0 (stamp is not a failure).
    code, payload = _run_cli(["--now", now_iso])
    assert code == 0
    assert payload["stamp"] is True
    assert payload["reason"] == REASON_WITHIN
    assert payload["delta_seconds"] == delta


@pytest.mark.parametrize("now_iso,delta,season", OFF_SEASON)
def test_off_season_companion_exits_0_without_stamp(now_iso: str, delta: int, season: str) -> None:
    now = parse_utc(now_iso)
    decision = decide_sydney_morning_anchor(now, force=False)
    assert decision.skip is True
    assert decision.stamp is False
    assert decision.reason == REASON_OUTSIDE
    assert decision.note == OUTSIDE_NOTE
    assert decision.delta_seconds == delta
    assert abs(decision.delta_seconds) > 900
    offset = decision.local_iso[-6:]
    if season == "AEST":
        assert offset == "+10:00"
    else:
        assert offset == "+11:00"
    code, payload = _run_cli(["--now", now_iso])
    assert code == 0
    assert payload["reason"] == REASON_OUTSIDE
    assert payload["stamp"] is False
    assert payload["skip"] is True
    assert payload["delta_seconds"] == delta


@pytest.mark.parametrize("now_iso,delta,season", OFF_SEASON)
def test_workflow_dispatch_force_bypasses_guard(now_iso: str, delta: int, season: str) -> None:
    now = parse_utc(now_iso)
    decision = decide_sydney_morning_anchor(now, force=True)
    assert decision.stamp is True
    assert decision.skip is False
    assert decision.reason == REASON_FORCE
    assert decision.force is True
    assert decision.delta_seconds == delta
    assert season in {"AEST", "AEDT"}
    code, payload = _run_cli(["--now", now_iso, "--force"])
    assert code == 0
    assert payload["stamp"] is True
    assert payload["reason"] == REASON_FORCE
    assert payload["skip"] is False


def test_force_env_bypasses_without_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORCE_STAMP", "true")
    code, payload = _run_cli(["--now", "2026-09-21T19:30:00Z"])
    assert code == 0
    assert payload["reason"] == REASON_FORCE
    assert payload["stamp"] is True
    assert payload["delta_seconds"] == -3600


def test_weekend_sydney_skips_even_on_anchor() -> None:
    # Saturday 2026-09-26 06:30 AEST = Friday 20:30 UTC. Cron does not schedule
    # this dow; the guard still refuses a non-forced stamp.
    now = parse_utc("2026-09-25T20:30:00Z")
    decision = decide_sydney_morning_anchor(now, force=False)
    assert decision.reason == REASON_WEEKEND
    assert decision.skip is True
    assert decision.stamp is False
    assert decision.delta_seconds == 0
    code, payload = _run_cli(["--now", "2026-09-25T20:30:00Z"])
    assert code == 0
    assert payload["reason"] == REASON_WEEKEND
    assert payload["stamp"] is False


def test_force_on_weekend_stamps() -> None:
    decision = decide_sydney_morning_anchor(parse_utc("2026-09-25T20:30:00Z"), force=True)
    assert decision.reason == REASON_FORCE
    assert decision.stamp is True
    assert decision.skip is False


def test_naive_now_is_rejected() -> None:
    with pytest.raises(ValueError):
        decide_sydney_morning_anchor(datetime(2026, 9, 22, 6, 30, 0))


def _run_cli(argv: list[str]) -> tuple[int, dict]:
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(argv)
    return code, json.loads(buf.getvalue())
