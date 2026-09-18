"""Statistical rigor helpers. Stdlib only. Deterministic when seed is fixed."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Sequence

EULER_MASCHERONI = 0.5772156649015329


@dataclass(frozen=True)
class SampleSize:
    n: int
    status: str
    reason: str = ""


@dataclass(frozen=True)
class TStatResult:
    n: int
    mean: float | None
    t_stat: float | None
    se: float | None
    ci_low: float | None
    ci_high: float | None
    status: str
    reason: str = ""


@dataclass(frozen=True)
class BootstrapCI:
    n: int
    draws: int
    seed: int
    mean: float | None
    ci_low: float | None
    ci_high: float | None
    status: str
    reason: str = ""


@dataclass(frozen=True)
class SharpeResult:
    n: int
    sharpe: float | None
    deflated_sharpe: float | None
    n_trials: int
    status: str
    reason: str = ""


@dataclass(frozen=True)
class WalkForwardSplit:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


@dataclass(frozen=True)
class MaeMfe:
    n: int
    mae: float | None
    mfe: float | None
    status: str
    reason: str = ""


@dataclass(frozen=True)
class Expectancy:
    n: int
    win_rate: float | None
    avg_win: float | None
    avg_loss: float | None
    expectancy: float | None
    status: str
    reason: str = ""


def sample_size(values: Sequence[float]) -> SampleSize:
    n = len(values)
    if n == 0:
        return SampleSize(n=0, status="unavailable", reason="empty series")
    return SampleSize(n=n, status="ok")


def _stdev(values: Sequence[float]) -> float | None:
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values) / (n - 1)
    if var < 0:
        return None
    return math.sqrt(var)


def t_stat(values: Sequence[float], *, z_crit: float = 1.959963984540054) -> TStatResult:
    """Mean t-stat with a normal CI (z_crit default ~95%). Unavailable below n=2."""
    n = len(values)
    if n < 2:
        return TStatResult(
            n=n,
            mean=None,
            t_stat=None,
            se=None,
            ci_low=None,
            ci_high=None,
            status="unavailable",
            reason="need at least 2 observations",
        )
    mean = sum(values) / n
    sd = _stdev(values)
    if sd is None or sd == 0:
        return TStatResult(
            n=n,
            mean=mean,
            t_stat=None,
            se=0.0 if sd == 0 else None,
            ci_low=None,
            ci_high=None,
            status="unavailable",
            reason="zero variance" if sd == 0 else "stdev unavailable",
        )
    se = sd / math.sqrt(n)
    t = mean / se
    return TStatResult(
        n=n,
        mean=mean,
        t_stat=t,
        se=se,
        ci_low=mean - z_crit * se,
        ci_high=mean + z_crit * se,
        status="ok",
    )


def bootstrap_ci(
    values: Sequence[float],
    *,
    draws: int = 500,
    seed: int = 42,
    alpha: float = 0.05,
) -> BootstrapCI:
    n = len(values)
    if n < 2 or draws < 1:
        return BootstrapCI(
            n=n,
            draws=draws,
            seed=seed,
            mean=None,
            ci_low=None,
            ci_high=None,
            status="unavailable",
            reason="need n>=2 and draws>=1",
        )
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(draws):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_idx = min(len(means) - 1, max(0, int(math.floor(alpha / 2 * draws))))
    hi_idx = min(len(means) - 1, max(0, int(math.ceil((1 - alpha / 2) * draws) - 1)))
    return BootstrapCI(
        n=n,
        draws=draws,
        seed=seed,
        mean=sum(values) / n,
        ci_low=means[lo_idx],
        ci_high=means[hi_idx],
        status="ok",
    )


def _norm_ppf(p: float) -> float:
    """Acklam inverse-normal CDF. Domain (0, 1)."""
    if p <= 0.0 or p >= 1.0:
        raise ValueError("p must be in (0, 1)")
    a = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577509590705e02,
        -3.066479806614736e01,
        2.506628277459239e00,
    )
    b = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d = (
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    )
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (
            (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5])
            * q
            / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
        )
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
        (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
    )


def _skew_kurt(values: Sequence[float]) -> tuple[float, float] | None:
    n = len(values)
    if n < 5:
        return None
    mean = sum(values) / n
    m2 = sum((x - mean) ** 2 for x in values) / n
    if m2 <= 0:
        return None
    m3 = sum((x - mean) ** 3 for x in values) / n
    m4 = sum((x - mean) ** 4 for x in values) / n
    skew = m3 / (m2 ** 1.5)
    kurt = m4 / (m2**2)
    return skew, kurt


def sharpe_ratio(returns: Sequence[float], *, periods_per_year: float = 252.0) -> float | None:
    n = len(returns)
    if n < 2:
        return None
    mean = sum(returns) / n
    sd = _stdev(returns)
    if sd is None or sd == 0:
        return None
    return (mean / sd) * math.sqrt(periods_per_year)


def multiple_testing_haircut(sharpe: float, n_tests: int) -> float | None:
    """Bonferroni-style haircut: SR / sqrt(n_tests). Unavailable if n_tests < 1."""
    if n_tests < 1:
        return None
    return sharpe / math.sqrt(n_tests)


def deflated_sharpe(
    returns: Sequence[float],
    *,
    n_trials: int = 1,
    periods_per_year: float = 252.0,
) -> SharpeResult:
    """Bailey & López de Prado (2014) deflated Sharpe, plus a trials haircut.

    n_trials is the number of strategies/tests inspected (multiple-testing).
    Missing moments → unavailable (never invented).
    """
    n = len(returns)
    sr = sharpe_ratio(returns, periods_per_year=periods_per_year)
    if sr is None or n < 5 or n_trials < 1:
        return SharpeResult(
            n=n,
            sharpe=sr,
            deflated_sharpe=None,
            n_trials=n_trials,
            status="unavailable",
            reason="need n>=5, finite Sharpe, n_trials>=1",
        )
    moments = _skew_kurt(returns)
    if moments is None:
        return SharpeResult(
            n=n,
            sharpe=sr,
            deflated_sharpe=None,
            n_trials=n_trials,
            status="unavailable",
            reason="skew/kurtosis unavailable",
        )
    skew, kurt = moments
    non_sr = sr / math.sqrt(periods_per_year)
    variance_sr = (1.0 - skew * non_sr + ((kurt - 1.0) / 4.0) * non_sr**2) / (n - 1)
    if variance_sr <= 0:
        return SharpeResult(
            n=n,
            sharpe=sr,
            deflated_sharpe=None,
            n_trials=n_trials,
            status="unavailable",
            reason="non-positive SR variance",
        )
    sd_sr = math.sqrt(variance_sr)
    # Expected max Sharpe under n_trials (BLP).
    z1 = _norm_ppf(1.0 - 1.0 / n_trials) if n_trials > 1 else 0.0
    z2 = _norm_ppf(1.0 - 1.0 / (n_trials * math.e)) if n_trials > 1 else 0.0
    sr0 = sd_sr * ((1.0 - EULER_MASCHERONI) * z1 + EULER_MASCHERONI * z2)
    dsr = (non_sr - sr0) / sd_sr
    return SharpeResult(
        n=n,
        sharpe=sr,
        deflated_sharpe=dsr,
        n_trials=n_trials,
        status="ok",
    )


def walk_forward_splits(
    n: int,
    *,
    train_min: int,
    test_size: int,
    step: int,
    embargo: int = 0,
) -> tuple[WalkForwardSplit, ...]:
    if n <= 0 or train_min < 1 or test_size < 1 or step < 1 or embargo < 0:
        return ()
    splits: list[WalkForwardSplit] = []
    train_end = train_min
    while True:
        test_start = train_end + embargo
        test_end = test_start + test_size
        if test_end > n:
            break
        splits.append(
            WalkForwardSplit(
                train_start=0,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        train_end += step
    return tuple(splits)


def mae_mfe(prices: Sequence[float], *, entry: float | None = None) -> MaeMfe:
    """Max adverse / max favorable excursion vs entry (first price if omitted)."""
    if len(prices) < 2:
        return MaeMfe(n=len(prices), mae=None, mfe=None, status="unavailable", reason="need >=2 prices")
    px0 = entry if entry is not None else prices[0]
    if px0 == 0:
        return MaeMfe(n=len(prices), mae=None, mfe=None, status="unavailable", reason="zero entry")
    excursions = [p / px0 - 1.0 for p in prices]
    return MaeMfe(
        n=len(prices),
        mae=min(excursions),
        mfe=max(excursions),
        status="ok",
    )


def expectancy(trade_returns: Sequence[float]) -> Expectancy:
    n = len(trade_returns)
    if n == 0:
        return Expectancy(
            n=0,
            win_rate=None,
            avg_win=None,
            avg_loss=None,
            expectancy=None,
            status="unavailable",
            reason="empty trades",
        )
    wins = [x for x in trade_returns if x > 0]
    losses = [x for x in trade_returns if x < 0]
    win_rate = len(wins) / n
    avg_win = (sum(wins) / len(wins)) if wins else 0.0
    avg_loss = (sum(losses) / len(losses)) if losses else 0.0
    exp = win_rate * avg_win + (1.0 - win_rate) * avg_loss
    return Expectancy(
        n=n,
        win_rate=win_rate,
        avg_win=avg_win if wins else None,
        avg_loss=avg_loss if losses else None,
        expectancy=exp,
        status="ok",
    )
