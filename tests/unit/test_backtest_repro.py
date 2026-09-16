"""Same params_hash → same backtest result (JSON and parquet)."""

from __future__ import annotations

from pathlib import Path

from mm_backtest.harness import run_backtest
from mm_backtest.loaders import load_fixture_file, write_parquet
from mm_backtest.params import params_hash
from mm_backtest.strategy import BuyHoldStrategy, ThresholdStrategy, build_strategy

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "tests" / "fixtures" / "backtest" / "clean_bars.json"


def test_same_params_hash_same_result() -> None:
    bars, facts, _ = load_fixture_file(CLEAN)
    first = run_backtest(bars, BuyHoldStrategy(), facts=facts, slippage_bps="5")
    second = run_backtest(bars, BuyHoldStrategy(), facts=facts, slippage_bps="5")
    assert first.params_hash == second.params_hash
    assert first.result_hash == second.result_hash
    assert first.metrics == second.metrics
    assert [fill.canonical() for fill in first.fills] == [fill.canonical() for fill in second.fills]
    assert first.canonical_result() == second.canonical_result()


def test_param_change_changes_hash_and_result() -> None:
    bars, facts, _ = load_fixture_file(CLEAN)
    hold = run_backtest(bars, BuyHoldStrategy(), facts=facts)
    threshold = run_backtest(bars, ThresholdStrategy(threshold="102"), facts=facts)
    assert hold.params_hash != threshold.params_hash
    assert hold.result_hash != threshold.result_hash
    assert hold.metrics["n_fills"] == "1"
    assert int(threshold.metrics["n_fills"]) >= 1


def test_parquet_roundtrip_matches_json_params_hash(tmp_path: Path) -> None:
    bars, facts, _ = load_fixture_file(CLEAN)
    parquet_path = tmp_path / "clean.parquet"
    write_parquet(parquet_path, bars)
    parquet_bars, _parquet_facts, _ = load_fixture_file(parquet_path)
    json_result = run_backtest(bars, build_strategy("buy_hold"), facts=facts)
    parquet_result = run_backtest(parquet_bars, build_strategy("buy_hold"), facts=facts)
    assert json_result.params_hash == parquet_result.params_hash
    assert json_result.result_hash == parquet_result.result_hash


def test_params_hash_helper_is_stable() -> None:
    payload = {"strategy": "buy_hold", "qty": "1", "instrument": "BTC"}
    assert params_hash(payload) == params_hash(dict(reversed(list(payload.items()))))
