"""Healthchecks.io dead-man ping for the Sydney morning Principal DM.

The ping URL is a secret. This module never prints it. A ping failure is an
outcome (``error`` / ``unset`` / ``not_found``), not an exception: callers
still send the DM and still write a deliver receipt.

``/start`` runs only on the path that will send. The success URL runs after
``sent: true``, and again when the anchor is ``already_delivered`` (no DM).
A failed send does not success-ping.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlsplit, urlunsplit

from mm_common.time import as_utc, parse_utc, utcnow
from mm_desks.deliver_receipt import ALREADY_DELIVERED, DEADMAN_OUTCOMES

HEALTHCHECKS_PING_URL_ENV = "HEALTHCHECKS_PING_URL"
DEADMAN_MISSING_LINE = "DEADMAN: MISSING"
DEADMAN_PING_TIMEOUT_SECONDS = 5.0

HttpGet = Callable[[str, float], tuple[int, str]]


@dataclass(frozen=True)
class DeadmanPing:
    outcome: str
    pinged_at: str
    kind: str

    def log_line(self) -> str:
        return f"deadman {self.kind} ping: {self.outcome}"


def _target_url(url: str, kind: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme not in {"https", "http"} or not parts.netloc:
        raise ValueError("unsupported deadman ping url")
    path = parts.path or ""
    if kind == "start":
        path = path.rstrip("/") + "/start"
    elif kind == "success":
        path = path.rstrip("/") or "/"
    else:
        raise ValueError("unsupported deadman ping kind")
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, ""))


def _redact(text: str, url: str | None) -> str:
    raw = (url or "").strip()
    if not raw or raw not in text:
        redacted = text
    else:
        redacted = text.replace(raw, "***")
    try:
        start = _target_url(raw, "start") if raw else ""
    except ValueError:
        start = ""
    if start and start in redacted:
        redacted = redacted.replace(start, "***")
    return redacted


def _classify(status: int, body: str) -> str:
    text = body.strip()
    if status == 200 and text == "OK":
        return "OK"
    if status == 404 or text == "not found":
        return "not_found"
    return "error"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is not HTTP 200 OK. Do not follow it (the Location is not logged)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)


def _http_get(url: str, timeout: float) -> tuple[int, str]:
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "market-memory-deadman"})
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=timeout) as response:
            status = int(response.status)
            raw = response.read(256)
    except urllib.error.HTTPError as exc:
        try:
            status = int(exc.code)
            raw = exc.read(256) if exc.fp is not None else b""
        finally:
            exc.close()
    return status, raw.decode("utf-8", errors="replace").strip()


def _stamp() -> str:
    return as_utc(utcnow()).isoformat()


def ping_deadman(
    url: str | None,
    *,
    kind: str,
    timeout: float = DEADMAN_PING_TIMEOUT_SECONDS,
    http_get: HttpGet | None = None,
) -> DeadmanPing:
    """GET the ping URL once. Never raises. Never returns the URL."""
    when = _stamp()
    if kind not in {"start", "success"}:
        return DeadmanPing(outcome="error", pinged_at=when, kind="success")
    raw = (url or "").strip()
    if not raw:
        return DeadmanPing(outcome="unset", pinged_at=when, kind=kind)
    getter = http_get or _http_get
    try:
        status, body = getter(_target_url(raw, kind), timeout)
        outcome = _classify(status, body)
    except Exception:
        outcome = "error"
    if outcome not in DEADMAN_OUTCOMES:
        outcome = "error"
    return DeadmanPing(outcome=outcome, pinged_at=when, kind=kind)


def emit_deadman_log(ping: DeadmanPing, url: str | None) -> None:
    """Job log line. Stderr so a deliver JSON stdout stays one object."""
    print(_redact(ping.log_line(), url), file=sys.stderr)


def apply_deadman_missing_line(markdown: str) -> str:
    """Append ``DEADMAN: MISSING`` once, after any LATE line already on the markdown."""
    line = DEADMAN_MISSING_LINE
    if markdown.endswith("\n"):
        return f"{markdown}{line}\n"
    if markdown:
        return f"{markdown}\n{line}\n"
    return f"{line}\n"


def _ping_and_log(url: str | None, *, kind: str, http_get: HttpGet | None = None) -> DeadmanPing:
    try:
        ping = ping_deadman(url, kind=kind, http_get=http_get)
        emit_deadman_log(ping, url)
        return ping
    except Exception:
        print(f"deadman {kind} ping: error", file=sys.stderr)
        return DeadmanPing(outcome="error", pinged_at=_stamp(), kind=kind)


def ping_deadman_start(url: str | None, *, http_get: HttpGet | None = None) -> DeadmanPing:
    """``/start`` before a Principal DM that this process is about to send."""
    return _ping_and_log(url, kind="start", http_get=http_get)


def ping_deadman_success(url: str | None, *, http_get: HttpGet | None = None) -> DeadmanPing:
    """Success ping. Does not send Telegram and does not write a receipt."""
    return _ping_and_log(url, kind="success", http_get=http_get)


def ping_success_if_already_delivered(
    decision: str,
    url: str | None = None,
    *,
    http_get: HttpGet | None = None,
) -> DeadmanPing | None:
    """Success ping when a receipt already exists. No start ping, no DM, no receipt write."""
    if decision != ALREADY_DELIVERED:
        return None
    secret = os.environ.get(HEALTHCHECKS_PING_URL_ENV) if url is None else url
    return ping_deadman_success(secret, http_get=http_get)


def deadman_receipt_fields(payload: dict) -> dict[str, str]:
    """Copy a success-ping outcome onto a receipt. Invalid or absent fields are omitted.

    Omitting them lets the receipt still be written. The ping URL is not a field.
    """
    if not isinstance(payload, dict):
        return {}
    outcome = payload.get("deadman_ping")
    at = payload.get("deadman_ping_at")
    if outcome is None and at is None:
        return {}
    if outcome not in DEADMAN_OUTCOMES or not isinstance(at, str) or not at.strip():
        return {}
    try:
        when = as_utc(parse_utc(at)).isoformat()
    except ValueError:
        return {}
    return {"deadman_ping": str(outcome), "deadman_ping_at": when}
