"""ULID identifiers for Market Memory rows."""

from __future__ import annotations

import os
import time

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_ulid() -> str:
    """Return a 26-character Crockford-base32 ULID (UTC millisecond time + entropy)."""
    ts_ms = int(time.time() * 1000)
    entropy = int.from_bytes(os.urandom(10), "big")
    n = (ts_ms << 80) | entropy
    chars = ["0"] * 26
    for i in range(25, -1, -1):
        chars[i] = _CROCKFORD[n & 31]
        n >>= 5
    return "".join(chars)
