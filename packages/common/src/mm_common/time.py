"""UTC datetime helpers. Naive datetimes are rejected.

``expected_equity_session`` is the morning equity T-1 date: the weekday before
the America/New_York calendar date. It is lockstep with
``mm_briefing.morning.expected_equity_session`` (that module stays the print
copy; tests assert the two dates match).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc
OPS_TZ = ZoneInfo("Australia/Sydney")
NY_TZ = ZoneInfo("America/New_York")


def utcnow() -> datetime:
    return datetime.now(UTC)


def in_ops_tz(value: datetime | None = None) -> datetime:
    """Display/ops timezone (Australia/Sydney). Storage remains UTC timestamptz."""
    return as_utc(value or utcnow()).astimezone(OPS_TZ)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("naive datetime is forbidden; store timestamptz UTC")
    return value.astimezone(UTC)


def from_unix_ms(ms: int | float) -> datetime:
    return datetime.fromtimestamp(int(ms) / 1000, tz=UTC)


def to_unix_ms(value: datetime) -> int:
    return int(as_utc(value).timestamp() * 1000)


def parse_utc(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    return as_utc(parsed)


def parse_window(spec: str, *, now: datetime | None = None) -> tuple[datetime, datetime]:
    """Parse ``7d`` / ``24h`` / ``60m`` into an inclusive UTC window ending at *now*."""
    end = as_utc(now or utcnow())
    spec = spec.strip().lower()
    if not spec:
        raise ValueError("empty window")
    unit = spec[-1]
    try:
        amount = int(spec[:-1])
    except ValueError as exc:
        raise ValueError(f"invalid window {spec!r}") from exc
    if amount <= 0:
        raise ValueError("window must be positive")
    if unit == "d":
        delta = timedelta(days=amount)
    elif unit == "h":
        delta = timedelta(hours=amount)
    elif unit == "m":
        delta = timedelta(minutes=amount)
    else:
        raise ValueError(f"unsupported window unit in {spec!r}; use Nd, Nh, or Nm")
    return end - delta, end


def expected_equity_session(knowledge_as_of: datetime) -> date:
    """Weekday before the New York calendar date of this instant.

    Same rule as ``mm_briefing.morning.expected_equity_session``, which the
    brief header and equity qualification already use. Morning retain stamps
    this date onto equity ``session_date``. Weekends are not sessions. There
    is no holiday list. Clock time on a given New York date does not change
    the result.
    """
    day = as_utc(knowledge_as_of).astimezone(NY_TZ).date() - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day
