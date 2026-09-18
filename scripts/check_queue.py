#!/usr/bin/env python3
"""Read-only improvement-queue hygiene. Exit 0 on pass, 2 on fail.

Does not merge PRs, waive gates, or close OPEN incidents.
"""

from __future__ import annotations

from mm_desks.queue import main

if __name__ == "__main__":
    raise SystemExit(main())
