"""±900s guard for the Sydney-morning dual cron (B1 Stage 1).

Catalog anchor: weekday 06:30 Australia/Sydney
(``config/schedules/routines.yaml`` ``grok.sydney_morning``).
``miss_after_seconds`` is 900.

GitHub Actions schedules both crons every week:

- AEST (UTC+10, ~first Sunday of April → first Sunday of October):
  ``30 20 * * 0-4`` (Sun–Thu 20:30 UTC = Mon–Fri 06:30 AEST)
- AEDT (UTC+11, ~first Sunday of October → first Sunday of April):
  ``30 19 * * 0-4`` (Sun–Thu 19:30 UTC = Mon–Fri 06:30 AEDT)

The off-season companion is one hour off the local anchor (|delta| = 3600 > 900).
It must no-op: reason ``outside_anchor_window``, exit 0, no stamp.
``workflow_dispatch`` with force bypasses the guard and stamps.

Paper only. This module does not send Telegram and does not write a completion row.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from mm_common.time import as_utc, parse_utc

SYDNEY = ZoneInfo("Australia/Sydney")
ANCHOR_LOCAL = time(6, 30, 0)
DEFAULT_MISS_AFTER_SECONDS = 900  # catalog miss_after_seconds; Stage-1 tolerance

REASON_WITHIN = "within_anchor_window"
REASON_OUTSIDE = "outside_anchor_window"
REASON_WEEKEND = "weekend_sydney"
REASON_FORCE = "force"

OUTSIDE_NOTE = "dual-cron off-season companion; counterpart cron owns this DST period"

_FORCE_TRUE = frozenset({"1", "true", "yes"})


def force_requested(value: str | None = None) -> bool:
    """True when FORCE_STAMP / workflow_dispatch force is set."""
    raw = os.environ.get("FORCE_STAMP", "") if value is None else value
    return raw.strip().lower() in _FORCE_TRUE


@dataclass(frozen=True)
class SydneyAnchorDecision:
    """Whether this instant may stamp ``grok.sydney_morning``.

    ``skip`` and ``stamp`` are exclusive. A skip is a successful no-op
    (process exit 0, no completion row).
    """

    skip: bool
    stamp: bool
    reason: str
    delta_seconds: int
    miss_after_seconds: int
    anchor_utc: datetime
    now_utc: datetime
    local_iso: str
    force: bool
    note: str = ""

    def as_public_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "skip": self.skip,
            "stamp": self.stamp,
            "reason": self.reason,
            "delta_seconds": self.delta_seconds,
            "miss_after_seconds": self.miss_after_seconds,
            "anchor_utc": self.anchor_utc.isoformat(),
            "now_utc": self.now_utc.isoformat(),
            "local": self.local_iso,
            "force": self.force,
        }
        if self.note:
            payload["note"] = self.note
        return payload


def decide_sydney_morning_anchor(
    now: datetime,
    *,
    force: bool = False,
    miss_after_seconds: int = DEFAULT_MISS_AFTER_SECONDS,
) -> SydneyAnchorDecision:
    """Today's 06:30 Australia/Sydney anchor, then ±miss_after skip.

    Anchor is 06:30 on the Sydney calendar date of ``now`` (same rule as the
    previous inline workflow). Weekend Sydney (Sat/Sun) skips unless ``force``.
    ``force`` (workflow_dispatch) stamps even outside the window and on a weekend.
    """
    now_u = as_utc(now)
    local = now_u.astimezone(SYDNEY)
    anchor_local = local.replace(
        hour=ANCHOR_LOCAL.hour,
        minute=ANCHOR_LOCAL.minute,
        second=0,
        microsecond=0,
    )
    anchor = anchor_local.astimezone(timezone.utc)
    delta = int((now_u - anchor).total_seconds())
    tolerance = int(miss_after_seconds)
    within = abs(delta) <= tolerance
    local_iso = local.isoformat()

    def decision(skip: bool, reason: str, note: str = "") -> SydneyAnchorDecision:
        return SydneyAnchorDecision(
            skip=skip,
            stamp=not skip,
            reason=reason,
            delta_seconds=delta,
            miss_after_seconds=tolerance,
            anchor_utc=anchor,
            now_utc=now_u,
            local_iso=local_iso,
            force=bool(force),
            note=note,
        )

    if force:
        return decision(False, REASON_FORCE)
    if local.weekday() >= 5:
        return decision(True, REASON_WEEKEND)
    if not within:
        return decision(True, REASON_OUTSIDE, OUTSIDE_NOTE)
    return decision(False, REASON_WITHIN)


def append_github_output(path: str, decision: SydneyAnchorDecision) -> None:
    """Append guard keys for ``actions/checkout`` step outputs."""
    skipped = "true" if decision.skip else "false"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"skipped={skipped}\n")
        fh.write(f"reason={decision.reason}\n")
        fh.write(f"delta_seconds={decision.delta_seconds}\n")


def main(argv: list[str] | None = None) -> int:
    """Print the decision JSON and exit 0.

    Skip and stamp are both exit 0. Callers read ``skip`` / ``stamp``.
    A skip (``outside_anchor_window``, ``weekend_sydney``) must not stamp.
    """
    parser = argparse.ArgumentParser(
        description="Sydney 06:30 ±900s dual-cron guard (exit 0; read skip/stamp)",
    )
    parser.add_argument("--now", default="", help="UTC ISO instant; default is now")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass the guard (also set by FORCE_STAMP=true)",
    )
    parser.add_argument("--miss-after", type=int, default=DEFAULT_MISS_AFTER_SECONDS)
    parser.add_argument(
        "--github-output",
        default="",
        help="Append skipped/reason/delta_seconds to this file",
    )
    args = parser.parse_args(argv)
    force = bool(args.force) or force_requested()
    now = parse_utc(args.now) if args.now else datetime.now(timezone.utc)
    decision = decide_sydney_morning_anchor(
        now,
        force=force,
        miss_after_seconds=args.miss_after,
    )
    print(json.dumps(decision.as_public_dict(), indent=2, sort_keys=True))
    if args.github_output:
        append_github_output(args.github_output, decision)
    return 0


if __name__ == "__main__":
    sys.exit(main())
