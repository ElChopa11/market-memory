#!/usr/bin/env python3
"""Refuse advancing research artifacts without required predecessors.

Phase 0 DoD: a thesis without intent is an error. Later stages have the
same predecessor gates (see docs/research-lifecycle.md).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REQUIRED_TEMPLATES = [
    "intent.md",
    "thesis.md",
    "research-plan.md",
    "skeptic-review.md",
    "unicorn-card.md",
    "paper-trade.md",
    "promotion-decision.md",
    "post-mortem.md",
]

SKIP_DIR_NAMES = {".git", "__pycache__", "evidence", "backtests", "paper"}


def _exists(workspace: Path, name: str) -> bool:
    return (workspace / name).is_file()


def _dir_nonempty(path: Path) -> bool:
    if not path.is_dir():
        return False
    return any(path.rglob("*"))


def _has_paper(workspace: Path) -> bool:
    if _exists(workspace, "paper-trade.md"):
        return True
    paper = workspace / "paper"
    if not paper.is_dir():
        return False
    return any(p.is_file() for p in paper.rglob("*"))


def _has_promotion(workspace: Path) -> bool:
    return _exists(workspace, "promotion-decision.md") or _exists(
        workspace, "promotion.md"
    )


def is_thesis_workspace(path: Path) -> bool:
    if not path.is_dir():
        return False
    if path.name.startswith("THESIS-"):
        return True
    markers = (
        "intent.md",
        "thesis.md",
        "research-plan.md",
        "skeptic-review.md",
        "paper-trade.md",
        "promotion-decision.md",
        "promotion.md",
        "post-mortem.md",
        "unicorn-card.md",
    )
    return any(_exists(path, name) for name in markers)


def discover_workspaces(research_root: Path) -> list[Path]:
    if not research_root.is_dir():
        return []
    found: list[Path] = []
    for candidate in sorted(research_root.rglob("*")):
        if not candidate.is_dir():
            continue
        if candidate.name in SKIP_DIR_NAMES:
            continue
        if is_thesis_workspace(candidate):
            found.append(candidate)
    # Prefer inner thesis dirs; drop parents that only exist as containers
    filtered: list[Path] = []
    for ws in found:
        if any(other != ws and other.is_relative_to(ws) for other in found):
            continue
        filtered.append(ws)
    return filtered


def check_templates(templates_root: Path) -> list[str]:
    errors: list[str] = []
    if not templates_root.is_dir():
        return [f"missing templates directory: {templates_root}"]
    for name in REQUIRED_TEMPLATES:
        if not (templates_root / name).is_file():
            errors.append(f"missing template: {templates_root / name}")
    return errors


def check_workspace(workspace: Path) -> list[str]:
    errors: list[str] = []
    rel = workspace.as_posix()

    if _exists(workspace, "thesis.md") and not _exists(workspace, "intent.md"):
        errors.append(f"{rel}: thesis without intent")

    if _exists(workspace, "research-plan.md") and not _exists(workspace, "thesis.md"):
        errors.append(f"{rel}: research-plan without thesis")

    if _exists(workspace, "skeptic-review.md") and not _exists(
        workspace, "research-plan.md"
    ):
        errors.append(f"{rel}: skeptic-review without research-plan")

    evidence = workspace / "evidence"
    backtests = workspace / "backtests"
    if (_dir_nonempty(evidence) or _dir_nonempty(backtests)) and not _exists(
        workspace, "research-plan.md"
    ):
        errors.append(f"{rel}: evidence/backtests without research-plan")

    if _has_paper(workspace) and not _exists(workspace, "skeptic-review.md"):
        errors.append(f"{rel}: paper without skeptic-review")

    if _has_promotion(workspace) and not _has_paper(workspace):
        errors.append(f"{rel}: promotion without paper")

    if _exists(workspace, "post-mortem.md") and not (
        _has_paper(workspace) or _has_promotion(workspace)
    ):
        errors.append(f"{rel}: post-mortem without paper or promotion")

    return errors


def run(research_root: Path, templates_root: Path | None) -> int:
    errors: list[str] = []
    if templates_root is not None:
        errors.extend(check_templates(templates_root))
    for workspace in discover_workspaces(research_root):
        errors.extend(check_workspace(workspace))
    if errors:
        print("lifecycle check failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    n = len(discover_workspaces(research_root))
    print(f"lifecycle check passed ({n} thesis workspace(s))")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--research-root",
        type=Path,
        default=Path("research"),
        help="Root directory to walk for THESIS-* workspaces",
    )
    parser.add_argument(
        "--templates-root",
        type=Path,
        default=Path("templates"),
        help="Templates directory (set empty string to skip)",
    )
    parser.add_argument(
        "--skip-templates",
        action="store_true",
        help="Do not require templates/ to be present",
    )
    args = parser.parse_args(argv)
    templates = None if args.skip_templates else args.templates_root
    return run(args.research_root, templates)


if __name__ == "__main__":
    raise SystemExit(main())
