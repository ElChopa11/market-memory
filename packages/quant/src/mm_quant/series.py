"""Point-in-time series filters. Knowledge clock is as_of_knowledge, never market_time."""

from __future__ import annotations

from datetime import datetime

from mm_common.time import as_utc
from mm_quant.models import MarketPanel, SeriesBar, StructurePoint


def visible_bars(
    bars: tuple[SeriesBar, ...] | list[SeriesBar],
    watermark: datetime,
) -> tuple[SeriesBar, ...]:
    cut = as_utc(watermark)
    return tuple(bar for bar in bars if bar.as_of_knowledge <= cut)


def visible_structure(
    points: tuple[StructurePoint, ...] | list[StructurePoint],
    watermark: datetime,
) -> tuple[StructurePoint, ...]:
    cut = as_utc(watermark)
    return tuple(point for point in points if point.as_of_knowledge <= cut)


def visible_panel(panel: MarketPanel, watermark: datetime) -> MarketPanel:
    return MarketPanel(
        bars=visible_bars(panel.bars, watermark),
        structure=visible_structure(panel.structure, watermark),
        fixture_id=panel.fixture_id,
        sector_of=dict(panel.sector_of),
        asset_class_of=dict(panel.asset_class_of),
    )


def bars_for(panel: MarketPanel, instrument: str) -> tuple[SeriesBar, ...]:
    wanted = instrument.upper()
    ordered = [bar for bar in panel.bars if bar.instrument.upper() == wanted]
    ordered.sort(key=lambda bar: (bar.as_of_knowledge, bar.market_time, bar.observation_id or ""))
    return tuple(ordered)


def closes(bars: tuple[SeriesBar, ...]) -> tuple[float, ...]:
    return tuple(bar.close for bar in bars)


def simple_returns(prices: tuple[float, ...] | list[float]) -> tuple[float, ...]:
    out: list[float] = []
    for prev, cur in zip(prices, prices[1:]):
        if prev == 0:
            continue
        out.append(cur / prev - 1.0)
    return tuple(out)


def aligned_return_pairs(
    left: tuple[SeriesBar, ...],
    right: tuple[SeriesBar, ...],
) -> tuple[tuple[float, float], ...]:
    """Pair returns on equal market_time. Does not relax the as_of_knowledge filter."""
    right_by_mt = {}
    for bar in right:
        right_by_mt[bar.market_time] = bar
    left_sorted = sorted(left, key=lambda bar: bar.market_time)
    pairs: list[tuple[float, float]] = []
    prev_l: SeriesBar | None = None
    prev_r: SeriesBar | None = None
    for bar in left_sorted:
        other = right_by_mt.get(bar.market_time)
        if other is None:
            continue
        if prev_l is not None and prev_r is not None and prev_l.close != 0 and prev_r.close != 0:
            pairs.append((bar.close / prev_l.close - 1.0, other.close / prev_r.close - 1.0))
        prev_l, prev_r = bar, other
    return tuple(pairs)


def latest_structure(
    panel: MarketPanel,
    instrument: str,
    metric: str,
) -> StructurePoint | None:
    wanted = instrument.upper()
    matches = [
        point
        for point in panel.structure
        if point.instrument.upper() == wanted and point.metric == metric
    ]
    if not matches:
        return None
    matches.sort(key=lambda point: (point.as_of_knowledge, point.observation_id or ""))
    return matches[-1]
