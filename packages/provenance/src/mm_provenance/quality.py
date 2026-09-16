"""Data-quality flags: stale (old when ingested) and partial (missing fields)."""

from __future__ import annotations

from datetime import datetime, timedelta

from mm_common.enums import DataQuality
from mm_common.time import as_utc


def assess_quality(
    *,
    ingested_at: datetime,
    published_at: datetime | None,
    missing_fields: tuple[str, ...] | list[str] = (),
    historical: bool = False,
    stale_after_seconds: int = 120,
    current_quality: DataQuality = DataQuality.OK,
) -> DataQuality:
    """Flag stale/missing data. Historical series are facts about the past, not stale.

    For snapshot polls, *published_at* is lab capture time (not an exchange event clock).
    """
    if current_quality in {DataQuality.REJECTED, DataQuality.CONTRADICTED}:
        return current_quality
    if missing_fields:
        return DataQuality.PARTIAL
    if historical:
        return current_quality
    if published_at is None:
        return DataQuality.PARTIAL
    ingested = as_utc(ingested_at)
    published = as_utc(published_at)
    if ingested - published > timedelta(seconds=stale_after_seconds):
        return DataQuality.STALE
    return current_quality
