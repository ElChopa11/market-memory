"""lab paper open|close|list — shadow ledger. No live orders."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from mm_memory.db import dsn_from_env, session_scope
from mm_memory.paper_repository import PaperRepository
from mm_memory.thesis_repository import ThesisRepository
from mm_paper.artifacts import list_paper_artifacts
from mm_paper.errors import PaperError, PaperGateError
from mm_paper.ledger import close_paper_trade, open_paper_trade
from mm_research_kit.errors import GateError, ResearchKitError
from mm_research_kit.lifecycle import read_status
from mm_research_kit.workspace import find_workspace


def add_paper_parser(sub) -> None:
    paper = sub.add_parser("paper", help="open/close/list shadow paper trades")
    paper_sub = paper.add_subparsers(dest="paper_cmd")

    open_p = paper_sub.add_parser("open", help="open a paper trade (requires invalidation + max loss)")
    open_p.add_argument("slug", help="THESIS-XXXX")
    open_p.add_argument("--size", required=True)
    open_p.add_argument("--max-loss", required=True, dest="max_loss")
    open_p.add_argument("--invalidation", required=True)
    open_p.add_argument("--instrument", default="BTC")
    open_p.add_argument("--side", default="long")
    open_p.add_argument("--checkpoint", action="append", default=[], dest="checkpoints")
    open_p.add_argument("--notes", default="")
    open_p.add_argument("--fill-price")
    open_p.add_argument("--mark")
    _add_common(open_p)

    close_p = paper_sub.add_parser("close", help="close a paper trade with an exit reason")
    close_p.add_argument("slug", help="THESIS-XXXX")
    close_p.add_argument("--id", dest="trade_id", help="paper trade id (ULID)")
    close_p.add_argument("--exit-reason", required=True, dest="exit_reason")
    close_p.add_argument("--pnl")
    close_p.add_argument("--slippage-bps")
    close_p.add_argument("--fill-price")
    close_p.add_argument("--mark")
    close_p.add_argument("--notes", default="")
    _add_common(close_p)

    list_p = paper_sub.add_parser("list", help="list paper trades")
    list_p.add_argument("slug", nargs="?", help="optional THESIS-XXXX filter")
    list_p.add_argument("--status", help="open|closed")
    _add_common(list_p)


def _add_common(parser) -> None:
    parser.add_argument("--research-root", type=Path, default=Path("research"))
    parser.add_argument("--templates-root", type=Path, default=Path("templates"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--dsn")
    parser.add_argument("--no-db", action="store_true")


def dispatch_paper(args: Namespace) -> int:
    cmd = getattr(args, "paper_cmd", None)
    handlers = {"open": cmd_paper_open, "close": cmd_paper_close, "list": cmd_paper_list}
    if cmd is None or cmd not in handlers:
        print("usage: lab paper {open,close,list}")
        return 2
    try:
        return handlers[cmd](args)
    except PaperGateError as exc:
        print(f"gate failed: {exc}", flush=True)
        return 2
    except (PaperError, GateError, ResearchKitError, FileNotFoundError, KeyError, ValueError) as exc:
        print(f"error: {exc}", flush=True)
        return 2


def cmd_paper_open(args: Namespace) -> int:
    thesis_id = None
    if not args.no_db:
        workspace = find_workspace(args.research_root, args.slug)
        with session_scope(args.dsn or dsn_from_env()) as session:
            row = ThesisRepository(session).get_by_slug(workspace.name)
            if row is not None:
                thesis_id = row.id
    record = open_paper_trade(
        research_root=args.research_root,
        templates_root=args.templates_root,
        repo_root=args.repo_root,
        slug=args.slug,
        size=args.size,
        max_loss=args.max_loss,
        invalidation=args.invalidation,
        instrument=args.instrument,
        side=args.side,
        expected_path=list(args.checkpoints or []),
        notes=args.notes,
        fill_price=args.fill_price,
        mark_price=args.mark,
        thesis_id=thesis_id,
    )
    if not args.no_db:
        workspace = find_workspace(args.research_root, args.slug)
        with session_scope(args.dsn or dsn_from_env()) as session:
            repo = ThesisRepository(session)
            row = repo.get_by_slug(workspace.name)
            if row is None:
                raise PaperError(f"thesis {workspace.name} is not indexed in Market Memory; run without --no-db after lab thesis new")
            repo.upsert(
                slug=workspace.name,
                status=read_status(workspace) or "paper",
                author_role=row.author_role,
                artifact_git_path=row.artifact_git_path,
                artifact_content_hash=row.artifact_content_hash,
                instrument=record.instrument,
                horizon=row.horizon,
                invalidation_summary=record.invalidation,
                risk_budget_bps=row.risk_budget_bps,
            )
            PaperRepository(session).insert(
                trade_id=record.id,
                thesis_id=row.id,
                opened_at=record.opened_at,
                instrument=record.instrument,
                size=record.size,
                invalidation=record.invalidation,
                max_loss=record.max_loss,
                max_loss_amount=record.max_loss_amount,
                intent_json=record.intent_json(),
                fills_json=[fill.canonical() for fill in record.fills],
                expected_path=list(record.expected_path),
                artifact_git_path=record.artifact_git_path,
                entry_thesis_snapshot_hash=record.entry_thesis_snapshot_hash,
                slippage_bps=record.slippage_bps,
                notes=record.notes or None,
            )
            record.thesis_id = row.id
    print(json.dumps({"status": "open", **record.canonical()}, indent=2, default=str))
    return 0


def cmd_paper_close(args: Namespace) -> int:
    record = close_paper_trade(
        research_root=args.research_root,
        templates_root=args.templates_root,
        repo_root=args.repo_root,
        slug=args.slug,
        trade_id=args.trade_id,
        exit_reason=args.exit_reason,
        pnl=args.pnl,
        slippage_bps=args.slippage_bps,
        fill_price=args.fill_price,
        mark_price=args.mark,
        notes=args.notes,
    )
    if not args.no_db:
        with session_scope(args.dsn or dsn_from_env()) as session:
            PaperRepository(session).close(
                record.id,
                closed_at=record.closed_at,
                exit_reason=record.exit_reason or args.exit_reason,
                fills_json=[fill.canonical() for fill in record.fills],
                realised_path=list(record.realised_path),
                pnl=record.pnl,
                slippage_bps=record.slippage_bps,
                notes=record.notes or None,
            )
    print(json.dumps({"status": "closed", **record.canonical()}, indent=2, default=str))
    return 0


def cmd_paper_list(args: Namespace) -> int:
    if not args.no_db:
        with session_scope(args.dsn or dsn_from_env()) as session:
            thesis_id = None
            if args.slug:
                row = ThesisRepository(session).get_by_slug(find_workspace(args.research_root, args.slug).name)
                thesis_id = None if row is None else row.id
            rows = PaperRepository(session).list_trades(thesis_id=thesis_id, status=args.status)
            payload = [
                {
                    "id": row.id,
                    "thesis_id": row.thesis_id,
                    "status": row.status,
                    "instrument": row.instrument,
                    "size": row.size,
                    "invalidation": row.invalidation,
                    "max_loss": row.max_loss,
                    "pnl": str(row.pnl) if row.pnl is not None else None,
                    "slippage_bps": str(row.slippage_bps) if row.slippage_bps is not None else None,
                    "exit_reason": row.exit_reason,
                    "opened_at": row.opened_at.isoformat(),
                    "closed_at": row.closed_at.isoformat() if row.closed_at else None,
                    "artifact_git_path": row.artifact_git_path,
                }
                for row in rows
            ]
        print(json.dumps({"count": len(payload), "trades": payload}, indent=2))
        return 0

    payload = []
    if args.slug:
        workspaces = [find_workspace(args.research_root, args.slug)]
    else:
        from mm_research_kit.lifecycle import discover_workspaces

        workspaces = discover_workspaces(args.research_root)
    for workspace in workspaces:
        for row in list_paper_artifacts(workspace):
            if args.status and row.get("status") != args.status:
                continue
            payload.append(row)
    print(json.dumps({"count": len(payload), "trades": payload}, indent=2, default=str))
    return 0
