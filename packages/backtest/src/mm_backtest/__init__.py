"""Reproducible evaluation harness (Phase 4). Must not submit live orders or leak future data."""

from mm_backtest.artifacts import write_backtest_artifact
from mm_backtest.errors import BacktestError, FixtureLookAheadError, LookAheadError, PointInTimeError
from mm_backtest.harness import BacktestResult, run_backtest
from mm_backtest.leakage import has_lookahead, scan_fixture_for_lookahead
from mm_backtest.loaders import load_fixture_file, load_fixture_payload
from mm_backtest.params import params_hash, result_hash
from mm_backtest.pit import PointInTimeView, visible_bars, visible_facts
from mm_backtest.strategy import BuyHoldStrategy, ThresholdStrategy, build_strategy

__phase__ = 4
LIVE_TRADING_ENABLED = False

__all__ = [
    "BacktestError",
    "BacktestResult",
    "BuyHoldStrategy",
    "FixtureLookAheadError",
    "LIVE_TRADING_ENABLED",
    "LookAheadError",
    "PointInTimeError",
    "PointInTimeView",
    "ThresholdStrategy",
    "build_strategy",
    "has_lookahead",
    "load_fixture_file",
    "load_fixture_payload",
    "params_hash",
    "result_hash",
    "run_backtest",
    "scan_fixture_for_lookahead",
    "visible_bars",
    "visible_facts",
    "write_backtest_artifact",
]
