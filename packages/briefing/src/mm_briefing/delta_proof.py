"""Live close plus one BTC delta line for workflow mode ``delta_proof``.

The first act is the expiry gate. Today's date is the system UTC clock
converted with ``zoneinfo`` ``Australia/Sydney``. It is not a dispatch input,
env var, or event field. A Sydney date after ``DELTA_PROOF_LAST_SYDNEY_DATE``
exits before any secret is read and before any fetch or database access.

The brief text is ``build_close_proof`` (the same ``generate_from_sources``
live, no-db path ``render_proof`` uses). A missing Polygon or FRED key leaves
those slots unavailable and does not abort this proof.

One read-only ``observation`` query supplies the BTC line. Any failure,
timeout, or missing ``POSTGRES_DSN`` prints ``n/a`` and exits 0. This module
does not send, write a receipt, stamp, capture, ping, or commit.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo

from mm_briefing.render_proof import build_close_proof

DELTA_PROOF_LAST_SYDNEY_DATE = date(2026, 10, 2)
QUERY_WALL_S = 5.0
CONNECT_TIMEOUT_S = 5
STATEMENT_TIMEOUT_MS = 5000
DELTA_LINE_PREFIX = "BTC vs prior capture: "
_SYDNEY = ZoneInfo("Australia/Sydney")
_WEEKDAY = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

# One SELECT. Proof and render rows are not morning captures.
BTC_DELTA_SQL = (
    "SELECT payload_json->>'value' AS value, "
    "payload_json->>'captured_at' AS captured_at "
    "FROM observation "
    "WHERE instrument = 'BTC' "
    "AND metric = 'mid_px' "
    "AND payload_json->>'retain_series' = 'mvp_retain' "
    "AND COALESCE(payload_json->>'capture_kind', '') NOT IN ('proof', 'render') "
    "ORDER BY payload_json->>'captured_at' DESC "
    "LIMIT 2"
)
_READ_ONLY_SQL = "SET TRANSACTION READ ONLY"
_STATEMENT_TIMEOUT_SQL = f"SET statement_timeout = {STATEMENT_TIMEOUT_MS}"


@dataclass(frozen=True)
class BtcCapture:
    value: str | None
    captured_at: str | None


@dataclass(frozen=True)
class DeltaOutcome:
    state: str
    label: str
    query_ms: int

    @property
    def line(self) -> str:
        return f"{DELTA_LINE_PREFIX}{self.label}"


def utc_now() -> datetime:
    """System UTC. Tests replace this seam. Production does not read a date input."""
    return datetime.now(timezone.utc)


def main() -> int:
    today = utc_now().astimezone(_SYDNEY).date()
    if today > DELTA_PROOF_LAST_SYDNEY_DATE:
        print(
            json.dumps(
                {
                    "proof": "delta_proof",
                    "ok": False,
                    "reason": "delta_proof_expired",
                    "sydney_date": today.isoformat(),
                }
            )
        )
        return 1

    text, _sources = build_close_proof()
    outcome = read_delta_bounded()
    base = text if text.endswith("\n") else text + "\n"
    shown = base + outcome.line + "\n"
    payload = {
        "proof": "delta_proof",
        "ok": True,
        "delta_state": outcome.state,
        "query_ms": outcome.query_ms,
        "sent": False,
        "wrote": False,
        "pinged": False,
    }
    encoded = json.dumps(payload)
    print(shown, end="")
    print(encoded)
    raw = os.environ.get("GITHUB_STEP_SUMMARY")
    if raw:
        Path(raw).write_text(shown + encoded + "\n", encoding="utf-8")
    return 0


def read_delta_bounded() -> DeltaOutcome:
    """Wall-cap the read. Missing DSN, timeout, and any error are ``n/a``."""
    dsn = os.environ.get("POSTGRES_DSN")
    if dsn is None or not str(dsn).strip():
        return DeltaOutcome("na", "n/a", 0)
    started = time.perf_counter()
    box: dict[str, object] = {}

    def target() -> None:
        try:
            box["rows"] = query_btc_captures(str(dsn))
        except Exception:
            box["error"] = True

    thread = threading.Thread(target=target, name="delta-proof-read", daemon=True)
    thread.start()
    thread.join(QUERY_WALL_S)
    elapsed = int((time.perf_counter() - started) * 1000)
    if thread.is_alive() or box.get("error") or "rows" not in box:
        return DeltaOutcome("na", "n/a", elapsed)
    try:
        state, label = describe_delta(box["rows"])  # type: ignore[arg-type]
    except Exception:
        return DeltaOutcome("na", "n/a", elapsed)
    return DeltaOutcome(state, label, elapsed)


def query_btc_captures(dsn: str) -> list[BtcCapture]:
    """Open one short read-only session and return at most two BTC mids.

    ``SET TRANSACTION READ ONLY`` runs before the SELECT. The session is
    rolled back and closed. The DSN is not logged.
    """
    from sqlalchemy import create_engine, text

    from mm_memory.db import normalize_dsn

    engine = create_engine(
        normalize_dsn(dsn),
        echo=False,
        future=True,
        pool_pre_ping=False,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_S},
    )
    conn = None
    try:
        conn = engine.connect()
        conn.execute(text(_READ_ONLY_SQL))
        conn.execute(text(_STATEMENT_TIMEOUT_SQL))
        result = conn.execute(text(BTC_DELTA_SQL))
        found: list[BtcCapture] = []
        for rec in result.mappings():
            raw_value = rec["value"]
            raw_at = rec["captured_at"]
            found.append(
                BtcCapture(
                    value=None if raw_value is None else str(raw_value),
                    captured_at=None if raw_at is None else str(raw_at),
                )
            )
        return found
    finally:
        if conn is not None:
            try:
                conn.rollback()
            finally:
                conn.close()
        engine.dispose()


def describe_delta(rows: list[BtcCapture]) -> tuple[str, str]:
    """``first`` is one capture. ``ok`` is a signed percent. Anything else is ``na``."""
    if len(rows) == 1:
        return "first", "n/a"
    if len(rows) < 2:
        return "na", "n/a"
    latest_n = _decimal(rows[0].value)
    prior_n = _decimal(rows[1].value)
    day = _sydney_weekday(rows[1].captured_at)
    if latest_n is None or prior_n is None or prior_n == 0 or day is None:
        return "na", "n/a"
    pct = ((latest_n - prior_n) / prior_n * Decimal("100")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return "ok", f"{pct:+.2f}% since {day} 06:30 capture"


def _decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "n/a", "na"}:
        return None
    try:
        number = Decimal(text)
    except Exception:
        return None
    if not number.is_finite():
        return None
    return number


def _sydney_weekday(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return _WEEKDAY[moment.astimezone(_SYDNEY).weekday()]


if __name__ == "__main__":
    sys.exit(main())
