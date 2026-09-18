"""Desk mesh bus protocol.

Principal lock: Postgres LISTEN/NOTIFY is the only production bus (IMP-014).
This module holds the in-memory stand-in for ``--no-db`` / fixture tests.
There is no Redis client and no Redis-as-source-of-truth.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from mm_common.hashing import canonical_json
from mm_common.time import as_utc
from mm_desks.envelope import NOTIFY_MAX_BYTES, DeskEnvelope


@dataclass(frozen=True)
class NotifyEvent:
    channel: str
    payload: dict[str, Any]


class Bus(Protocol):
    def notify(self, channel: str, payload: dict[str, Any]) -> None: ...

    def listen(
        self,
        channels: Sequence[str],
        *,
        timeout: float | None = None,
        stop_after: int | None = None,
    ) -> Iterator[NotifyEvent]: ...


class EnvelopeStore(Protocol):
    def put(self, envelope: DeskEnvelope) -> bool:
        """Insert if new. Return True when a row was created (NOTIFY this)."""

    def get(self, envelope_id: str) -> DeskEnvelope | None: ...

    def latest(self, desk: str, as_of: datetime) -> DeskEnvelope | None: ...

    def list_for_as_of(self, as_of: datetime) -> list[DeskEnvelope]: ...


class InMemoryBus:
    """Fixture bus. Same channel names as PG NOTIFY; no network."""

    def __init__(self) -> None:
        self.events: list[NotifyEvent] = []

    def notify(self, channel: str, payload: dict[str, Any]) -> None:
        blob = canonical_json(payload)
        if len(blob.encode("utf-8")) > NOTIFY_MAX_BYTES:
            raise ValueError("NOTIFY payload exceeds Postgres 8000-byte limit")
        self.events.append(NotifyEvent(channel=channel, payload=dict(payload)))

    def listen(
        self,
        channels: Sequence[str],
        *,
        timeout: float | None = None,
        stop_after: int | None = None,
        on_listening: Any | None = None,
    ) -> Iterator[NotifyEvent]:
        if on_listening is not None:
            on_listening()
        wanted = set(channels)
        yielded = 0
        for event in list(self.events):
            if event.channel in wanted:
                yield event
                yielded += 1
                if stop_after is not None and yielded >= stop_after:
                    return


class InMemoryEnvelopeStore:
    def __init__(self) -> None:
        self._by_id: dict[str, DeskEnvelope] = {}
        self._order: list[str] = []

    def put(self, envelope: DeskEnvelope) -> bool:
        key = (envelope.desk, envelope.as_of_utc.isoformat(), envelope.content_hash)
        for existing in self._by_id.values():
            if (existing.desk, existing.as_of_utc.isoformat(), existing.content_hash) == key:
                return False
        self._by_id[envelope.envelope_id] = envelope
        self._order.append(envelope.envelope_id)
        return True

    def get(self, envelope_id: str) -> DeskEnvelope | None:
        return self._by_id.get(envelope_id)

    def latest(self, desk: str, as_of: datetime) -> DeskEnvelope | None:
        watermark = as_utc(as_of)
        found: DeskEnvelope | None = None
        for envelope_id in self._order:
            env = self._by_id[envelope_id]
            if env.desk == desk and env.as_of_utc == watermark:
                found = env
        return found

    def list_for_as_of(self, as_of: datetime) -> list[DeskEnvelope]:
        watermark = as_utc(as_of)
        return [self._by_id[i] for i in self._order if self._by_id[i].as_of_utc == watermark]


@dataclass
class DeskHealth:
    desk: str
    status: str
    last_as_of: datetime | None = None
    last_envelope_id: str | None = None
    last_content_hash: str | None = None
    error_class: str | None = None
    n: int = 0
    completeness: float = 0.0

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "desk": self.desk,
            "status": self.status,
            "last_as_of": self.last_as_of.isoformat() if self.last_as_of else None,
            "last_envelope_id": self.last_envelope_id,
            "last_content_hash": self.last_content_hash,
            "error_class": self.error_class,
            "n": self.n,
            "completeness": self.completeness,
        }
