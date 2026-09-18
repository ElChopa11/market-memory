"""Idempotency key per (desk, as_of, content_hash) and TTL dedupe store."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import as_utc, parse_utc


def idempotency_key(*, desk: str, as_of: datetime, content_hash: str) -> str:
    payload = {
        "desk": desk,
        "as_of": as_utc(as_of).isoformat(),
        "content_hash": content_hash,
    }
    return sha256_hex(canonical_json(payload))


@dataclass
class DedupeStore:
    """Remember sent keys for ttl_seconds. File-backed when path is set; else memory."""

    ttl_seconds: int = 86400
    path: Path | None = None
    records: dict[str, str] = field(default_factory=dict)

    def load(self) -> None:
        if self.path is None or not self.path.is_file():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            self.records = {str(k): str(v) for k, v in raw.items()}

    def dump(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.records, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    def prune(self, now: datetime) -> None:
        cutoff = as_utc(now) - timedelta(seconds=max(0, int(self.ttl_seconds)))
        keep: dict[str, str] = {}
        for key, stamp in self.records.items():
            try:
                when = parse_utc(stamp)
            except (ValueError, TypeError):
                continue
            if when >= cutoff:
                keep[key] = stamp
        self.records = keep

    def seen(self, key: str, now: datetime) -> bool:
        self.prune(now)
        return key in self.records

    def remember(self, key: str, now: datetime) -> None:
        self.records[key] = as_utc(now).isoformat()
        self.dump()

    def canonical(self) -> dict[str, Any]:
        return {"ttl_seconds": self.ttl_seconds, "keys": sorted(self.records)}
