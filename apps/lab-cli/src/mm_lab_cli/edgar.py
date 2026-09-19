"""lab data edgar — paper probe for SEC filings / CBRS+SPCX lockups.

Default is dry-run (``--no-db``). Never sends Telegram. 403 → unavailable.
"""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from mm_common.time import parse_utc, utcnow
from mm_ingest.config import load_ingest_settings
from mm_ingest.edgar import load_lockup_targets, pull_lockup_targets
from mm_ingest.edgar_stack import edgar_envelopes, run_edgar_stack, write_edgar_artifact
from mm_ingest.pipeline import envelopes_from_fixture, load_fixture_file


def add_edgar_parser(data_sub) -> None:
    edgar = data_sub.add_parser(
        "edgar",
        help="SEC EDGAR filings/lockup probe (paper; no Telegram send)",
    )
    edgar.add_argument("--fixture", type=Path, help="JSON/YAML stored-filing fixture")
    edgar.add_argument("--lockups", action="store_true", help="CBRS+SPCX lockup targets from monitor.yaml")
    edgar.add_argument("--live", action="store_true", help="fetch Archives (403 → unavailable; never invent text)")
    edgar.add_argument("--no-db", action="store_true", help="dry-run envelopes without Postgres (ELIGIBLE only)")
    edgar.add_argument("--as-of", help="UTC instant for ingested_at (ISO-8601)")
    edgar.add_argument("--repo-root", type=Path, default=Path("."), help="repo root for artifacts")
    edgar.add_argument("--write-artifact", action="store_true", help="write ops/reports/edgar/YYYY-MM-DD.md")


def cmd_edgar(args: Namespace) -> int:
    settings = load_ingest_settings()
    ingested = parse_utc(args.as_of) if args.as_of else utcnow()
    stale = int(settings.get("stale_after_seconds") or 120)
    if args.fixture:
        fixture = load_fixture_file(Path(args.fixture))
        envelopes = envelopes_from_fixture(fixture, stale_after_seconds=stale)
    elif args.lockups and args.live:
        envelopes = pull_lockup_targets(
            load_lockup_targets(),
            ingested_at=ingested,
            settings=settings,
            stale_after_seconds=stale,
        )
    elif args.lockups:
        print(
            json.dumps(
                {
                    "error": "lab data edgar --lockups requires --fixture (stored filing) or --live",
                    "hint": "live Archives may 403; never invent filing text",
                }
            )
        )
        return 2
    else:
        print("usage: lab data edgar --fixture PATH --no-db | lab data edgar --lockups --live --no-db")
        return 2

    # Probe is paper-only. Persist goes through `lab ingest` (not this command).
    stack = run_edgar_stack(envelopes, no_db=True)
    if args.write_artifact:
        day = ingested.date().isoformat()
        write_edgar_artifact(stack, Path(args.repo_root).resolve(), day=day)
    payload = stack.as_public_dict()
    payload["qualities"] = sorted({row.data_quality.value for row in edgar_envelopes(envelopes)})
    print(json.dumps(payload))
    return 0
