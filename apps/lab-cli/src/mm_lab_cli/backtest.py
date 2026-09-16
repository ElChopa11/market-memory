"""lab backtest run — reproducible fixture replay. No live trading."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from mm_backtest.artifacts import write_backtest_artifact
from mm_backtest.errors import BacktestError, LookAheadError
from mm_backtest.harness import run_backtest
from mm_backtest.loaders import load_fixture_file
from mm_backtest.strategy import build_strategy
from mm_common.enums import ResearchRunKind
from mm_common.time import parse_utc, utcnow
from mm_memory.db import dsn_from_env, session_scope
from mm_memory.run_repository import ResearchRunRepository
from mm_memory.thesis_repository import ThesisRepository
from mm_research_kit.workspace import find_workspace, git_path


def add_backtest_parser(sub) -> None:
    backtest = sub.add_parser("backtest", help="run a reproducible fixture backtest")
    backtest_sub = backtest.add_subparsers(dest="backtest_cmd")
    run_p = backtest_sub.add_parser("run", help="replay JSON/parquet candles; record params_hash")
    run_p.add_argument("--fixture", type=Path, required=True, help="JSON or parquet candles")
    run_p.add_argument("--strategy", default="buy_hold", help="buy_hold | threshold")
    run_p.add_argument("--instrument", help="override fixture instrument")
    run_p.add_argument("--thesis", help="THESIS-XXXX to bind the run and write backtests/")
    run_p.add_argument("--out", type=Path, help="artifact directory (default: thesis backtests/ or ./backtests)")
    run_p.add_argument("--param", action="append", default=[], help="strategy param key=value (repeatable)")
    run_p.add_argument("--initial-cash", default="10000")
    run_p.add_argument("--slippage-bps", default="0")
    run_p.add_argument("--start", help="UTC start as-of (ISO-8601)")
    run_p.add_argument("--end", help="UTC end as-of (ISO-8601)")
    run_p.add_argument("--research-root", type=Path, default=Path("research"))
    run_p.add_argument("--repo-root", type=Path, default=Path("."))
    run_p.add_argument("--dsn")
    run_p.add_argument("--no-db", action="store_true")
    run_p.add_argument(
        "--allow-lookahead",
        action="store_true",
        help="do not refuse look-ahead fixtures (debug only; adversarial tests use the default refuse path)",
    )


def _parse_params(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise BacktestError(f"strategy param must be key=value, got {item!r}")
        key, value = item.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def dispatch_backtest(args: Namespace) -> int:
    if getattr(args, "backtest_cmd", None) != "run":
        print("usage: lab backtest run --fixture PATH [--strategy buy_hold] [--thesis THESIS-XXXX]")
        return 2
    try:
        return cmd_backtest_run(args)
    except (BacktestError, LookAheadError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", flush=True)
        return 2


def cmd_backtest_run(args: Namespace) -> int:
    fixture: Path = args.fixture
    strategy_params = _parse_params(args.param or [])
    bars, facts, meta = load_fixture_file(fixture, strict=not args.allow_lookahead)
    instrument = args.instrument or meta.get("instrument") or (bars[0].instrument if bars else "BTC")
    strategy = build_strategy(args.strategy, strategy_params)
    start = parse_utc(args.start) if args.start else None
    end = parse_utc(args.end) if args.end else None
    started = utcnow()
    result = run_backtest(
        bars,
        strategy,
        instrument=instrument,
        facts=facts,
        initial_cash=args.initial_cash,
        slippage_bps=args.slippage_bps,
        start=start,
        end=end,
    )
    finished = utcnow()

    workspace = None
    dest = args.out
    if args.thesis:
        workspace = find_workspace(args.research_root, args.thesis)
        dest = dest or (workspace / "backtests")
    dest = dest or Path("backtests")
    artifact = write_backtest_artifact(result, Path(dest))
    artifact_rel = git_path(artifact, args.repo_root)

    thesis_db_id = None
    run_id = None
    if not args.no_db:
        with session_scope(args.dsn or dsn_from_env()) as session:
            if workspace is not None:
                row = ThesisRepository(session).get_by_slug(workspace.name)
                if row is not None:
                    thesis_db_id = row.id
            recorded = ResearchRunRepository(session).record(
                kind=ResearchRunKind.BACKTEST.value,
                params_hash=result.params_hash,
                started_at=started,
                finished_at=finished,
                thesis_id=thesis_db_id,
                result_summary=result.summary(),
                artifact_paths=[artifact_rel],
            )
            run_id = recorded.id

    print(
        json.dumps(
            {
                "params_hash": result.params_hash,
                "result_hash": result.result_hash,
                "strategy": result.strategy,
                "instrument": result.instrument,
                "metrics": result.metrics,
                "artifact": str(artifact),
                "thesis": workspace.name if workspace is not None else None,
                "research_run_id": run_id,
                "lookahead_findings": meta.get("lookahead_findings") or [],
            },
            indent=2,
        )
    )
    return 0
