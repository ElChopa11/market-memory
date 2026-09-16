"""Canonical JSON + SHA-256 helpers for claim dedupe and object checksums."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=_default)


def _default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def claim_hash(payload: dict[str, Any]) -> str:
    """Hash a canonical claim identity. Must not include ingested_at (knowledge time)."""
    return sha256_hex(canonical_json(payload))


def normalize_numeric(value: Any) -> str | None:
    """Stable decimal string for prices/rates so '65000.0' and '65000.00' collide."""
    if value is None or value == "":
        return None
    decimal = Decimal(str(value))
    normalized = format(decimal.normalize(), "f")
    if normalized == "-0":
        return "0"
    return normalized
