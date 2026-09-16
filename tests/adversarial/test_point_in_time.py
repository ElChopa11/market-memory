"""Adversarial: point-in-time replay cannot see future bars or observations."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from mm_backtest.errors import PointInTimeError
from mm_backtest.harness import run_backtest
from mm_backtest.loaders import load_fixture_file
from mm_backtest.pit import PointInTimeView, visible_bars, visible_facts
from mm_backtest.strategy import BuyHoldStrategy
from mm_common.time import parse_utc

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "tests" / "fixtures" / "backtest" / "clean_bars.json"


def test_view_hides_future_bars_and_observations() -> None:
    bars, facts, _meta = load_fixture_file(CLEAN)
    as_of = parse_utc("2026-09-01T01:00:00Z")
    view = PointInTimeView.at(as_of=as_of, instrument="BTC", bars=bars, facts=facts)
    assert len(view.bars) == 1
    assert view.last is not None
    assert view.last.available_at == as_of
    assert [fact.id for fact in view.observations] == ["obs-known"]
    with pytest.raises(PointInTimeError, match="future bars"):
        view.future_bars()
    with pytest.raises(PointInTimeError, match="future observations"):
        view.future_observations()
    with pytest.raises(PointInTimeError, match="future bars"):
        view.bar_at_or_before(parse_utc("2026-09-01T06:00:00Z"))


def test_delayed_ingest_is_not_visible_before_available_at() -> None:
    bars, facts, _ = load_fixture_file(CLEAN)
    delayed = bars[1].model_copy(update={"available_at": parse_utc("2026-09-01T04:00:00Z")})
    series = [bars[0], delayed, *bars[2:]]
    mid = parse_utc("2026-09-01T02:00:00Z")
    visible = visible_bars(series, mid)
    assert bars[0] in visible
    assert delayed not in visible
    assert delayed.market_time <= mid
    known = visible_facts(facts, parse_utc("2026-09-01T03:00:00Z"))
    assert [fact.id for fact in known] == ["obs-known"]
    later = visible_facts(facts, parse_utc("2026-09-01T06:00:00Z"))
    assert {fact.id for fact in later} == {"obs-known", "obs-future"}


def test_backtest_equity_curve_as_of_never_exceeds_clock() -> None:
    bars, facts, _ = load_fixture_file(CLEAN)
    result = run_backtest(bars, BuyHoldStrategy(), facts=facts)
    for point, bar in zip(result.equity_curve, bars, strict=True):
        assert point.as_of == bar.available_at
        assert point.as_of <= bars[-1].available_at
    assert result.fills[0].as_of == bars[0].available_at
    assert all(fill.as_of <= bars[-1].available_at for fill in result.fills)


def test_knowledge_watermark_is_available_at_not_market_time() -> None:
    """A close that already happened but was not ingested must stay hidden."""
    bars, _facts, _ = load_fixture_file(CLEAN)
    early_clock = datetime(2026, 9, 1, 3, 30, tzinfo=timezone.utc)
    leaked_if_using_market_time = [bar for bar in bars if bar.market_time <= early_clock]
    visible = visible_bars(bars, early_clock)
    assert [bar.available_at for bar in visible] == [bar.available_at for bar in leaked_if_using_market_time]
    delayed = bars[2].model_copy(update={"available_at": parse_utc("2026-09-01T08:00:00Z")})
    mixed = [*bars[:2], delayed]
    visible_mixed = visible_bars(mixed, early_clock)
    assert delayed not in visible_mixed
    assert delayed.market_time <= early_clock
