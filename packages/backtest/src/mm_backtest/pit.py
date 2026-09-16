"""Point-in-time views: only bars/observations with knowledge time <= as_of."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from mm_backtest.bars import Bar, KnowledgeFact
from mm_backtest.errors import PointInTimeError
from mm_common.time import as_utc


def visible_bars(bars: list[Bar] | tuple[Bar, ...], as_of: datetime) -> tuple[Bar, ...]:
    """Bars knowable at *as_of* (`available_at <= as_of`). Never `market_time` alone."""
    watermark = as_utc(as_of)
    return tuple(bar for bar in bars if bar.available_at <= watermark)


def visible_facts(facts: list[KnowledgeFact] | tuple[KnowledgeFact, ...], as_of: datetime) -> tuple[KnowledgeFact, ...]:
    """Observations knowable at *as_of* (`ingested_at <= as_of`)."""
    watermark = as_utc(as_of)
    return tuple(fact for fact in facts if fact.ingested_at <= watermark)


@dataclass(frozen=True)
class PointInTimeView:
    """Replay context at one as-of instant. Future accessors raise."""

    as_of: datetime
    instrument: str
    _bars: tuple[Bar, ...]
    _facts: tuple[KnowledgeFact, ...]

    @classmethod
    def at(
        cls,
        *,
        as_of: datetime,
        instrument: str,
        bars: list[Bar] | tuple[Bar, ...],
        facts: list[KnowledgeFact] | tuple[KnowledgeFact, ...] = (),
    ) -> PointInTimeView:
        watermark = as_utc(as_of)
        return cls(
            as_of=watermark,
            instrument=instrument,
            _bars=visible_bars(bars, watermark),
            _facts=visible_facts(facts, watermark),
        )

    @property
    def bars(self) -> tuple[Bar, ...]:
        return self._bars

    @property
    def observations(self) -> tuple[KnowledgeFact, ...]:
        return self._facts

    @property
    def last(self) -> Bar | None:
        return self._bars[-1] if self._bars else None

    def bar_at_or_before(self, ts: datetime) -> Bar | None:
        watermark = as_utc(ts)
        if watermark > self.as_of:
            raise PointInTimeError("cannot see future bars")
        chosen: Bar | None = None
        for bar in self._bars:
            if bar.available_at <= watermark:
                chosen = bar
        return chosen

    def future_bars(self) -> tuple[Bar, ...]:
        raise PointInTimeError("cannot see future bars")

    def future_observations(self) -> tuple[KnowledgeFact, ...]:
        raise PointInTimeError("cannot see future observations")
