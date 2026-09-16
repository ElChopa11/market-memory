"""Stale and missing data-quality flags."""

from __future__ import annotations

from datetime import datetime, timezone

from mm_common.enums import DataQuality
from mm_provenance.quality import assess_quality


T0 = datetime(2026, 9, 10, 0, 0, tzinfo=timezone.utc)
T5 = datetime(2026, 9, 10, 0, 5, tzinfo=timezone.utc)


def test_snapshot_older_than_threshold_is_stale() -> None:
    assert (
        assess_quality(ingested_at=T5, published_at=T0, historical=False, stale_after_seconds=120)
        is DataQuality.STALE
    )


def test_fresh_snapshot_is_ok() -> None:
    assert (
        assess_quality(ingested_at=T0, published_at=T0, historical=False, stale_after_seconds=120)
        is DataQuality.OK
    )


def test_historical_series_not_stale_just_because_old() -> None:
    assert (
        assess_quality(ingested_at=T5, published_at=T0, historical=True, stale_after_seconds=120)
        is DataQuality.OK
    )


def test_missing_fields_are_partial() -> None:
    assert (
        assess_quality(
            ingested_at=T0,
            published_at=T0,
            missing_fields=("openInterest",),
            stale_after_seconds=120,
        )
        is DataQuality.PARTIAL
    )
