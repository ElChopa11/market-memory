"""Source-health models. Health/provenance only — never market prints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

STATUS_OK = "ok"
STATUS_DEGRADED = "degraded"
STATUS_UNAVAILABLE = "unavailable"
STATUSES = (STATUS_OK, STATUS_DEGRADED, STATUS_UNAVAILABLE)

PULSE_REQUIRED = "required"
PULSE_OPTIONAL = "optional"
PULSE_NA = "n/a"

# Always listed, even when the probe cannot reach the source.
SOURCE_INVENTORY: tuple[str, ...] = (
    "hyperliquid.info",
    "coingecko",
    "stooq",
    "fred",
    "calendar.yaml",
    "postgres",
    "object_store",
)

PULSE_ROLE: dict[str, str] = {
    "hyperliquid.info": PULSE_REQUIRED,
    "coingecko": PULSE_OPTIONAL,
    "stooq": PULSE_OPTIONAL,
    "fred": PULSE_OPTIONAL,
    "calendar.yaml": PULSE_REQUIRED,
    "postgres": PULSE_OPTIONAL,  # Pulse can run --no-db
    "object_store": PULSE_NA,
}

DISPLAY_NAME: dict[str, str] = {
    "hyperliquid.info": "hyperliquid.info /info",
    "coingecko": "coingecko",
    "stooq": "stooq",
    "fred": "fred",
    "calendar.yaml": "config/briefing/calendar.yaml",
    "postgres": "postgres",
    "object_store": "object_store",
}


@dataclass(frozen=True)
class SourceHealth:
    source_id: str
    display_name: str
    pulse_role: str
    status: str
    latency_ms: float | None
    error_class: str
    last_success_at: datetime | None
    credentials_present: str
    notes: tuple[str, ...]
    endpoint: str | None = None
    probe: str | None = None

    def as_public_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "display_name": self.display_name,
            "pulse_role": self.pulse_role,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "error_class": self.error_class,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "credentials_present": self.credentials_present,
            "notes": list(self.notes),
            "endpoint": self.endpoint,
            "probe": self.probe,
        }


@dataclass(frozen=True)
class HealthReport:
    generated_at: datetime
    overall: str
    sources: tuple[SourceHealth, ...]
    markdown: str
    content_hash: str
    limitations: tuple[str, ...]

    def source_ids(self) -> tuple[str, ...]:
        return tuple(row.source_id for row in self.sources)

    def by_id(self) -> dict[str, SourceHealth]:
        return {row.source_id: row for row in self.sources}

    def as_public_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "overall": self.overall,
            "content_hash": self.content_hash,
            "sources": [row.as_public_dict() for row in self.sources],
            "limitations": list(self.limitations),
        }


def overall_status(rows: tuple[SourceHealth, ...] | list[SourceHealth]) -> str:
    """Unavailable if any Pulse-required source is down; else degraded if any row is not ok."""
    worst = STATUS_OK
    for row in rows:
        if row.pulse_role == PULSE_REQUIRED and row.status == STATUS_UNAVAILABLE:
            return STATUS_UNAVAILABLE
        if row.status == STATUS_UNAVAILABLE:
            worst = STATUS_DEGRADED
        elif row.status == STATUS_DEGRADED and worst == STATUS_OK:
            worst = STATUS_DEGRADED
    return worst


def fallback_row(
    source_id: str,
    *,
    notes: tuple[str, ...],
    error_class: str = "internal_error",
    status: str = STATUS_UNAVAILABLE,
) -> SourceHealth:
    return SourceHealth(
        source_id=source_id,
        display_name=DISPLAY_NAME.get(source_id, source_id),
        pulse_role=PULSE_ROLE.get(source_id, PULSE_OPTIONAL),
        status=status,
        latency_ms=None,
        error_class=error_class,
        last_success_at=None,
        credentials_present="unknown",
        notes=notes,
    )
