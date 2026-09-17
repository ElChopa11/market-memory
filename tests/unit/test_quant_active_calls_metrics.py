"""QUANT-20260917 metric helpers — synthetic series only, no network."""

from __future__ import annotations

import math
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parents[2] / "research" / "queue" / "quant-20260917"
sys.path.insert(0, str(PACK))

from metrics import (  # noqa: E402
    log_returns,
    max_drawdown,
    naive_funding_annualized,
    ols_alpha_beta,
    pearson,
    realized_vol,
    total_return,
)


def test_log_returns_and_total_return() -> None:
    prices = [100.0, 110.0, 99.0]
    rets = log_returns(prices)
    assert len(rets) == 2
    assert math.isclose(rets[0], math.log(1.1))
    assert math.isclose(total_return(prices, 2) or 0.0, 99.0 / 100.0 - 1.0)


def test_max_drawdown_peak_to_trough() -> None:
    prices = [100.0, 120.0, 90.0, 95.0]
    dd = max_drawdown(prices)
    assert dd is not None
    assert math.isclose(dd, 90.0 / 120.0 - 1.0)


def test_realized_vol_known_stdev() -> None:
    rets = [0.01, -0.01, 0.01, -0.01]
    vol = realized_vol(rets, window=4, ann_factor=1)
    assert vol is not None
    mean = sum(rets) / 4
    var = sum((x - mean) ** 2 for x in rets) / 3
    assert math.isclose(vol, math.sqrt(var))


def test_ols_beta_and_pearson() -> None:
    x = [1.0, 2.0, 3.0, 4.0]
    y = [2.0, 4.0, 6.0, 8.0]
    alpha, beta = ols_alpha_beta(y, x)
    assert alpha is not None and beta is not None
    assert math.isclose(beta, 2.0)
    assert math.isclose(alpha, 0.0, abs_tol=1e-12)
    assert math.isclose(pearson(x, y) or 0.0, 1.0)


def test_insufficient_history_is_none_not_invented() -> None:
    assert realized_vol([0.01], window=20, ann_factor=252) is None
    assert total_return([1.0, 1.1], 21) is None
    assert max_drawdown([]) is None
    assert pearson([1.0], [1.0]) is None


def test_naive_funding_annualization() -> None:
    assert math.isclose(naive_funding_annualized(0.0001), 0.0001 * 3 * 365)


def test_windowed_cross_corr_uses_trailing_pairs() -> None:
    import run_pack as pack

    dates_aligned = {
        "A": [1.0, 1.1, 1.21, 1.331, 10.0],
        "B": [1.0, 1.1, 1.21, 1.331, 10.0],
    }
    _names, matrix_full, n_full = pack.cross_corr_matrix(dates_aligned, ("A", "B"))
    _names, matrix_w, n_w = pack.cross_corr_matrix(dates_aligned, ("A", "B"), window=2)
    assert n_full == 4
    assert n_w == 2
    assert matrix_full["A"]["B"] is not None
    assert matrix_w["A"]["A"] == 1.0


def test_quant_pack_is_not_a_thesis_workspace() -> None:
    from mm_research_kit.lifecycle import discover_workspaces, is_thesis_workspace

    assert PACK.is_dir()
    assert not is_thesis_workspace(PACK)
    workspaces = discover_workspaces(PACK.parents[1])
    assert PACK not in workspaces
