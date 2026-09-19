"""IMP-042 import boundary: scheduler/desks must not import execution."""

from __future__ import annotations

import ast
from pathlib import Path

from mm_desks.scheduler import load_catalog
from mm_memory.heartbeat_repository import persist_heartbeat

ROOT = Path(__file__).resolve().parents[2]


def _imported_top_levels(path: Path) -> set[str]:
    names: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_scheduler_module_has_no_execution_import() -> None:
    sched = ROOT / "packages" / "desks" / "src" / "mm_desks" / "scheduler.py"
    repo = ROOT / "packages" / "memory" / "src" / "mm_memory" / "heartbeat_repository.py"
    assert "mm_execution" not in _imported_top_levels(sched)
    assert "mm_execution" not in _imported_top_levels(repo)
    for snippet in ("sign_l1_action", "hl_trade", "submit_order"):
        assert snippet not in sched.read_text(encoding="utf-8")
        assert snippet not in repo.read_text(encoding="utf-8")
    assert persist_heartbeat is not None
    catalog = load_catalog(ROOT)
    assert catalog.routines
