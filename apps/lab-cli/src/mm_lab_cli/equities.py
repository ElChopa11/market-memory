"""lab equities reclaim-screen — read-only Equities desk product. No credentials, no orders."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import Any

import yaml

from mm_common.time import parse_utc, utcnow
from mm_lab_cli.quant_review import overlays_from_quant_pack
from mm_research_kit.errors import GateError, ResearchKitError
from mm_research_kit.post_ipo_reclaim.engine import run_screen, write_screen
from mm_research_kit.post_ipo_reclaim.models import ENGINE_VERSION, SCREEN_FOOTER
from mm_research_kit.post_ipo_reclaim.universe import universe_from_mapping
from mm_research_kit.quant_review.engine import empty_snapshot, merge_overlays, snapshot_from_mapping


def _add_screen_args(parser) -> None:
    parser.add_argument("--fixture", type=Path, help="JSON/YAML snapshot (prints + optional overlays)")
    parser.add_argument(
        "--universe",
        type=Path,
        help="screen-only universe YAML (default config/equities/post_ipo_reclaim.yaml)",
    )
    parser.add_argument("--quant-pack", type=Path, help="optional QUANT pack directory (CSV overlay; never invents missing names)")
    parser.add_argument("--as-of", help="review clock UTC instant (ISO-8601)")
    parser.add_argument("--screen-date", help="artifact date YYYY-MM-DD")
    parser.add_argument("--research-root", type=Path, default=Path("research"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--stale-after-hours", type=int, default=None)
    parser.add_argument("--dsn")
    parser.add_argument("--no-db", action="store_true", help="git artifacts only (no Market Memory index)")


def add_equities_parser(sub) -> None:
    equities = sub.add_parser("equities", help="Equities & Post-IPO desk commands (read-only)")
    eq_sub = equities.add_subparsers(dest="equities_cmd")
    screen = eq_sub.add_parser(
        "reclaim-screen",
        help="Post-IPO / reclaim research triage screen (not a trading decision)",
    )
    _add_screen_args(screen)


def dispatch_equities(args: Namespace) -> int:
    cmd = getattr(args, "equities_cmd", None)
    if cmd is None:
        print("usage: lab equities reclaim-screen")
        return 2
    if cmd != "reclaim-screen":
        print("usage: lab equities reclaim-screen")
        return 2
    try:
        return cmd_reclaim_screen(args)
    except (GateError, ResearchKitError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", flush=True)
        return 2


def cmd_reclaim_screen(args: Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    universe_path = (
        Path(args.universe) if args.universe else repo_root / "config" / "equities" / "post_ipo_reclaim.yaml"
    )
    universe = universe_from_mapping(_load_mapping(universe_path))
    as_of = parse_utc(args.as_of) if args.as_of else utcnow()
    if args.fixture:
        snapshot = snapshot_from_mapping(_load_mapping(Path(args.fixture)), symbol_map=universe.symbol_map)
    else:
        snapshot = empty_snapshot(as_of_knowledge=as_of, source="empty")

    if args.quant_pack:
        snapshot = merge_overlays(snapshot, overlays_from_quant_pack(Path(args.quant_pack), universe.symbol_map))

    screen_date = args.screen_date or snapshot.as_of_knowledge.date().isoformat()
    result = run_screen(
        universe,
        snapshot,
        review_at=as_of,
        screen_date=screen_date,
        stale_after_hours=args.stale_after_hours,
        generated_at=as_of,
    )
    written = write_screen(result, research_root=Path(args.research_root))
    payload = {
        "engine": ENGINE_VERSION,
        "command": "lab equities reclaim-screen",
        "screen_date": result.screen_date,
        "as_of_knowledge": result.as_of_knowledge,
        "params_hash": result.params_hash,
        "screen": written["screen"],
        "meta": written["meta"],
        "row_count": len(result.rows),
        "verdicts": {row.instrument: row.verdict for row in result.rows},
        "data_quality": {row.instrument: row.data_quality for row in result.rows},
        "disclaimer": SCREEN_FOOTER,
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON/YAML object")
    return data
