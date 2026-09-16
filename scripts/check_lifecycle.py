#!/usr/bin/env python3
"""Refuse advancing research artifacts without required predecessors.

Phase 4 DoD: a thesis without intent is an error; in_skeptic requires
evidence links; paper artifacts require invalidation + max loss.
Rejected theses remain on disk as learning records.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mm_research_kit.lifecycle import run as run_lifecycle_check


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
    return run_lifecycle_check(args.research_root, templates)


if __name__ == "__main__":
    raise SystemExit(main())
