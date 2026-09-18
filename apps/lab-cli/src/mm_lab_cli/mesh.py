"""lab mesh — Phase 6a PG LISTEN/NOTIFY dry-run (no Redis, no send)."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from mm_desks.cadence import all_channels
from mm_desks.mesh import mesh_from_fixture
from mm_desks.naming import require_publishing_desk


def add_mesh_parser(sub) -> None:
    mesh = sub.add_parser("mesh", help="Phase 6a desk mesh (PG NOTIFY; default dry-run)")
    mesh_sub = mesh.add_subparsers(dest="mesh_cmd")

    dry = mesh_sub.add_parser("dry", help="run desks, publish envelopes, Coord assemble (fixture)")
    dry.add_argument("--fixture", type=Path, required=True, help="frozen-day JSON/YAML")
    dry.add_argument("--kill-desk", action="append", default=[], dest="kill_desk", help="omit desk (FAILED + error_class)")
    dry.add_argument("--no-db", action="store_true", help="in-memory bus (default for fixture tests)")
    dry.add_argument("--dsn", help="Postgres DSN (default POSTGRES_DSN); ignored with --no-db")
    dry.add_argument("--repo-root", type=Path, default=Path("."))
    dry.add_argument("--out", type=Path, help="write pack + hashes under briefs/YYYY-MM-DD/")

    ch = mesh_sub.add_parser("channels", help="list LISTEN/NOTIFY channels")
    ch.add_argument("--repo-root", type=Path, default=Path("."))


def dispatch_mesh(args: Namespace) -> int:
    import sys

    cmd = getattr(args, "mesh_cmd", None)
    if cmd == "channels":
        channels = all_channels(Path(args.repo_root).resolve())
        print(json.dumps({"bus": "postgres-listen-notify", "redis": False, "channels": list(channels)}, indent=2))
        return 0
    if cmd != "dry":
        print("usage: lab mesh dry --fixture PATH [--kill-desk SLUG] [--no-db]", file=sys.stderr)
        return 2

    killed = tuple(args.kill_desk or ())
    for slug in killed:
        try:
            require_publishing_desk(slug)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    root = Path(args.repo_root).resolve()
    store = None
    bus = None
    session_cm = None
    if not bool(getattr(args, "no_db", False)):
        from mm_memory.db import dsn_from_env, session_scope
        from mm_desks.pg import PostgresBus, PostgresEnvelopeStore

        dsn = args.dsn or dsn_from_env()
        session_cm = session_scope(dsn)
        session = session_cm.__enter__()
        store = PostgresEnvelopeStore(session)
        bus = PostgresBus(dsn)
    try:
        first = mesh_from_fixture(Path(args.fixture), repo_root=root, killed=killed, store=store, bus=bus)
        second = mesh_from_fixture(Path(args.fixture), repo_root=root, killed=killed, store=store, bus=bus)
    finally:
        if session_cm is not None:
            session_cm.__exit__(None, None, None)

    written: dict[str, str] = {}
    out_root = Path(args.out).resolve() if getattr(args, "out", None) is not None else None
    if out_root is not None:
        day_dir = out_root / "briefs" / first.session_date
        day_dir.mkdir(parents=True, exist_ok=True)
        pack_path = day_dir / "mesh-pack.md"
        hash_path = day_dir / "mesh-run.sha256"
        pack_path.write_text(first.assemble.pack_markdown or "", encoding="utf-8")
        hash_path.write_text(first.content_hash + "\n", encoding="utf-8")
        written = {"pack": str(pack_path), "sha256": str(hash_path)}

    payload = first.as_public_dict()
    payload["written"] = written
    payload["no_db"] = bool(getattr(args, "no_db", False))
    payload["bus"] = "in-memory" if getattr(args, "no_db", False) else "postgres-listen-notify"
    payload["redis"] = False
    payload["double_run_identical"] = first.content_hash == second.content_hash
    payload["second_content_hash"] = second.content_hash
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0
