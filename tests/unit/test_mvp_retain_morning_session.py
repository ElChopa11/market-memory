"""Morning retain equity session_date matches the brief T-1 header.

C4 (2026-09-30 16:30 ET) stamped the last completed cash session. The brief
qualifies the weekday before that New York date. ``_qualify`` stays strict.
``run_proof_capture`` still requests the last completed cash session.
"""

from __future__ import annotations

import importlib.util
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from mm_briefing.equity_close_lines import (
    RANK_ELIGIBLE_EQUITIES,
    _qualify,
    equity_close_print,
)
from mm_briefing.morning import expected_equity_session as print_equity_session
from mm_common.http import ERROR_NONE
from mm_common.time import expected_equity_session
from mm_ingest.mvp_retain import (
    load_mvp_retain_spec,
    run_morning_capture,
    run_proof_capture,
    us_cash_session_date,
)

UTC = timezone.utc
NY = ZoneInfo("America/New_York")
ROOT_TEST = Path(__file__).resolve().parents[2]
PROOF_ID = "11111111-1111-4111-8111-111111111111"
# C4 capture instant: 2026-10-01 06:30:37 AEST == 2026-09-30 16:30:37 ET.
C4 = datetime(2026, 9, 30, 16, 30, 37, tzinfo=NY)

# (label, fetch clock, T-1 header, last completed cash session)
CLOCKS = [
    ("c4_1630_et", C4, date(2026, 9, 29), date(2026, 9, 30)),
    ("close_bell_1600_et", datetime(2026, 9, 30, 16, 0, 0, tzinfo=NY), date(2026, 9, 29), date(2026, 9, 30)),
    ("pre_close_1500_et", datetime(2026, 9, 30, 15, 0, 0, tzinfo=NY), date(2026, 9, 29), date(2026, 9, 29)),
    ("sunday_1630_et", datetime(2026, 9, 27, 16, 30, 0, tzinfo=NY), date(2026, 9, 25), date(2026, 9, 25)),
    ("monday_1632_et", datetime(2026, 9, 28, 16, 32, 0, tzinfo=NY), date(2026, 9, 25), date(2026, 9, 28)),
    ("friday_1630_et", datetime(2026, 10, 2, 16, 30, 0, tzinfo=NY), date(2026, 10, 1), date(2026, 10, 2)),
    ("thursday_1630_et", datetime(2026, 10, 1, 16, 30, 37, tzinfo=NY), date(2026, 9, 30), date(2026, 10, 1)),
]


class _Store:
    def __init__(self) -> None:
        self.last_envelopes: list = []

    def count_for_anchor(self, anchor_date: str) -> int:
        return 0

    def prior_captured_at(self, anchor_date: str, before: str) -> str | None:
        return None

    def persist(self, envelopes) -> None:
        self.last_envelopes = list(envelopes)

    def count_for_captured_at(self, captured_at: str) -> int:
        return len(self.last_envelopes)

    def count_for_capture_id(self, capture_id: str) -> int:
        return len(self.last_envelopes)


class _HL:
    def meta_and_asset_ctxs(self):
        return []

    def spot_meta_and_asset_ctxs(self):
        return []

    def close(self) -> None:
        return None


class _Poly:
    def __init__(self, symbols: tuple[str, ...]) -> None:
        self.symbols = symbols
        self.dates: list[date] = []

    def grouped_daily(self, session_date: date):
        self.dates.append(session_date)
        bar = datetime(session_date.year, session_date.month, session_date.day, 20, 0, tzinfo=UTC)
        bar_ms = int(bar.timestamp() * 1000)
        results = [
            {"T": ticker, "c": 100 + index, "t": bar_ms}
            for index, ticker in enumerate(self.symbols)
        ]
        return {"results": results}, ERROR_NONE

    def close(self) -> None:
        return None


def _closes(store: _Store) -> list:
    return [env for env in store.last_envelopes if env.metric == "close"]


def _dumped(store: _Store) -> list[dict]:
    return [env.model_dump(mode="json") for env in _closes(store)]


@pytest.mark.parametrize(("label", "clock", "header", "last_completed"), CLOCKS, ids=[row[0] for row in CLOCKS])
def test_morning_retain_stamps_expected_equity_session(label: str, clock: datetime, header: date, last_completed: date) -> None:
    """Morning equity session_date follows the T-1 header across fetch clocks."""
    assert print_equity_session(clock) == header, label
    assert expected_equity_session(clock) == header
    assert us_cash_session_date(clock) == last_completed
    spec = load_mvp_retain_spec()
    store = _Store()
    poly = _Poly(spec.equity_symbols)
    result = run_morning_capture(
        scheduled_for="2026-09-30T20:30:00Z",
        now=clock,
        timeout_s=5,
        store=store,
        hl_client=_HL(),
        polygon_adapter=poly,
    )
    assert result.wrote is True
    assert poly.dates == [header]
    assert {env.payload["session_date"] for env in _closes(store)} == {header.isoformat()}
    printed = equity_close_print(_dumped(store), header_date=header)
    assert [line.split(" ", 1)[0] for line in printed.lines] == list(RANK_ELIGIBLE_EQUITIES)
    assert printed.missing == ()


def test_c4_1630_et_refuses_last_completed_session_against_t1_header() -> None:
    """C4 post-close: retain stores 2026-09-29; a 2026-09-30 stamp stays a gap."""
    header = date(2026, 9, 29)
    last_completed = date(2026, 9, 30)
    assert C4.isoformat() == "2026-09-30T16:30:37-04:00"
    assert expected_equity_session(C4) == print_equity_session(C4) == header
    assert us_cash_session_date(C4) == last_completed
    spec = load_mvp_retain_spec()
    store = _Store()
    poly = _Poly(spec.equity_symbols)
    result = run_morning_capture(
        scheduled_for="2026-09-30T20:30:00Z",
        now=C4,
        timeout_s=5,
        store=store,
        hl_client=_HL(),
        polygon_adapter=poly,
    )
    assert result.wrote is True
    assert poly.dates == [header]
    rows = _dumped(store)
    ranked = [row for row in rows if str(row.get("instrument") or "").upper() in RANK_ELIGIBLE_EQUITIES]
    assert len(ranked) == 16
    for row in ranked:
        assert _qualify(row, header_date=header) is not None
        assert row["payload"]["session_date"] == "2026-09-29"
    refused = []
    for row in ranked:
        stamped = dict(row)
        payload = dict(stamped["payload"])
        payload["session_date"] = last_completed.isoformat()
        stamped["payload"] = payload
        stamped["market_time"] = "2026-09-30T20:00:00+00:00"
        assert _qualify(stamped, header_date=header) is None
        refused.append(stamped)
    gaps = equity_close_print(refused, header_date=header)
    assert gaps.lines == ()
    assert gaps.missing == RANK_ELIGIBLE_EQUITIES


def test_qualify_refuses_header_mismatch_and_market_time_mismatch() -> None:
    """The gate still requires session_date == header_date == market_time's UTC date."""
    header = date(2026, 9, 29)
    session_only = {
        "instrument": "NVDA",
        "metric": "close",
        "market_time": "2026-09-30T20:00:00+00:00",
        "source_name": "polygon",
        "source_url_or_id": "grouped_daily:NVDA",
        "payload": {
            "value": "180.12",
            "session_date": "2026-09-29",
            "resolution": "grouped_daily",
            "capture_kind": "lab_snapshot",
        },
    }
    assert _qualify(session_only, header_date=header) is None
    market_only = {
        "instrument": "NVDA",
        "metric": "close",
        "market_time": "2026-09-29T20:00:00+00:00",
        "source_name": "polygon",
        "source_url_or_id": "grouped_daily:NVDA",
        "payload": {
            "value": "180.12",
            "session_date": "2026-09-30",
            "resolution": "grouped_daily",
            "capture_kind": "lab_snapshot",
        },
    }
    assert _qualify(market_only, header_date=header) is None
    both_wrong = {
        "instrument": "TSLA",
        "metric": "close",
        "market_time": "2026-09-30T20:00:00+00:00",
        "source_name": "polygon",
        "source_url_or_id": "grouped_daily:TSLA",
        "payload": {
            "value": "200",
            "session_date": "2026-09-30",
            "resolution": "grouped_daily",
            "capture_kind": "lab_snapshot",
        },
    }
    assert _qualify(both_wrong, header_date=header) is None
    printed = equity_close_print([session_only, market_only, both_wrong], header_date=header)
    assert printed.lines == ()
    assert "NVDA" in printed.missing
    assert "TSLA" in printed.missing


def test_run_proof_capture_keeps_us_cash_session_date() -> None:
    """run_proof_capture at the C4 clock still requests the last completed session."""
    last_completed = date(2026, 9, 30)
    header = date(2026, 9, 29)
    assert us_cash_session_date(C4) == last_completed
    assert expected_equity_session(C4) == header
    spec = load_mvp_retain_spec()
    store = _Store()
    poly = _Poly(spec.equity_symbols)
    result = run_proof_capture(
        now=C4,
        scheduled_for="2026-09-30T20:30:00Z",
        timeout_s=5,
        store=store,
        hl_client=_HL(),
        polygon_adapter=poly,
        capture_id=PROOF_ID,
    )
    assert result.wrote is True
    assert result.capture_id == PROOF_ID
    assert poly.dates == [last_completed]
    assert {env.payload["session_date"] for env in _closes(store)} == {last_completed.isoformat()}
    assert all(env.payload.get("capture_kind") == "proof" for env in _closes(store))


def test_c1_c3_set1_and_format_freeze_hash_locks_stay() -> None:
    """Set1 receipts and the format-freeze dry-run stay on the #145 hash locks."""
    path = ROOT_TEST / "tests" / "unit" / "test_equity_close_lines.py"
    spec = importlib.util.spec_from_file_location("equity_close_lock", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.test_set1_bodies_and_format_freeze_artifact_stay()
