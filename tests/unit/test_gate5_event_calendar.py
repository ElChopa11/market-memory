"""Gate 5 event blackout loads config/macro/event_calendar.yaml."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from mm_desks.event_calendar import (
    EVENT_CALENDAR_REL,
    Gate5Event,
    blocking_gate5_event,
    load_event_calendar,
)
from mm_desks.monitor import idea_eligible, lockup_inside_horizon, name_by_ticker
from mm_desks.watchlist import run_watchlist_from_fixture

ROOT = Path(__file__).resolve().parents[2]
LOCKED = ROOT / "tests" / "fixtures" / "phase6c4" / "locked_scan.json"
AS_OF = datetime(2026, 9, 19, tzinfo=timezone.utc)
BB_EARNINGS = date(2026, 9, 24)


def _event(**overrides: object) -> Gate5Event:
    payload: dict[str, object] = {
        "event_id": "synthetic",
        "name": "synthetic",
        "kind": "earnings",
        "event_date": BB_EARNINGS,
        "verification": "Verified",
        "gate5_relevant": True,
        "tickers": ("BB",),
        "scope": "",
        "provenance": "test",
    }
    payload.update(overrides)
    return Gate5Event(**payload)  # type: ignore[arg-type]


def test_gate5_blocks_bb_earnings_2026_09_24_when_horizon_crosses() -> None:
    calendar = load_event_calendar(ROOT)
    assert calendar.source_rel == EVENT_CALENDAR_REL.as_posix()
    assert calendar.source_rel == "config/macro/event_calendar.yaml"
    assert any(
        event.verified and event.event_date == BB_EARNINGS and "BB" in event.tickers
        for event in calendar.events
    )

    bb = name_by_ticker("BB", ROOT)
    assert bb is not None
    assert lockup_inside_horizon("BB", AS_OF, ROOT) is False

    blocked, reason = idea_eligible(bb, as_of=AS_OF, repo_root=ROOT, horizon="5d")
    assert blocked is False
    assert "BB earnings 2026-09-24" in reason
    assert "gate 5 (Skeptic) blackout" in reason

    # Default scan window (no stated horizon) also crosses 2026-09-24.
    blocked_default, reason_default = idea_eligible(bb, as_of=AS_OF, repo_root=ROOT)
    assert blocked_default is False
    assert "2026-09-24" in reason_default

    clear, clear_reason = idea_eligible(bb, as_of=AS_OF, repo_root=ROOT, horizon="4d")
    assert clear is True
    assert "blackout" not in clear_reason

    after = datetime(2026, 9, 25, tzinfo=timezone.utc)
    clear_after, _ = idea_eligible(bb, as_of=after, repo_root=ROOT, horizon="10d")
    assert clear_after is True

    nvda = name_by_ticker("NVDA", ROOT)
    assert nvda is not None
    ok_nvda, _ = idea_eligible(nvda, as_of=AS_OF, repo_root=ROOT, horizon="30d")
    assert ok_nvda is True

    scan = run_watchlist_from_fixture(LOCKED, repo_root=ROOT)
    row = next(item for item in scan.rows if item.instrument == "BB")
    assert row.idea_eligible is False
    assert "2026-09-24" in row.idea_reason
    assert "BB earnings 2026-09-24" in row.notes

    cbrs = name_by_ticker("CBRS", ROOT)
    assert cbrs is not None
    assert lockup_inside_horizon("CBRS", AS_OF, ROOT) is True
    cbrs_ok, cbrs_reason = idea_eligible(cbrs, as_of=AS_OF, repo_root=ROOT, horizon="1d")
    assert cbrs_ok is False
    assert cbrs_reason == "lockup inside horizon; gate 5 (Skeptic) blackout"


def test_unverified_or_not_gate5_events_do_not_block() -> None:
    bb = name_by_ticker("BB", ROOT)
    draft = _event(verification="unverified")
    flagged_off = _event(gate5_relevant=False)
    other_name = _event(kind="cpi", gate5_relevant=True, tickers=("NVDA",), name="NVDA print")
    assert blocking_gate5_event(bb, (draft, flagged_off, other_name), as_of=AS_OF, horizon="10d") is None

    market = _event(
        event_id="cpi",
        name="CPI",
        kind="cpi",
        gate5_relevant=True,
        tickers=(),
        scope="market",
    )
    hit = blocking_gate5_event(bb, (market,), as_of=AS_OF, horizon="10d")
    assert hit is not None and hit.event_id == "cpi"
    missed = blocking_gate5_event(bb, (market,), as_of=AS_OF, horizon="4d")
    assert missed is None
