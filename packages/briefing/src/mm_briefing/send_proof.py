"""Send the render_proof morning close once to the Principal DM.

The first act is the expiry gate. Today's date is the system UTC clock
converted with ``zoneinfo`` ``Australia/Sydney``. It is not a dispatch input,
env var, or event field. A Sydney date after ``SEND_PROOF_LAST_SYDNEY_DATE``
exits before any secret is read and before any fetch or send.

The brief text is ``build_close_proof`` (the same function ``render_proof``
uses). A Polygon or FRED missing-key failure is ``fail_lines`` and a non-zero
exit before any send.

The bytes that follow are the ``lab deliver pack --to-principal-dm`` path
with no LATE line, no DEADMAN line, no receipt, no Neon write, and no ping:

* ``append_brief_status_lines`` with capture ``CAPTURE: n/a (send_proof)``
* ``deliver(..., send=True, respect_quiet_hours=False,
  chat_id_env_override=TELEGRAM_CHAT_ID_PRINCIPAL_DM)``

``deliver`` evaluates gates (quiet hours are ignored, matching
``--ignore-quiet-hours``), builds the payload through ``chunk_markdown_v2``
(which calls ``escape_markdown_v2``), and POSTs each chunk with
``TelegramClient.send_message`` at MarkdownV2. A single chunk has no
``[i/n]`` prefix. ``out_root`` is omitted, so no payload file is written.
The dedupe store stays in memory. ``TELEGRAM_CHAT_ID`` is not the destination;
``deliver`` refuses only when that value equals the Principal DM id.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from mm_briefing.render_proof import build_close_proof, fail_lines
from mm_common.env import PRINCIPAL_DM_CHAT_ID_ENV
from mm_common.time import utcnow
from mm_delivery.deliver import deliver
from mm_lab_cli.deliver import append_brief_status_lines

CAPTURE_LINE = "CAPTURE: n/a (send_proof)"
SEND_PROOF_LAST_SYDNEY_DATE = date(2026, 9, 28)
_SYDNEY = ZoneInfo("Australia/Sydney")


def utc_now() -> datetime:
    """System UTC. Tests replace this seam. Production does not read a date input."""
    return datetime.now(timezone.utc)


def main() -> int:
    today = utc_now().astimezone(_SYDNEY).date()
    if today > SEND_PROOF_LAST_SYDNEY_DATE:
        _emit_expired(today)
        return 1

    text, sources = build_close_proof()
    failed = fail_lines(sources)
    if failed:
        for line in failed:
            print(line)
        _emit(sent=False, http_status=None, reason="render_proof_fail", message_length=0)
        return 1

    markdown = append_brief_status_lines(text, capture=CAPTURE_LINE)
    result = deliver(
        markdown,
        desk="ops",
        as_of=utcnow(),
        send=True,
        kind="desk_pack",
        completeness_pct=100.0,
        respect_quiet_hours=False,
        chat_id_env_override=PRINCIPAL_DM_CHAT_ID_ENV,
    )
    http_status = result.results[0].status_code if result.results else None
    message_length = sum(len(chunk) for chunk in result.payload.chunks)
    _emit(
        sent=bool(result.sent),
        http_status=http_status,
        reason=str(result.reason),
        message_length=message_length,
    )
    return 0 if result.sent else 1


def _emit_expired(today: date) -> None:
    payload = {
        "reason": "send_proof_expired",
        "sent": False,
        "sydney_date": today.isoformat(),
    }
    print(json.dumps(payload, sort_keys=True))
    line = f"send_proof sent=false reason=send_proof_expired sydney_date={today.isoformat()}"
    print(line)
    raw = os.environ.get("GITHUB_STEP_SUMMARY")
    if raw:
        Path(raw).write_text(line + "\n", encoding="utf-8")


def _emit(*, sent: bool, http_status: int | None, reason: str, message_length: int) -> None:
    payload = {
        "http_status": http_status,
        "message_length": message_length,
        "reason": reason,
        "sent": sent,
    }
    print(json.dumps(payload, sort_keys=True))
    status = "none" if http_status is None else str(http_status)
    line = (
        f"send_proof sent={str(sent).lower()} http_status={status} "
        f"reason={reason} message_length={message_length}"
    )
    print(line)
    raw = os.environ.get("GITHUB_STEP_SUMMARY")
    if raw:
        Path(raw).write_text(line + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
