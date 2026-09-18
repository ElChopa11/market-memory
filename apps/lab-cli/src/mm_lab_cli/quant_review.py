"""lab quant-review — read-only Quant Review Board. No credentials, no orders."""

from __future__ import annotations

import csv
import json
from argparse import Namespace
from pathlib import Path
from typing import Any

import yaml

from mm_common.enums import ResearchRunKind
from mm_common.time import parse_utc, utcnow
from mm_research_kit.errors import GateError, ResearchKitError
from mm_research_kit.quant_review.engine import (
    empty_snapshot,
    find_prior_board,
    merge_memory,
    merge_overlays,
    run_board,
    snapshot_from_mapping,
    write_board,
)
from mm_research_kit.quant_review.models import ENGINE_VERSION, MemoryOverlay, SeriesOverlay
from mm_research_kit.quant_review.locked_membership import write_locked_membership_pass
from mm_research_kit.quant_review.universe import universe_from_mapping
from mm_research_kit.workspace import git_path


def add_quant_review_parser(sub) -> None:
    parser = sub.add_parser("quant-review", help="run the read-only Quant Review Board")
    parser.add_argument("--fixture", type=Path, help="JSON/YAML snapshot (prints + optional overlays)")
    parser.add_argument("--universe", type=Path, help="universe YAML (default config/quant_review_universe.yaml)")
    parser.add_argument("--quant-pack", type=Path, help="optional QUANT pack directory (CSV overlay)")
    parser.add_argument("--as-of", help="review clock UTC instant (ISO-8601)")
    parser.add_argument("--review-date", help="board folder date YYYY-MM-DD")
    parser.add_argument("--research-root", type=Path, default=Path("research"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--stale-after-hours", type=int, default=36)
    parser.add_argument("--dsn")
    parser.add_argument("--no-db", action="store_true", help="git artifacts only (no Market Memory index)")
    parser.add_argument(
        "--locked-membership",
        action="store_true",
        help="desk re-score of config/universe.yaml membership only (IMP-008); ignores screenshot fixture",
    )


def dispatch_quant_review(args: Namespace) -> int:
    try:
        return cmd_quant_review(args)
    except (GateError, ResearchKitError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", flush=True)
        return 2


def cmd_quant_review(args: Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    if args.locked_membership:
        written = write_locked_membership_pass(repo_root, research_root=Path(args.research_root))
        payload = {
            "engine": "imp-008.locked-membership-desk-pass",
            "review_date": "2026-09-18",
            "board": written["board"],
            "card_count": len(written["cards"]),
            "params_hash": written["params_hash"],
            "research_priority_names": [],
            "disclaimer": "Research only. Not a trade instruction, allocation decision, or execution approval.",
        }
        print(json.dumps(payload, indent=2, default=str))
        return 0
    universe_path = Path(args.universe) if args.universe else repo_root / "config" / "quant_review_universe.yaml"
    universe = universe_from_mapping(_load_mapping(universe_path))
    as_of = parse_utc(args.as_of) if args.as_of else utcnow()
    if args.fixture:
        snapshot = snapshot_from_mapping(_load_mapping(Path(args.fixture)), symbol_map=universe.symbol_map)
    else:
        snapshot = empty_snapshot(as_of_knowledge=as_of, source="empty")

    if args.quant_pack:
        snapshot = merge_overlays(snapshot, overlays_from_quant_pack(Path(args.quant_pack), universe.symbol_map))

    memory_rows: tuple[MemoryOverlay, ...] = ()
    if not args.no_db:
        memory_rows = _memory_overlay(args, universe)
        if memory_rows:
            snapshot = merge_memory(snapshot, memory_rows)

    ingest_overlap, deferred = _locked_universe_sets(repo_root)
    review_date = args.review_date or snapshot.as_of_knowledge.date().isoformat()
    prior_path = find_prior_board(Path(args.research_root), review_date)
    started = utcnow()
    result = run_board(
        universe,
        snapshot,
        review_at=as_of,
        review_date=review_date,
        stale_after_hours=int(args.stale_after_hours),
        ingest_overlap=ingest_overlap & {spec.symbol for spec in universe.instruments},
        deferred_must_cut=deferred & {spec.symbol for spec in universe.instruments},
        prior_board=prior_path.as_posix() if prior_path else None,
        generated_at=as_of,
    )
    written = write_board(result, research_root=Path(args.research_root))
    run_id = None
    if not args.no_db:
        run_id = _index_run(args, result, written, repo_root, started)
    payload = {
        "engine": ENGINE_VERSION,
        "review_date": result.review_date,
        "as_of_knowledge": result.as_of_knowledge,
        "params_hash": result.params_hash,
        "board": written["board"],
        "card_count": len(result.cards),
        "verdicts": {card.instrument: card.verdict for card in result.cards},
        "research_run_id": run_id,
        "disclaimer": "Research only. Not a trade instruction, allocation decision, or execution approval.",
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0


def overlays_from_quant_pack(path: Path, symbol_map: dict[str, str]) -> tuple[SeriesOverlay, ...]:
    metrics = path / "metrics_active_and_watch.csv"
    meta_path = path / "run_meta.json"
    if not metrics.is_file():
        raise FileNotFoundError(f"quant pack metrics missing: {metrics}")
    captured = ""
    tickers: dict[str, Any] = {}
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        captured = str(meta.get("as_of_knowledge") or meta.get("run_ts_utc") or "")
        tickers = meta.get("tickers") or {}
    adv_by: dict[str, float] = {}
    adv_path = path / "equity_adv_5d_from_universe_scan.csv"
    if adv_path.is_file():
        with adv_path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                name = str(row.get("name") or row.get("symbol") or "").upper()
                for key in ("adv_5d_shares", "adv_5d", "adv", "average_volume"):
                    if row.get(key):
                        try:
                            adv_by[name] = float(row[key])
                        except ValueError:
                            pass
                        break
    out: list[SeriesOverlay] = []
    with metrics.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            symbol = str(row.get("name") or "").strip().upper()
            if not symbol:
                continue
            ticker_meta = tickers.get(symbol) or {}
            out.append(
                SeriesOverlay(
                    symbol=symbol_map.get(symbol, symbol),
                    source=str(row.get("source") or "quant_pack"),
                    asof=str(row.get("asof") or ""),
                    captured_at=captured,
                    last_close=_float(row.get("last_close")),
                    ret_short=_float(row.get("ret_1m")),
                    ret_long=_float(row.get("ret_3m")),
                    rel_short=_float(row.get("rel_1m")),
                    rel_long=_float(row.get("rel_3m")),
                    rv_20d=_float(row.get("rv_20d")),
                    rv_60d=_float(row.get("rv_60d")),
                    mdd=_float(row.get("mdd_1y")),
                    n_bars=int(ticker_meta["n_bars"]) if ticker_meta.get("n_bars") is not None else None,
                    bench=str(row["bench"]) if row.get("bench") else None,
                    data_quality="partial" if "LAG" in str(row.get("asof_note") or "").upper() else "ok",
                    notes=str(row.get("asof_note") or row.get("rel_method") or ""),
                    adv=adv_by.get(symbol),
                )
            )
    return tuple(out)


def _memory_overlay(args: Namespace, universe) -> tuple[MemoryOverlay, ...]:
    from mm_memory.db import dsn_from_env, session_scope
    from mm_memory.queries import what_did_we_know

    wanted = {spec.symbol for spec in universe.instruments}
    try:
        dsn = args.dsn or dsn_from_env()
    except Exception:
        return ()
    as_of = parse_utc(args.as_of) if args.as_of else utcnow()
    try:
        with session_scope(dsn) as session:
            rows = what_did_we_know(session, as_of)
    except Exception:
        return ()
    out: list[MemoryOverlay] = []
    for row in rows:
        if row.instrument not in wanted:
            continue
        out.append(
            MemoryOverlay(
                symbol=row.instrument,
                observation_id=row.id,
                metric=row.metric,
                value=str((row.payload_json or {}).get("value") or ""),
                data_quality=row.data_quality,
                as_of_knowledge=row.as_of_knowledge.isoformat(),
                claim_hash=row.claim_hash,
            )
        )
    return tuple(out)


def _index_run(args: Namespace, result, written: dict[str, Any], repo_root: Path, started) -> str | None:
    from mm_memory.db import dsn_from_env, session_scope
    from mm_memory.run_repository import ResearchRunRepository

    dsn = args.dsn or dsn_from_env()
    finished = utcnow()
    with session_scope(dsn) as session:
        row = ResearchRunRepository(session).record(
            kind=ResearchRunKind.SCAN.value,
            params_hash=result.params_hash,
            started_at=started,
            finished_at=finished,
            result_summary={
                "review_date": result.review_date,
                "as_of_knowledge": result.as_of_knowledge,
                "card_count": len(result.cards),
                "engine": ENGINE_VERSION,
            },
            artifact_paths=[
                git_path(Path(written["board"]), repo_root),
                git_path(Path(written["meta"]), repo_root),
            ],
        )
        return row.id


def _locked_universe_sets(repo_root: Path) -> tuple[frozenset[str], frozenset[str]]:
    path = repo_root / "config" / "universe.yaml"
    if not path.is_file():
        return frozenset(), frozenset()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    overlap = set(data.get("crypto_perps") or []) | set(data.get("equities") or [])
    deferred = set((data.get("deferred_must_cut") or {}).get("crypto") or []) | set(
        (data.get("deferred_must_cut") or {}).get("equities") or []
    )
    return frozenset(str(x).upper() for x in overlap), frozenset(str(x).upper() for x in deferred)


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON/YAML object")
    return data


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
