"""Improvement-queue hygiene (Phase 6e / IMP-030).

Ops-owned. Parses ops/improvement-queue.md. Enforces the single-threaded
READY→IN_PROGRESS slot. OPEN incidents do not occupy that slot.

Does **not** auto-merge, auto-waive gates, auto-close OPEN incidents, or
edit the queue file. Claim is a dry check only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

QUEUE_REL = Path("ops") / "improvement-queue.md"
STATUSES = (
    "OPEN",
    "BACKLOG",
    "READY",
    "IN_PROGRESS",
    "IN_REVIEW",
    "DONE",
    "PARKED",
    "REJECTED",
)
IMPLEMENTATION_STATUSES = frozenset({"BACKLOG", "READY", "IN_PROGRESS", "IN_REVIEW", "DONE", "PARKED", "REJECTED"})
REQUIRED_FIELDS = (
    "ID",
    "Priority",
    "Type",
    "Desk",
    "Owner",
    "Problem",
    "Evidence",
    "Proposed outcome",
    "Definition of done",
    "Non-goals",
    "Dependencies",
    "Risk level",
    "Status",
    "PR",
    "Lesson learned",
)
FORBIDDEN_ACTIONS = frozenset({"merge", "waive", "auto-merge", "auto-waive", "close-open", "promote-live"})
OPEN_INCIDENT_PREFIXES = ("SCHED-", "BRIEF-TAG-", "SRC-")
IMP_RE = re.compile(r"^IMP-\d+$")
FIELD_RE = re.compile(r"^\|\s*\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|$")
BOARD_RE = re.compile(r"^\|\s*(IMP-\d+|SCHED-\d+|BRIEF-TAG-[0-9A-Z-]+|SRC-[A-Z0-9-]+)\s*\|")
HEADING_RE = re.compile(r"^###\s+(\S+)")


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "packages").is_dir():
            return candidate
    return here


@dataclass(frozen=True)
class QueueItem:
    item_id: str
    status: str
    desk: str
    owner: str
    fields: dict[str, str]
    kind: str  # implementation | incident

    def canonical(self) -> dict[str, Any]:
        return {
            "id": self.item_id,
            "status": self.status,
            "desk": self.desk,
            "owner": self.owner,
            "kind": self.kind,
            "fields": dict(self.fields),
        }


@dataclass(frozen=True)
class QueueReport:
    path: str
    items: tuple[QueueItem, ...]
    in_progress: tuple[str, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    auto_merge: bool = False
    auto_waive: bool = False

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "ok": self.ok,
            "in_progress": list(self.in_progress),
            "in_progress_count": len(self.in_progress),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "auto_merge": self.auto_merge,
            "auto_waive": self.auto_waive,
            "n_items": len(self.items),
            "open_incidents": [i.item_id for i in self.items if i.kind == "incident" and i.status == "OPEN"],
        }


def _kind_for(item_id: str) -> str:
    if IMP_RE.match(item_id):
        return "implementation"
    return "incident"


def parse_queue(text: str) -> tuple[QueueItem, ...]:
    items: list[QueueItem] = []
    current_id: str | None = None
    fields: dict[str, str] = {}

    def flush() -> None:
        nonlocal current_id, fields
        if not current_id:
            fields = {}
            return
        status = str(fields.get("Status") or "").strip()
        items.append(
            QueueItem(
                item_id=current_id,
                status=status,
                desk=str(fields.get("Desk") or "").strip(),
                owner=str(fields.get("Owner") or "").strip(),
                fields=dict(fields),
                kind=_kind_for(current_id),
            )
        )
        current_id = None
        fields = {}

    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            flush()
            token = heading.group(1)
            current_id = token
            fields = {"ID": token}
            continue
        match = FIELD_RE.match(line)
        if match and current_id:
            key, value = match.group(1).strip(), match.group(2).strip()
            if key == "ID" and value:
                current_id = value
            fields[key] = value
    flush()
    return tuple(items)


def implementation_in_progress(items: tuple[QueueItem, ...]) -> tuple[str, ...]:
    return tuple(
        item.item_id
        for item in items
        if item.kind == "implementation" and item.status == "IN_PROGRESS"
    )


def check_queue(text: str, *, path: str = str(QUEUE_REL)) -> QueueReport:
    items = parse_queue(text)
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item.item_id in seen:
            errors.append(f"duplicate id {item.item_id}")
        seen.add(item.item_id)
        if item.status not in STATUSES:
            errors.append(f"{item.item_id} has unknown status {item.status!r}")
        if item.kind == "implementation":
            missing = [name for name in REQUIRED_FIELDS if not str(item.fields.get(name) or "").strip()]
            if missing:
                errors.append(f"{item.item_id} missing required fields: {', '.join(missing)}")
            if item.status == "OPEN":
                errors.append(f"{item.item_id} is an implementation item with OPEN; OPEN is for incidents")
        if item.kind == "incident" and item.status not in {"OPEN", "DONE", "PARKED"}:
            warnings.append(f"{item.item_id} incident status {item.status!r} (incidents stay OPEN until verified)")
    in_progress = implementation_in_progress(items)
    if len(in_progress) > 1:
        errors.append(
            "single-threaded rule: at most one IMP-* IN_PROGRESS; found "
            + ", ".join(in_progress)
        )
    return QueueReport(
        path=path,
        items=items,
        in_progress=in_progress,
        errors=tuple(errors),
        warnings=tuple(warnings),
        auto_merge=False,
        auto_waive=False,
    )


def load_queue(root: Path | None = None) -> QueueReport:
    base = repo_root(root)
    path = base / QUEUE_REL
    text = path.read_text(encoding="utf-8")
    return check_queue(text, path=str(path))


def can_start(item_id: str, report: QueueReport) -> tuple[bool, str]:
    """READY→IN_PROGRESS aid. Does not write the queue. Does not waive gates."""
    target = next((item for item in report.items if item.item_id == item_id), None)
    if target is None:
        return False, f"{item_id} is not in the queue"
    if target.kind != "implementation":
        return False, f"{item_id} is an incident; OPEN incidents do not occupy IN_PROGRESS and cannot be claimed"
    if target.status == "IN_PROGRESS":
        return False, f"{item_id} is already IN_PROGRESS"
    if target.status != "READY":
        return False, f"{item_id} status is {target.status}; only READY may move to IN_PROGRESS"
    others = [iid for iid in report.in_progress if iid != item_id]
    if others:
        return False, f"slot occupied by {', '.join(others)}; park or finish that item first"
    if report.errors:
        return False, "queue hygiene failed: " + "; ".join(report.errors)
    return True, f"{item_id} may move READY→IN_PROGRESS (operator edits the queue; helper does not write)"


def refuse_forbidden(action: str | None) -> str | None:
    if not action:
        return None
    key = action.strip().lower()
    if key in FORBIDDEN_ACTIONS:
        return f"queue helper refuses {key!r}: no auto-merge, no gate waiver, no auto-close of OPEN incidents"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="improvement-queue hygiene (read-only)")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--can-start", dest="can_start_id", help="check READY→IN_PROGRESS without writing")
    parser.add_argument("--merge", action="store_true", help="forbidden")
    parser.add_argument("--waive", action="store_true", help="forbidden")
    args = parser.parse_args(argv)
    for flag, name in ((args.merge, "merge"), (args.waive, "waive")):
        if flag:
            print(refuse_forbidden(name), file=sys.stderr)
            return 2
    report = load_queue(args.repo_root)
    payload = report.as_public_dict()
    if args.can_start_id:
        ok, reason = can_start(str(args.can_start_id), report)
        payload["can_start"] = {"id": args.can_start_id, "ok": ok, "reason": reason}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if ok and report.ok else 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
