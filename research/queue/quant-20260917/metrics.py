"""Pure metric helpers for the QUANT-20260917 active-calls pack.

Stdlib only. No network. No invented fills — callers must pass observed prices.
Sample standard deviation uses ddof=1. Pearson uses the cosine-of-demeaned form.
"""

from __future__ import annotations

import math
from typing import Sequence

EQUITY_ANN_FACTOR = 252
CRYPTO_ANN_FACTOR = 365

EQUITY_1M_BARS = 21
EQUITY_3M_BARS = 63
EQUITY_1Y_BARS = 252

CRYPTO_1M_BARS = 30
CRYPTO_3M_BARS = 90
CRYPTO_1Y_BARS = 365

RV_WINDOWS = (20, 60)


def log_returns(prices: Sequence[float]) -> list[float]:
    out: list[float] = []
    for prev, price in zip(prices, prices[1:]):
        if prev <= 0 or price <= 0:
            raise ValueError("prices must be positive to take log returns")
        out.append(math.log(price / prev))
    return out


def sample_std(values: Sequence[float], *, ddof: int = 1) -> float | None:
    n = len(values)
    if n <= ddof:
        return None
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / (n - ddof)
    if var < 0:
        return None
    return math.sqrt(var)


def realized_vol(returns: Sequence[float], window: int, ann_factor: int, *, ddof: int = 1) -> float | None:
    if window < 2 or len(returns) < window:
        return None
    std = sample_std(returns[-window:], ddof=ddof)
    if std is None:
        return None
    return std * math.sqrt(ann_factor)


def total_return(prices: Sequence[float], lookback_bars: int) -> float | None:
    """End / start - 1 using `lookback_bars` steps (needs lookback_bars + 1 prices)."""
    need = lookback_bars + 1
    if lookback_bars < 1 or len(prices) < need:
        return None
    start = prices[-need]
    end = prices[-1]
    if start <= 0:
        return None
    return end / start - 1.0


def max_drawdown(prices: Sequence[float]) -> float | None:
    """Peak-to-trough drawdown on the supplied window (negative or zero)."""
    if not prices:
        return None
    peak = prices[0]
    worst = 0.0
    for price in prices:
        if price <= 0:
            return None
        if price > peak:
            peak = price
        dd = price / peak - 1.0
        if dd < worst:
            worst = dd
    return worst


def trailing(prices: Sequence[float], n: int) -> list[float]:
    if n <= 0:
        return []
    if len(prices) <= n:
        return list(prices)
    return list(prices[-n:])


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0.0 or dy == 0.0:
        return None
    return num / (dx * dy)


def ols_alpha_beta(y: Sequence[float], x: Sequence[float]) -> tuple[float | None, float | None]:
    """Ordinary least squares: y = alpha + beta * x."""
    if len(x) != len(y) or len(x) < 3:
        return None, None
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    varx = sum((xi - mx) ** 2 for xi in x)
    if varx == 0.0:
        return None, None
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    beta = cov / varx
    alpha = my - beta * mx
    return alpha, beta


def naive_funding_annualized(rate_8h: float) -> float:
    """Simple 8h → year scale (rate * 3 * 365). Not a forecast."""
    return rate_8h * 3.0 * 365.0
