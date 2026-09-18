#!/usr/bin/env python3
"""Import-boundary CI for Phase 5a desk walls.

Research / desks / quant / delivery must not import execution or signing
surfaces. Intel (ingest) must not import opine packages.

Never prints secrets. Exit 0 on pass, 1 on fail.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OPINE_PACKAGES = ("research_kit", "desks", "quant", "delivery")
INTEL_PACKAGE = "ingest"

FORBIDDEN_EXECUTION_IMPORTS = frozenset({"mm_execution", "mm_execution_service"})
FORBIDDEN_INTEL_OPINE_IMPORTS = frozenset({"mm_research_kit", "mm_desks", "mm_quant", "mm_delivery"})
FORBIDDEN_BUS_IMPORTS = frozenset({"redis", "aioredis", "walrus"})
FORBIDDEN_SNIPPETS = ("sign_l1_action", "hl_trade", "submit_order", "private_key")


def _imported_top_levels(root: Path) -> set[str]:
    names: set[str] = set()
    if not root.is_dir():
        return names
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
    return names


def _snippet_hits(root: Path) -> list[str]:
    hits: list[str] = []
    if not root.is_dir():
        return hits
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in text:
                hits.append(f"{path.relative_to(ROOT)}:{snippet}")
    return hits


def check() -> list[str]:
    errors: list[str] = []
    for name in OPINE_PACKAGES:
        src = ROOT / "packages" / name / "src"
        imported = _imported_top_levels(src)
        bad = imported & FORBIDDEN_EXECUTION_IMPORTS
        if bad:
            errors.append(f"{name} imports execution surface: {sorted(bad)}")
        bus = imported & FORBIDDEN_BUS_IMPORTS
        if bus:
            errors.append(f"{name} imports Redis/bus client (Principal lock is PG NOTIFY): {sorted(bus)}")
        errors.extend(_snippet_hits(src))
    memory_src = ROOT / "packages" / "memory" / "src"
    memory_imported = _imported_top_levels(memory_src)
    memory_bus = memory_imported & FORBIDDEN_BUS_IMPORTS
    if memory_bus:
        errors.append(f"memory imports Redis/bus client (Principal lock is PG NOTIFY): {sorted(memory_bus)}")
    ingest_src = ROOT / "packages" / INTEL_PACKAGE / "src"
    imported = _imported_top_levels(ingest_src)
    bad = imported & FORBIDDEN_INTEL_OPINE_IMPORTS
    if bad:
        errors.append(f"ingest (Intel) imports opine package: {sorted(bad)}")
    return errors


def main() -> int:
    errors = check()
    if errors:
        print("import-boundary check failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("import-boundary check passed (research/desks/quant/delivery vs execution; Intel vs opine; no Redis bus)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
