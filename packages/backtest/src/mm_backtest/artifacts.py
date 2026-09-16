"""Write backtest artifacts (JSON) under a thesis `backtests/` folder or --out."""

from __future__ import annotations

import json
from pathlib import Path

from mm_backtest.harness import BacktestResult
from mm_common.hashing import canonical_json


def artifact_filename(params_hash: str) -> str:
    return f"{params_hash[:16]}.json"


def write_backtest_artifact(result: BacktestResult, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / artifact_filename(result.params_hash)
    payload = {
        "params_hash": result.params_hash,
        "result_hash": result.result_hash,
        "bars_hash": result.bars_hash,
        "strategy": result.strategy,
        "instrument": result.instrument,
        "params": result.params,
        "metrics": result.metrics,
        "fills": [fill.canonical() for fill in result.fills],
        "equity_curve": [point.canonical() for point in result.equity_curve],
    }
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    return path


def read_backtest_artifact(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
