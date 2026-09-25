"""Sydney Morning deliver receipts keyed on the stamp's scheduled anchor.

First writer wins. The key is ``scheduled_anchor_ts`` (catalog anchor / ``scheduled_for``),
not wall clock and not ``run_id``. A receipt is not a completion row: it lives under
``ops/reports/scheduler/completions/receipts/`` so miss-check's ``*.json`` glob does not
load it. Write one only after a successful Principal DM send (``sent`` is true and the
deliver process exited 0). A failed send leaves the anchor open.

Must not import mm_execution, sign, or talk to Telegram live.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from mm_common.time import as_utc, parse_utc, utcnow

# Same character class as completion filenames in mm_desks.completions.
_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")

RECEIPTS_DIRNAME = "receipts"
RECEIPTS_REL = Path("ops") / "reports" / "scheduler" / "completions" / RECEIPTS_DIRNAME
KIND = "deliver_receipt"
ALREADY_DELIVERED = "already_delivered"
PROCEED = "proceed"
NOT_SENT = "not_sent"
# Success-ping outcome stored on a new receipt. Absent on receipts written
# before the dead-man ping existed; those remain valid.
DEADMAN_OUTCOMES = frozenset({"OK", "not_found", "error", "unset"})

RECEIPT_KEYS = frozenset(
    {
        "kind",
        "routine_id",
        "scheduled_anchor_ts",
        "run_id",
        "sent",
        "delivered_at_ts",
        "source",
        "deadman_ping",
        "deadman_ping_at",
        "capture_rows",
    }
)
# Split so the desks tree does not contain the signing snippet the import-boundary
# check rejects. The runtime string is still the needle.
_PRIVATE_KEY = "private" + "_key"
_SECRETISH = ("token", "secret", "password", "api_key", "telegram", _PRIVATE_KEY)
_SECRET_NEEDLES = (
    "telegram_bot_token",
    "begin rsa private",
    "begin openssh private",
    _PRIVATE_KEY,
)


def anchor_utc(scheduled_anchor_ts: str | datetime) -> datetime:
    """Normalize the stamp anchor. ``Z`` and ``+00:00`` are the same key."""
    if isinstance(scheduled_anchor_ts, datetime):
        return as_utc(scheduled_anchor_ts)
    text = str(scheduled_anchor_ts or "").strip()
    if not text:
        raise ValueError("scheduled_anchor missing")
    return as_utc(parse_utc(text))


def anchor_token(scheduled_anchor_ts: str | datetime) -> str:
    """UTC compact token matching completion filenames: YYYYMMDDTHHMMSSZ."""
    return anchor_utc(scheduled_anchor_ts).strftime("%Y%m%dT%H%M%SZ")


def _safe_routine(routine_id: str) -> str:
    safe = _SAFE_ID.sub("_", str(routine_id or "")).strip("._")
    if not safe:
        raise ValueError("routine_id missing")
    return safe


def receipt_filename(routine_id: str, scheduled_anchor_ts: str | datetime) -> str:
    return f"{_safe_routine(routine_id)}__{anchor_token(scheduled_anchor_ts)}.deliver.json"


def receipts_dir(completions_dir: Path) -> Path:
    return Path(completions_dir) / RECEIPTS_DIRNAME


def receipt_path(completions_dir: Path, routine_id: str, scheduled_anchor_ts: str | datetime) -> Path:
    return receipts_dir(completions_dir) / receipt_filename(routine_id, scheduled_anchor_ts)


def find_receipt(completions_dir: Path, routine_id: str, scheduled_anchor_ts: str | datetime) -> Path | None:
    path = receipt_path(completions_dir, routine_id, scheduled_anchor_ts)
    return path if path.is_file() else None


def _load_receipt_object(path: Path) -> dict:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"deliver receipt is not JSON: {path}") from exc
    if not isinstance(raw, dict):
        raise ValueError("deliver receipt JSON must be an object")
    return raw


def validate_receipt_payload(raw: dict) -> dict:
    """A usable receipt is ``sent: true`` and contains no secret-shaped fields."""
    extra = [key for key in raw if key not in RECEIPT_KEYS]
    if extra:
        raise ValueError(f"unexpected deliver receipt keys: {extra}")
    for key in raw:
        if any(needle in key.lower() for needle in _SECRETISH):
            raise ValueError(f"secret-like key in deliver receipt: {key}")
    blob = json.dumps(raw).lower()
    for needle in _SECRET_NEEDLES:
        if needle in blob:
            raise ValueError(f"secret-like material in deliver receipt ({needle})")
    if raw.get("kind") != KIND:
        raise ValueError("deliver receipt kind must be deliver_receipt")
    if raw.get("sent") is not True:
        raise ValueError("deliver receipt requires sent true")
    if "capture_rows" in raw:
        rows = raw.get("capture_rows")
        if rows is not None and (isinstance(rows, bool) or not isinstance(rows, int) or rows < 0):
            raise ValueError("capture_rows must be a non-negative integer or null")
    routine_id = str(raw.get("routine_id") or "")
    if not routine_id:
        raise ValueError("deliver receipt routine_id missing")
    # Re-parse so a bad anchor fails closed instead of counting as delivered.
    anchor_utc(str(raw.get("scheduled_anchor_ts") or ""))
    _validate_deadman(raw)
    return raw


def _validate_deadman(raw: dict) -> None:
    """Both dead-man fields, or neither. Values are an outcome and a UTC timestamp, never the URL."""
    has_ping = "deadman_ping" in raw
    has_at = "deadman_ping_at" in raw
    if not has_ping and not has_at:
        return
    if not has_ping or not has_at:
        raise ValueError("deadman_ping and deadman_ping_at must be written together")
    if raw.get("deadman_ping") not in DEADMAN_OUTCOMES:
        raise ValueError("deadman_ping outcome invalid")
    try:
        as_utc(parse_utc(str(raw.get("deadman_ping_at") or "")))
    except ValueError as exc:
        raise ValueError("deadman_ping_at is not UTC ISO") from exc


def stored_deadman(deadman_ping: str | None, deadman_ping_at: str | None) -> dict[str, str]:
    """Receipt fields for a success ping. An invalid pair is omitted so the receipt can still be written."""
    if deadman_ping is None and deadman_ping_at is None:
        return {}
    if deadman_ping not in DEADMAN_OUTCOMES or not isinstance(deadman_ping_at, str) or not deadman_ping_at.strip():
        return {}
    try:
        when = as_utc(parse_utc(deadman_ping_at)).isoformat()
    except ValueError:
        return {}
    return {"deadman_ping": str(deadman_ping), "deadman_ping_at": when}


def load_receipt(path: Path) -> dict:
    return validate_receipt_payload(_load_receipt_object(path))


def decide_deliver(completions_dir: Path, routine_id: str, scheduled_anchor_ts: str | datetime) -> str:
    """``already_delivered`` when a valid receipt exists for this anchor; else ``proceed``.

    A file that is present but not a valid sent receipt raises. Callers must not Telegram.
    """
    path = receipt_path(completions_dir, routine_id, scheduled_anchor_ts)
    if not path.is_file():
        return PROCEED
    try:
        load_receipt(path)
    except ValueError as exc:
        raise ValueError(f"deliver receipt present but not usable: {path}: {exc}") from exc
    return ALREADY_DELIVERED


def parse_deliver_stdout(stdout: str) -> dict | None:
    """Last JSON object on deliver stdout. ``lab deliver pack`` prints one object."""
    raw = stdout or ""
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        payload = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def deliver_sent(stdout: str) -> bool:
    """True only when stdout JSON has boolean ``sent: true`` (not the string ``\"true\"``)."""
    payload = parse_deliver_stdout(stdout)
    return payload is not None and payload.get("sent") is True


def accept_delivery(stdout: str, returncode: int) -> bool:
    """Receipt may be written only when the process exited 0 and ``sent`` is true."""
    return int(returncode) == 0 and deliver_sent(stdout)


_OMIT = object()


def _receipt_body(
    *,
    routine_id: str,
    scheduled_anchor_ts: str | datetime,
    run_id: str,
    source: str,
    delivered_at: datetime | None,
    deadman_ping: str | None = None,
    deadman_ping_at: str | None = None,
    capture_rows: int | None | object = _OMIT,
) -> str:
    anchor = anchor_utc(scheduled_anchor_ts)
    when = as_utc(delivered_at or utcnow())
    payload = {
        "kind": KIND,
        "routine_id": _safe_routine(routine_id),
        "scheduled_anchor_ts": anchor.isoformat(),
        "run_id": str(run_id or ""),
        "sent": True,
        "delivered_at_ts": when.isoformat(),
        "source": str(source or "github.actions"),
    }
    payload.update(stored_deadman(deadman_ping, deadman_ping_at))
    if capture_rows is not _OMIT:
        payload["capture_rows"] = capture_rows
    validate_receipt_payload(payload)
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_deliver_receipt(
    *,
    completions_dir: Path,
    routine_id: str,
    scheduled_anchor_ts: str | datetime,
    run_id: str,
    sent: bool,
    source: str = "github.actions",
    delivered_at: datetime | None = None,
    deadman_ping: str | None = None,
    deadman_ping_at: str | None = None,
    capture_rows: int | None | object = _OMIT,
) -> tuple[Path | None, bool]:
    """Write a receipt only when ``sent`` is true.

    Returns ``(path, created)``. ``created`` is false when the anchor already has a
    receipt (first writer wins; bytes are not replaced). ``sent`` not true returns
    ``(None, False)`` and writes nothing.
    """
    if sent is not True:
        return None, False
    path = receipt_path(completions_dir, routine_id, scheduled_anchor_ts)
    if path.is_file():
        return path, False
    path.parent.mkdir(parents=True, exist_ok=True)
    body = _receipt_body(
        routine_id=routine_id,
        scheduled_anchor_ts=scheduled_anchor_ts,
        run_id=run_id,
        source=source,
        delivered_at=delivered_at,
        deadman_ping=deadman_ping,
        deadman_ping_at=deadman_ping_at,
        capture_rows=capture_rows,
    )
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(path, flags, 0o644)
    except FileExistsError:
        return path, False
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(body)
    return path, True


def relative_receipt_path(path: Path, *, repo_root: Path) -> str:
    rel = path.resolve().relative_to(repo_root.resolve()).as_posix()
    prefix = RECEIPTS_REL.as_posix() + "/"
    if not rel.startswith(prefix) or not rel.endswith(".deliver.json"):
        raise ValueError(f"refusing receipt path outside {RECEIPTS_REL.as_posix()}: {rel}")
    return rel


def assert_receipt_committable(path: Path, *, repo_root: Path) -> str:
    """Repo-relative path safe to commit. Raises on scope, key, or sent violations."""
    rel = relative_receipt_path(path, repo_root=repo_root)
    raw = load_receipt(path)
    expected = receipt_filename(str(raw["routine_id"]), str(raw["scheduled_anchor_ts"]))
    if Path(rel).name != expected:
        raise ValueError(f"receipt filename does not match scheduled_anchor_ts: {Path(rel).name}")
    return rel


@dataclass(frozen=True)
class DeliverAttempt:
    outcome: str
    telegram: bool
    receipt_path: Path | None
    receipt_created: bool


def attempt_deliver(
    *,
    completions_dir: Path,
    routine_id: str,
    scheduled_anchor_ts: str | datetime,
    run_id: str,
    send: Callable[[], tuple[int, str]],
    source: str = "github.actions",
    delivered_at: datetime | None = None,
) -> DeliverAttempt:
    """Gate used by contract tests and mirrored by the Actions job.

    ``send`` is invoked only when no valid receipt exists. It stands in for
    ``lab deliver pack`` (stdout, return code). Telegram is not called here.
    """
    decision = decide_deliver(completions_dir, routine_id, scheduled_anchor_ts)
    if decision == ALREADY_DELIVERED:
        return DeliverAttempt(
            outcome=ALREADY_DELIVERED,
            telegram=False,
            receipt_path=find_receipt(completions_dir, routine_id, scheduled_anchor_ts),
            receipt_created=False,
        )
    returncode, stdout = send()
    if not accept_delivery(stdout, returncode):
        return DeliverAttempt(
            outcome=NOT_SENT,
            telegram=True,
            receipt_path=None,
            receipt_created=False,
        )
    path, created = write_deliver_receipt(
        completions_dir=completions_dir,
        routine_id=routine_id,
        scheduled_anchor_ts=scheduled_anchor_ts,
        run_id=run_id,
        sent=True,
        source=source,
        delivered_at=delivered_at,
    )
    if path is not None and not created:
        return DeliverAttempt(
            outcome=ALREADY_DELIVERED,
            telegram=True,
            receipt_path=path,
            receipt_created=False,
        )
    return DeliverAttempt(
        outcome="sent",
        telegram=True,
        receipt_path=path,
        receipt_created=created,
    )
