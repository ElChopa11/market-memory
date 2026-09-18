"""Phase 5e gates: threshold, quiet hours, completeness. Never alert without a threshold."""

from __future__ import annotations

from pathlib import Path

from mm_common.time import parse_utc
from mm_delivery.config import load_telegram_settings
from mm_delivery.gates import (
    REASON_QUIET_HOURS,
    REASON_THRESHOLD_CONFIG_REQUIRED,
    REASON_THRESHOLD_NOT_MET,
    evaluate_quiet_hours,
    evaluate_send_gates,
    evaluate_threshold,
    in_quiet_hours,
)

ROOT = Path(__file__).resolve().parents[2]


def test_config_requires_numeric_thresholds() -> None:
    settings = load_telegram_settings(ROOT)
    assert settings.thresholds.require_threshold_config is True
    assert settings.thresholds.has_numeric("desk_pack") is True
    assert settings.thresholds.has_numeric("alert") is True


def test_missing_threshold_refuses() -> None:
    settings = load_telegram_settings(ROOT)
    empty = evaluate_threshold(
        type(settings.thresholds)(require_threshold_config=True, specs=()),
        kind="alert",
        completeness_pct=3,
    )
    assert empty.allow is False
    assert empty.reason == REASON_THRESHOLD_CONFIG_REQUIRED


def test_completeness_below_min_refuses_desk_pack() -> None:
    settings = load_telegram_settings(ROOT)
    decision = evaluate_threshold(settings.thresholds, kind="desk_pack", completeness_pct=0.0)
    assert decision.allow is False
    assert decision.reason == REASON_THRESHOLD_NOT_MET
    ok = evaluate_threshold(settings.thresholds, kind="desk_pack", completeness_pct=100.0)
    assert ok.allow is True


def test_quiet_hours_sydney_overnight_window() -> None:
    settings = load_telegram_settings(ROOT)
    qh = settings.quiet_hours
    inside = parse_utc("2026-09-18T13:00:00Z")  # 23:00 Sydney (AEST)
    outside = parse_utc("2026-09-18T02:00:00Z")  # 12:00 Sydney
    assert in_quiet_hours(inside, start=qh.start, end=qh.end, tz=qh.timezone) is True
    assert in_quiet_hours(outside, start=qh.start, end=qh.end, tz=qh.timezone) is False
    blocked = evaluate_quiet_hours(settings, inside)
    assert blocked.allow is False
    assert blocked.reason == REASON_QUIET_HOURS
    open_ = evaluate_quiet_hours(settings, outside)
    assert open_.allow is True


def test_send_gates_compose() -> None:
    settings = load_telegram_settings(ROOT)
    now = parse_utc("2026-09-18T02:00:00Z")
    ok = evaluate_send_gates(settings, kind="desk_pack", now=now, completeness_pct=100.0)
    assert ok.allow is True
    quiet = evaluate_send_gates(
        settings, kind="desk_pack", now=parse_utc("2026-09-18T13:00:00Z"), completeness_pct=100.0
    )
    assert quiet.allow is False
