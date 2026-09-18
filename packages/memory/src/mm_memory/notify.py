"""Postgres LISTEN/NOTIFY bus (Phase 6a). No Redis.

NOTIFY payload must stay small (Postgres limit 8000 bytes). Envelopes live
in ``desk_envelope``; notifications carry id / desk / as_of / content_hash.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from mm_common.hashing import canonical_json
from mm_memory.db import make_engine, normalize_dsn

NOTIFY_MAX_BYTES = 8000


def psycopg_dsn(dsn: str) -> str:
    normalized = normalize_dsn(dsn)
    if normalized.startswith("postgresql+psycopg://"):
        return "postgresql://" + normalized[len("postgresql+psycopg://") :]
    return normalized


@dataclass(frozen=True)
class PgNotifyEvent:
    channel: str
    payload: dict[str, Any]


class PostgresNotifyBus:
    """LISTEN/NOTIFY using a dedicated psycopg connection (autocommit)."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def notify(self, channel: str, payload: dict[str, Any]) -> None:
        blob = canonical_json(payload)
        if len(blob.encode("utf-8")) > NOTIFY_MAX_BYTES:
            raise ValueError("NOTIFY payload exceeds Postgres 8000-byte limit")
        engine = make_engine(self.dsn)
        with engine.connect() as conn:
            conn.execute(text("SELECT pg_notify(:channel, :payload)"), {"channel": channel, "payload": blob})
            conn.commit()

    def listen(
        self,
        channels: Sequence[str],
        *,
        timeout: float | None = None,
        stop_after: int | None = None,
        on_listening: Any | None = None,
    ) -> Iterator[PgNotifyEvent]:
        import psycopg
        from psycopg import sql

        yielded = 0
        with psycopg.connect(psycopg_dsn(self.dsn), autocommit=True) as conn:
            for channel in channels:
                conn.execute(sql.SQL("LISTEN {}").format(sql.Identifier(channel)))
            if on_listening is not None:
                on_listening()
            for notify in conn.notifies(timeout=timeout, stop_after=stop_after):
                raw = notify.payload or "{}"
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = {"raw": raw}
                if not isinstance(data, dict):
                    data = {"raw": raw}
                yield PgNotifyEvent(channel=notify.channel, payload=data)
                yielded += 1
                if stop_after is not None and yielded >= stop_after:
                    return
