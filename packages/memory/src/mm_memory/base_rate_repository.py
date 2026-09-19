"""Persist unconditional event-class base-rate snapshots into Market Memory.

Accepts the Quant artifact payload (dicts). Must not import mm_quant.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from mm_common.ids import new_ulid
from mm_common.time import as_utc, parse_utc
from mm_memory.models import EventBaseRate


def _dec(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value))


def persist_memory_rows(session: Session, rows: list[Mapping[str, Any]]) -> list[str]:
    """Insert one row per event class. Same (class, params_hash, as_of) is idempotent."""
    ids: list[str] = []
    for payload in rows:
        event_class = str(payload["event_class"])
        as_of = as_utc(parse_utc(str(payload["as_of_knowledge"])))
        ingested = as_utc(parse_utc(str(payload.get("ingested_at") or payload["as_of_knowledge"])))
        if as_of != ingested:
            raise ValueError("as_of_knowledge must lockstep ingested_at")
        params_hash = str(payload["params_hash"])
        existing = session.scalar(
            select(EventBaseRate).where(
                EventBaseRate.event_class == event_class,
                EventBaseRate.params_hash == params_hash,
                EventBaseRate.as_of_knowledge == as_of,
            )
        )
        if existing is not None:
            ids.append(existing.id)
            continue
        row = EventBaseRate(
            id=new_ulid(),
            event_class=event_class,
            as_of_knowledge=as_of,
            ingested_at=ingested,
            params_hash=params_hash,
            content_hash=str(payload["content_hash"]),
            instrument_set=list(payload.get("instrument_set") or []),
            window_json=dict(payload.get("window") or {}),
            cost_model_json=dict(payload.get("cost_model") or {}),
            n=int(payload.get("n") or 0),
            n_min=int(payload.get("n_min") or 20),
            claimed=bool(payload.get("claimed")),
            hit_rate=_dec(payload.get("hit_rate")),
            median_fwd_return=_dec(payload.get("median_fwd_return")),
            mean_r_after_cost=_dec(payload.get("mean_r_after_cost")),
            reason=str(payload.get("reason") or ""),
            cites_candidate=str(payload.get("cites_candidate") or ""),
            survivorship_tag=str(payload.get("survivorship_tag") or "survivorship_uncontrolled"),
            fixture_id=None if payload.get("fixture_id") is None else str(payload.get("fixture_id")),
            payload_json=dict(payload),
        )
        session.add(row)
        ids.append(row.id)
    session.flush()
    return ids


def rows_visible_at(session: Session, watermark: str) -> list[EventBaseRate]:
    """what_did_we_know-style: as_of_knowledge <= T."""
    cut = as_utc(parse_utc(watermark))
    return list(
        session.scalars(
            select(EventBaseRate)
            .where(EventBaseRate.as_of_knowledge <= cut)
            .order_by(EventBaseRate.as_of_knowledge, EventBaseRate.event_class)
        )
    )
