"""Prior-capture reads for the morning brief.

Neon MVP retain rows (`captured_at`, `prior_captured_at`) are wired by a
separate PR (#122). This module is the seam. The brief asks for a metric by
name. Capture 1, a missing `prior_captured_at`, and any read failure are
"no prior": basis stays omitted, and "changed" falls back to non-zero only.
The brief must not fail.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class PriorCaptureValue:
    """One metric from the previous retain capture."""

    instrument: str
    metric: str
    value: float | None
    captured_at: datetime | None = None
    prior_captured_at: datetime | None = None
    # Vendor bar date (equity ``market_time``) or FRED observation date.
    # Absent means the change cell cannot tell whether the print rolled.
    observation_as_of: datetime | None = None


class PriorCaptureReader(Protocol):
    """Read one prior metric. Implementations must not be required for the brief to render."""

    def read(self, instrument: str, metric: str) -> PriorCaptureValue | None:
        """Return the prior value, or None when this metric has no prior capture."""


class NullPriorCaptureReader:
    """Capture 1 and the unwired Neon path. No prior."""

    def read(self, instrument: str, metric: str) -> PriorCaptureValue | None:
        return None


class MapPriorCaptureReader:
    """In-memory reader for tests and for a caller that already loaded retain rows."""

    def __init__(self, values: dict[tuple[str, str], PriorCaptureValue]) -> None:
        self._values = values

    def read(self, instrument: str, metric: str) -> PriorCaptureValue | None:
        return self._values.get((instrument.upper(), metric))


def prior_value_from_retain(
    *,
    instrument: str,
    metric: str,
    value: str | float | None,
    captured_at: datetime | None,
    prior_captured_at: datetime | None,
    observation_as_of: datetime | None = None,
) -> PriorCaptureValue | None:
    """Build a prior reading from a #122 retain row.

    ``prior_captured_at`` absent means capture 1 (or a row that is not a
    consecutive pair). That is no prior, not a zero.
    """
    if prior_captured_at is None:
        return None
    parsed: float | None
    if value is None or value == "":
        parsed = None
    else:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = None
    return PriorCaptureValue(
        instrument=instrument.upper(),
        metric=metric,
        value=parsed,
        captured_at=captured_at,
        prior_captured_at=prior_captured_at,
        observation_as_of=observation_as_of,
    )


def read_prior(
    reader: PriorCaptureReader | None,
    instrument: str,
    metric: str,
) -> PriorCaptureValue | None:
    """Never raises. A missing reader and a failed read are both no prior."""
    if reader is None:
        return None
    try:
        found = reader.read(instrument, metric)
    except Exception:
        return None
    if found is None:
        return None
    if (
        found.prior_captured_at is None
        and found.captured_at is None
        and found.value is None
        and found.observation_as_of is None
    ):
        return None
    return found
