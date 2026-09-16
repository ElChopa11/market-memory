"""CLI: lab backtest run and lab paper open/close/list."""

from __future__ import annotations

import json
from pathlib import Path

from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "tests" / "fixtures" / "backtest" / "clean_bars.json"
LOOKAHEAD = ROOT / "tests" / "fixtures" / "backtest" / "lookahead_bars.json"
TEMPLATES = ROOT / "templates"


def _research_args(tmp_path: Path) -> list[str]:
    return [
        "--research-root",
        str(tmp_path / "research"),
        "--templates-root",
        str(TEMPLATES),
        "--repo-root",
        str(tmp_path),
        "--no-db",
    ]


def _ready_thesis(tmp_path: Path) -> str:
    common = _research_args(tmp_path)
    assert main(["thesis", "new", "--goal", "BTC fade", "--owner", "Research", "--instrument", "BTC", *common]) == 0
    # slug THESIS-0001
    slug = "THESIS-0001"
    assert main(["thesis", "link-evidence", slug, "--observation", "01ARZ3NDEKTSV4RRFFQ69G5FAV", "--role", "supports", *common]) == 0
    assert main(["skeptic", "record", slug, "--verdict", "pass", "--reviewer", "Skeptic", *common]) == 0
    return slug


def test_lab_backtest_run_is_reproducible(tmp_path: Path, capsys) -> None:
    out_dir = tmp_path / "bt"
    args = [
        "backtest",
        "run",
        "--fixture",
        str(CLEAN),
        "--strategy",
        "buy_hold",
        "--out",
        str(out_dir),
        "--no-db",
    ]
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert main(args) == 0
    second = json.loads(capsys.readouterr().out)
    assert first["params_hash"] == second["params_hash"]
    assert first["result_hash"] == second["result_hash"]
    assert (out_dir / f"{first['params_hash'][:16]}.json").is_file()


def test_lab_backtest_refuses_lookahead_fixture(capsys) -> None:
    rc = main(["backtest", "run", "--fixture", str(LOOKAHEAD), "--no-db"])
    assert rc == 2
    assert "look-ahead" in capsys.readouterr().out


def test_lab_paper_open_requires_invalidation_and_max_loss(tmp_path: Path, capsys) -> None:
    slug = _ready_thesis(tmp_path)
    common = _research_args(tmp_path)
    capsys.readouterr()
    rc = main(["paper", "open", slug, "--size", "0.01", "--max-loss", "500 USDC", "--invalidation", "", *common])
    # argparse required=True on --invalidation still allows empty string
    assert rc == 2
    assert "without invalidation" in capsys.readouterr().out

    rc = main(
        ["paper", "open", slug, "--size", "0.01", "--max-loss", "", "--invalidation", "Close < 60k", *common]
    )
    assert rc == 2
    assert "without max loss" in capsys.readouterr().out


def test_lab_paper_open_close_list(tmp_path: Path, capsys) -> None:
    slug = _ready_thesis(tmp_path)
    common = _research_args(tmp_path)
    capsys.readouterr()
    assert (
        main(
            [
                "paper",
                "open",
                slug,
                "--size",
                "0.01",
                "--max-loss",
                "500 USDC",
                "--invalidation",
                "Close < 60000 on the daily",
                "--checkpoint",
                "funding fades in 48h",
                "--fill-price",
                "65000",
                "--mark",
                "64990",
                *common,
            ]
        )
        == 0
    )
    opened = json.loads(capsys.readouterr().out)
    assert opened["status"] == "open"
    trade_id = opened["id"]
    assert opened["invalidation"]
    assert opened["max_loss"]
    assert (
        main(
            [
                "paper",
                "close",
                slug,
                "--id",
                trade_id,
                "--exit-reason",
                "time stop",
                "--pnl",
                "25",
                "--slippage-bps",
                "4.5",
                *common,
            ]
        )
        == 0
    )
    closed = json.loads(capsys.readouterr().out)
    assert closed["status"] == "closed"
    assert closed["exit_reason"] == "time stop"
    assert main(["paper", "list", slug, *common]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["count"] == 1
    assert listed["trades"][0]["id"] == trade_id
