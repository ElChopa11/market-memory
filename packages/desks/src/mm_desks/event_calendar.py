"""Skeptic gate 5 event blackout from config/macro/event_calendar.yaml.

Verified earnings, and other verified gate5_relevant events, block a candidate
when the candidate horizon crosses the event date. Lockup blackout stays in
mm_desks.monitor and is not decided here.

This module is the only loader of the live event calendar. The March pulse
fixture config/briefing/calendar.yaml is not a gate source.
# Boundary comment: packages here must not import mm_execution (statement form is gated).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from mm_common.time import as_utc
from mm_desks.invalidation import parse_horizon_days

EVENT_CALENDAR_REL = Path("config/macro/event_calendar.yaml")
DEFAULT_HORIZON_DAYS = 10

_VERIFIED = "verified"
_EARNINGS_KINDS = frozenset({"earnings"})
_MARKET_SCOPES = frozenset({"market", "all", "*"})


@dataclass(frozen=True)
class Gate5Event:
    event_id: str
    name: str
    kind: str
    event_date: date
    verification: str
    gate5_relevant: bool
    tickers: tuple[str, ...]
    scope: str
    provenance: str

    @property
    def verified(self) -> bool:
        return self.verification.strip().lower() == _VERIFIED

    def applies_to(self, subject: Any) -> bool:
        if self.scope in _MARKET_SCOPES and not self.tickers:
            return True
        if not self.tickers:
            return False
        return bool(set(self.tickers) & _subject_keys(subject))


@dataclass(frozen=True)
class EventCalendar:
    source_rel: str
    version: str
    default_horizon_days: int
    events: tuple[Gate5Event, ...]


def _subject_keys(subject: Any) -> set[str]:
    if isinstance(subject, str):
        text = subject.strip()
        return {text.upper()} if text else set()
    keys: set[str] = set()
    for attr in ("ticker", "membership_key", "tape_alias", "qualified_id"):
        value = getattr(subject, attr, None)
        if value:
            keys.add(str(value).strip().upper())
    return keys


def _parse_day(value: Any) -> date | None:
    if value is None or value in {"", "unresolved", "unavailable"}:
        return None
    if isinstance(value, datetime):
        return as_utc(value).date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _as_bool(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return default


def _tickers(raw: dict[str, Any]) -> tuple[str, ...]:
    found: list[str] = []
    for key in ("ticker", "qualified_id", "symbol"):
        value = raw.get(key)
        if value not in (None, "", "unresolved"):
            found.append(str(value).strip().upper())
    extra = raw.get("tickers") or raw.get("names") or ()
    if isinstance(extra, str):
        extra = [extra]
    if isinstance(extra, (list, tuple)):
        for item in extra:
            if item not in (None, "", "unresolved"):
                found.append(str(item).strip().upper())
    # Preserve order, drop duplicates.
    seen: set[str] = set()
    out: list[str] = []
    for item in found:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def _event_from_raw(raw: dict[str, Any], *, index: int) -> Gate5Event:
    event_id = str(raw.get("event_id") or raw.get("id") or f"event-{index}").strip()
    event_day = _parse_day(raw.get("event_date") or raw.get("date") or raw.get("when"))
    if event_day is None:
        raise ValueError(f"event calendar row {event_id} missing event_date")
    kind = str(raw.get("kind") or raw.get("event_type") or raw.get("type") or "").strip().lower()
    explicit = raw.get("gate5_relevant")
    if kind in _EARNINGS_KINDS:
        relevant = _as_bool(explicit, default=True)
    else:
        relevant = _as_bool(explicit, default=False)
    scope = str(raw.get("scope") or "").strip().lower()
    provenance = raw.get("provenance") or raw.get("notes") or ""
    if isinstance(provenance, (list, tuple)):
        provenance = " ".join(str(item) for item in provenance)
    return Gate5Event(
        event_id=event_id,
        name=str(raw.get("name") or kind or event_id).strip(),
        kind=kind,
        event_date=event_day,
        verification=str(raw.get("verification") or raw.get("status") or "").strip(),
        gate5_relevant=relevant,
        tickers=_tickers(raw),
        scope=scope,
        provenance=str(provenance).strip(),
    )


def _empty(source_rel: str) -> EventCalendar:
    return EventCalendar(
        source_rel=source_rel,
        version="",
        default_horizon_days=DEFAULT_HORIZON_DAYS,
        events=(),
    )


@lru_cache(maxsize=8)
def _load_cached(repo_root: str) -> EventCalendar:
    path = Path(repo_root) / EVENT_CALENDAR_REL
    rel = EVENT_CALENDAR_REL.as_posix()
    if not path.is_file():
        return _empty(rel)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{rel} must be a mapping")
    if data.get("send"):
        raise ValueError(f"{rel} must not enable send")
    if data.get("promote"):
        raise ValueError(f"{rel} must not enable promotion")
    if data.get("llm"):
        raise ValueError(f"{rel} must not enable LLM")
    if "paper_only" in data and not _as_bool(data.get("paper_only"), default=True):
        raise ValueError(f"{rel} must stay paper_only")
    owner = str(data.get("owner") or "intel").strip().lower()
    if owner != "intel":
        raise ValueError(f"{rel} owner must be intel")
    days_raw = data.get("default_horizon_days")
    if days_raw is None:
        default_days = DEFAULT_HORIZON_DAYS
    else:
        default_days = int(days_raw)
        if default_days < 0:
            raise ValueError(f"{rel} default_horizon_days must be >= 0")
    rows = data.get("events") or []
    if not isinstance(rows, list):
        raise ValueError(f"{rel} events must be a list")
    events: list[Gate5Event] = []
    seen: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise ValueError(f"{rel} event {index} must be a mapping")
        event = _event_from_raw(raw, index=index)
        if event.event_id in seen:
            raise ValueError(f"duplicate event_id {event.event_id}")
        seen.add(event.event_id)
        events.append(event)
    events.sort(key=lambda row: (row.event_date, row.name, row.event_id))
    return EventCalendar(
        source_rel=rel,
        version=str(data.get("version") or ""),
        default_horizon_days=default_days,
        events=tuple(events),
    )


def load_event_calendar(repo_root: Path) -> EventCalendar:
    """Load the sole live gate-5 event calendar. Missing file yields no events."""
    return _load_cached(str(Path(repo_root).resolve()))


def horizon_end(as_of: datetime, horizon: Any, *, default_horizon_days: int) -> date:
    """Inclusive end date of the candidate window."""
    start = as_utc(as_of).date()
    if horizon is None or horizon == "":
        return start + timedelta(days=int(default_horizon_days))
    if isinstance(horizon, datetime):
        return as_utc(horizon).date()
    if isinstance(horizon, date):
        return horizon
    if isinstance(horizon, (int, float)) and not isinstance(horizon, bool):
        return start + timedelta(days=float(horizon))
    text = str(horizon).strip()
    if not text:
        return start + timedelta(days=int(default_horizon_days))
    days = parse_horizon_days(text)
    if days is not None:
        return start + timedelta(days=float(days))
    parsed = _parse_day(text)
    if parsed is None:
        raise ValueError(f"unusable candidate horizon {horizon!r}")
    return parsed


def blocking_gate5_event(
    subject: Any,
    events: tuple[Gate5Event, ...] | list[Gate5Event],
    *,
    as_of: datetime,
    horizon: Any = None,
    default_horizon_days: int = DEFAULT_HORIZON_DAYS,
) -> Gate5Event | None:
    """First verified in-horizon gate-5 event that applies to this candidate."""
    start = as_utc(as_of).date()
    end = horizon_end(as_of, horizon, default_horizon_days=default_horizon_days)
    if end < start:
        return None
    chosen: Gate5Event | None = None
    for event in events:
        if not event.verified or not event.gate5_relevant:
            continue
        if event.event_date < start or event.event_date > end:
            continue
        if not event.applies_to(subject):
            continue
        if chosen is None or (event.event_date, event.name) < (chosen.event_date, chosen.name):
            chosen = event
    return chosen


def event_blackout_reason(
    subject: Any,
    *,
    as_of: datetime,
    repo_root: Path,
    horizon: Any = None,
) -> str | None:
    """Reason string when gate 5 blocks on the live event calendar. None when clear."""
    calendar = load_event_calendar(repo_root)
    event = blocking_gate5_event(
        subject,
        calendar.events,
        as_of=as_of,
        horizon=horizon,
        default_horizon_days=calendar.default_horizon_days,
    )
    if event is None:
        return None
    return (
        f"{event.name} {event.event_date.isoformat()} inside horizon; "
        "gate 5 (Skeptic) blackout"
    )
