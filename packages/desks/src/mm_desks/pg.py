"""Postgres LISTEN/NOTIFY adapters for the desk mesh. No Redis.

``mm_memory`` owns tables + raw NOTIFY. This module adapts them to the
``Bus`` / ``EnvelopeStore`` protocols used by the Coord worker stub.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from datetime import datetime

from sqlalchemy.orm import Session

from mm_common.time import as_utc
from mm_desks.bus import NotifyEvent
from mm_desks.envelope import DeskEnvelope, envelope_from_row
from mm_memory.envelope_repository import MeshEnvelopeRepository
from mm_memory.notify import PostgresNotifyBus


class PostgresEnvelopeStore:
    def __init__(self, session: Session) -> None:
        self.repo = MeshEnvelopeRepository(session)

    def put(self, envelope: DeskEnvelope) -> bool:
        _row, inserted = self.repo.put(envelope.as_row())
        return inserted

    def get(self, envelope_id: str) -> DeskEnvelope | None:
        row = self.repo.get(envelope_id)
        return envelope_from_row(row) if row is not None else None

    def latest(self, desk: str, as_of: datetime) -> DeskEnvelope | None:
        row = self.repo.latest(desk, as_utc(as_of))
        return envelope_from_row(row) if row is not None else None

    def list_for_as_of(self, as_of: datetime) -> list[DeskEnvelope]:
        return [envelope_from_row(row) for row in self.repo.list_for_as_of(as_utc(as_of))]


class PostgresBus:
    def __init__(self, dsn: str) -> None:
        self._inner = PostgresNotifyBus(dsn)

    def notify(self, channel: str, payload: dict) -> None:
        self._inner.notify(channel, payload)

    def listen(
        self,
        channels: Sequence[str],
        *,
        timeout: float | None = None,
        stop_after: int | None = None,
        on_listening=None,
    ) -> Iterator[NotifyEvent]:
        for event in self._inner.listen(
            channels, timeout=timeout, stop_after=stop_after, on_listening=on_listening
        ):
            yield NotifyEvent(channel=event.channel, payload=event.payload)
