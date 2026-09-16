"""Naive datetimes are rejected; windows parse in UTC."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mm_common.time import as_utc, in_ops_tz, parse_utc, parse_window


def test_naive_datetime_rejected() -> None:
    with pytest.raises(ValueError, match="naive"):
        as_utc(datetime(2026, 9, 10, 0, 0))


def test_parse_utc_z_suffix() -> None:
    parsed = parse_utc("2026-09-10T00:05:00Z")
    assert parsed.tzinfo is not None
    assert parsed.utcoffset().total_seconds() == 0


def test_parse_window_7d() -> None:
    now = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
    start, end = parse_window("7d", now=now)
    assert end == now
    assert (end - start).days == 7


def test_ops_timezone_is_sydney() -> None:
    now = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
    ops = in_ops_tz(now)
    assert str(ops.tzinfo) in {"Australia/Sydney", "AEDT", "AEST"} or ops.tzname() in {"AEDT", "AEST"}
    assert ops.year == 2026
