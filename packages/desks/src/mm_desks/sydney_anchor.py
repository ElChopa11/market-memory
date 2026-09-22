"""Weekday 06:30 Australia/Sydney anchor and the ±900s decision.

Extracted so frozen AEST and AEDT clocks can be tested. This module does not
write a completion row and does not send Telegram.

``.github/workflows/hybrid-sydney-morning.yml`` does not import this module.
That workflow stays one cron (``30 20 * * 0-4``): fire, stamp, exit. No guard,
no skip, no second cron. Wiring this decision back into the workflow is a
later PR, after the baseline fire succeeds and after the tolerance bugs below
are fixed. Draft #98 stays unmerged: it restores the guard into the workflow.

Catalog: ``grok.sydney_morning`` in ``config/schedules/routines.yaml``.
``miss_after_seconds`` is 900. Anchor is 06:30 on the Sydney calendar date
of ``now`` (same rule as ``scheduled_slot``).

Known bugs for future tolerance work (current behaviour, recorded on purpose):

(a) Run ``actions-b1-35727756341``
    (``ops/reports/scheduler/completions/grok.sydney_morning__20260921T203000Z.json``)
    fired ``2026-09-22T12:32:21Z`` and recorded
    ``scheduled_for=2026-09-21T20:30:00Z`` (Tuesday 06:30 AEST, delta 57741).
    Principal: that derivation computed the Tuesday anchor for a Wednesday run.
    Wednesday 06:30 Australia/Sydney is ``2026-09-22T20:30:00Z``.
(b) ±900s is far too tight versus observed Actions drift. The schedule run
    created ``2026-09-22T22:21:07Z`` against the ``20:30Z`` cron; the skip log
    is ``delta_seconds=6682`` (~1h51m; ``now_utc`` ``2026-09-22T22:21:22Z``,
    actions run ``35791891126``). A later unguarded stamp
    ``actions-b1-35795814246`` landed at delta 9428 (~2h37m).

Paper only.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from mm_common.time import as_utc, parse_utc

SYDNEY = ZoneInfo("Australia/Sydney")
ANCHOR_LOCAL = time(6, 30, 0)
DEFAULT_MISS_AFTER_SECONDS = 900
ROUTINE_ID = "grok.sydney_morning"

REASON_WITHIN = "within_anchor_window"
REASON_OUTSIDE = "outside_anchor_window"
REASON_WEEKEND = "weekend_sydney"
REASON_FORCE = "force"

# Production evidence. Tests lock these so a silent change is visible.
# Future tolerance work replaces the rule; this extract does not.
KNOWN_BUG_A_RUN_ID = "actions-b1-35727756341"
KNOWN_BUG_A_FIRE = "2026-09-22T12:32:21Z"
KNOWN_BUG_A_ANCHOR = "2026-09-21T20:30:00Z"  # Tuesday 06:30 AEST
KNOWN_BUG_A_WEDNESDAY_SLOT = "2026-09-22T20:30:00Z"  # Wednesday 06:30 AEST
KNOWN_BUG_A_DELTA = 57741

KNOWN_BUG_B_ACTIONS_RUN = "35791891126"
KNOWN_BUG_B_CREATED = "2026-09-22T22:21:07Z"
KNOWN_BUG_B_NOW = "2026-09-22T22:21:22Z"
KNOWN_BUG_B_ANCHOR = "2026-09-22T20:30:00Z"
KNOWN_BUG_B_DELTA = 6682

OBSERVED_DRIFT_RUN_ID = "actions-b1-35795814246"
OBSERVED_DRIFT_NOW = "2026-09-22T23:07:08Z"
OBSERVED_DRIFT_DELTA = 9428


@dataclass(frozen=True)
class SydneyAnchorDecision:
    """Whether this instant is inside the catalog ±900s window.

    ``stamp`` is the decision. This object does not write a completion row.
    ``skip`` and ``stamp`` are exclusive. A skip is a successful no-op for a
    future caller (exit 0, no row). The live workflow does not consult it.
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

    def as_public_dict(self) -> dict[str, object]:
        return {
            "skip": self.skip,
            "stamp": self.stamp,
            "reason": self.reason,
            "delta_seconds": self.delta_seconds,
            "miss_after_seconds": self.miss_after_seconds,
            "anchor_utc": self.anchor_utc.isoformat(),
            "now_utc": self.now_utc.isoformat(),
            "local": self.local_iso,
            "force": self.force,
            "routine_id": ROUTINE_ID,
        }


def sydney_morning_anchor(now: datetime) -> datetime:
    """06:30 Australia/Sydney on the Sydney calendar date of ``now``, as UTC.

    Same rule as ``mm_desks.scheduler.scheduled_slot`` for ``grok.sydney_morning``.
    Known bug (a) is this rule at ``KNOWN_BUG_A_FIRE``.
    """
    now_u = as_utc(now)
    local = now_u.astimezone(SYDNEY)
    anchor_local = local.replace(
        hour=ANCHOR_LOCAL.hour,
        minute=ANCHOR_LOCAL.minute,
        second=0,
        microsecond=0,
    )
    return anchor_local.astimezone(timezone.utc)


def decide_sydney_morning_anchor(
    now: datetime,
    *,
    force: bool = False,
    miss_after_seconds: int = DEFAULT_MISS_AFTER_SECONDS,
) -> SydneyAnchorDecision:
    """±900s around today's 06:30 Australia/Sydney.

    Weekend Sydney (Sat/Sun) skips unless ``force``. ``force`` stamps outside
    the window and on a weekend. The live workflow has no force flag and does
    not call this function. Default ``force`` is false.
    """
    now_u = as_utc(now)
    local = now_u.astimezone(SYDNEY)
    anchor = sydney_morning_anchor(now_u)
    delta = int((now_u - anchor).total_seconds())
    tolerance = int(miss_after_seconds)
    within = abs(delta) <= tolerance

    def decision(skip: bool, reason: str) -> SydneyAnchorDecision:
        return SydneyAnchorDecision(
            skip=skip,
            stamp=not skip,
            reason=reason,
            delta_seconds=delta,
            miss_after_seconds=tolerance,
            anchor_utc=anchor,
            now_utc=now_u,
            local_iso=local.isoformat(),
            force=bool(force),
        )

    if force:
        return decision(False, REASON_FORCE)
    if local.weekday() >= 5:
        return decision(True, REASON_WEEKEND)
    if not within:
        return decision(True, REASON_OUTSIDE)
    return decision(False, REASON_WITHIN)


def main(argv: list[str] | None = None) -> int:
    """Print the decision JSON and exit 0.

    Skip and stamp are both exit 0. Callers read ``stamp``. Nothing here
    writes a completion or talks to Telegram.
    """
    parser = argparse.ArgumentParser(
        description="Sydney 06:30 ±900s decision (exit 0; read stamp). Not wired to Actions.",
    )
    parser.add_argument("--now", default="", help="UTC ISO instant; default is wall-clock now")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass the window (tests / a later PR). The live workflow has no force flag.",
    )
    parser.add_argument("--miss-after", type=int, default=DEFAULT_MISS_AFTER_SECONDS)
    args = parser.parse_args(argv)
    now = parse_utc(args.now) if args.now else datetime.now(timezone.utc)
    decision = decide_sydney_morning_anchor(
        now,
        force=bool(args.force),
        miss_after_seconds=args.miss_after,
    )
    print(json.dumps(decision.as_public_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
