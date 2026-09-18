"""Math primitives for price factors. Stdlib only."""

from __future__ import annotations

import math
from typing import Sequence


def trailing_return(prices: Sequence[float], bars: int) -> float | None:
    """close[-1] / close[-1-bars] - 1. Need bars+1 prices."""
    if bars < 1 or len(prices) < bars + 1:
        return None
    start = prices[-1 - bars]
    end = prices[-1]
    if start == 0:
        return None
    return end / start - 1.0


def realised_vol(returns: Sequence[float], window: int, ann_factor: float) -> float | None:
    if window < 2 or len(returns) < window or ann_factor <= 0:
        return None
    sl = returns[-window:]
    mean = sum(sl) / window
    var = sum((x - mean) ** 2 for x in sl) / (window - 1)
    if var < 0:
        return None
    return math.sqrt(var) * math.sqrt(ann_factor)


def zscore(prices: Sequence[float], window: int) -> float | None:
    if window < 2 or len(prices) < window:
        return None
    sl = prices[-window:]
    mean = sum(sl) / window
    var = sum((x - mean) ** 2 for x in sl) / (window - 1)
    if var <= 0:
        return None
    return (sl[-1] - mean) / math.sqrt(var)


def sma(prices: Sequence[float], window: int) -> float | None:
    if window < 1 or len(prices) < window:
        return None
    sl = prices[-window:]
    return sum(sl) / window


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    n = len(xs)
    if n < 2 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def beta(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """OLS beta of xs on ys (instrument on benchmark)."""
    n = len(xs)
    if n < 2 or n != len(ys):
        return None
    my = sum(ys) / n
    mx = sum(xs) / n
    var_y = sum((y - my) ** 2 for y in ys) / (n - 1)
    if var_y == 0:
        return None
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (n - 1)
    return cov / var_y


def _true_range(high: float, low: float, prev_close: float) -> float:
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def adx_wilder(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int,
) -> float | None:
    """Wilder ADX. Needs period*2 bars of directional data (plus the first close)."""
    n = min(len(highs), len(lows), len(closes))
    if period < 2 or n < period * 2 + 1:
        return None
    trs: list[float] = []
    plus_dm: list[float] = []
    minus_dm: list[float] = []
    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm.append(up if up > down and up > 0 else 0.0)
        minus_dm.append(down if down > up and down > 0 else 0.0)
        trs.append(_true_range(highs[i], lows[i], closes[i - 1]))
    if len(trs) < period * 2:
        return None
    atr = sum(trs[:period])
    pdm = sum(plus_dm[:period])
    mdm = sum(minus_dm[:period])
    dxs: list[float] = []
    for i in range(period, len(trs)):
        atr = atr - atr / period + trs[i]
        pdm = pdm - pdm / period + plus_dm[i]
        mdm = mdm - mdm / period + minus_dm[i]
        if atr == 0:
            continue
        plus_di = 100.0 * pdm / atr
        minus_di = 100.0 * mdm / atr
        denom = plus_di + minus_di
        if denom == 0:
            dxs.append(0.0)
        else:
            dxs.append(100.0 * abs(plus_di - minus_di) / denom)
    if len(dxs) < period:
        return None
    adx = sum(dxs[:period]) / period
    for dx in dxs[period:]:
        adx = (adx * (period - 1) + dx) / period
    return adx
