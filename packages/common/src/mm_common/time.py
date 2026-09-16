"""UTC-only datetime helpers. Naive datetimes are rejected."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

UTC = timezone.utc


def utcnow() -> datetime:
    return datetime.now(UTC)


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
