"""Paper trade records (in-memory / artifact). Persistence lives in Market Memory."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mm_common.enums import PaperTradeStatus
from mm_common.time import as_utc
from mm_paper.gates import require_open_fields


class FillRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    as_of: datetime
    side: str
    qty: str
    price: str
    mark: str | None = None
    note: str = ""

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return as_utc(value)

    def canonical(self) -> dict[str, Any]:
        return {
            "as_of": self.as_of.isoformat(),
            "side": self.side,
            "qty": self.qty,
            "price": self.price,
            "mark": self.mark,
            "note": self.note,
        }


class MarkRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    as_of: datetime
    price: str
    note: str = ""

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return as_utc(value)

    def canonical(self) -> dict[str, Any]:
        return {"as_of": self.as_of.isoformat(), "price": self.price, "note": self.note}


class PaperTradeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    thesis_slug: str
    thesis_id: str | None = None
    instrument: str
    size: str
    side: str = "long"
    invalidation: str
    max_loss: str
    max_loss_amount: Decimal
    opened_at: datetime
    closed_at: datetime | None = None
    status: str = PaperTradeStatus.OPEN.value
    expected_path: list[str] = Field(default_factory=list)
    realised_path: list[str] = Field(default_factory=list)
    fills: list[FillRecord] = Field(default_factory=list)
    marks: list[MarkRecord] = Field(default_factory=list)
    pnl: Decimal | None = None
    slippage_bps: Decimal | None = None
    exit_reason: str | None = None
    notes: str = ""
    artifact_git_path: str = ""
    entry_thesis_snapshot_hash: str = ""

    @field_validator("opened_at", "closed_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        return as_utc(value) if value is not None else None

    def intent_json(self) -> dict[str, Any]:
        return {
            "thesis_slug": self.thesis_slug,
            "instrument": self.instrument,
            "size": self.size,
            "side": self.side,
            "invalidation": self.invalidation,
            "max_loss": self.max_loss,
            "max_loss_amount": format(self.max_loss_amount, "f"),
            "expected_path": list(self.expected_path),
            "entry_thesis_snapshot_hash": self.entry_thesis_snapshot_hash,
        }

    def canonical(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "thesis_slug": self.thesis_slug,
            "thesis_id": self.thesis_id,
            "instrument": self.instrument,
            "size": self.size,
            "side": self.side,
            "invalidation": self.invalidation,
            "max_loss": self.max_loss,
            "max_loss_amount": format(self.max_loss_amount, "f"),
            "opened_at": self.opened_at.isoformat(),
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "status": self.status,
            "expected_path": list(self.expected_path),
            "realised_path": list(self.realised_path),
            "fills": [fill.canonical() for fill in self.fills],
            "marks": [mark.canonical() for mark in self.marks],
            "pnl": format(self.pnl, "f") if self.pnl is not None else None,
            "slippage_bps": format(self.slippage_bps, "f") if self.slippage_bps is not None else None,
            "exit_reason": self.exit_reason,
            "notes": self.notes,
            "artifact_git_path": self.artifact_git_path,
            "entry_thesis_snapshot_hash": self.entry_thesis_snapshot_hash,
        }


def compute_slippage_bps(*, fill_price: Decimal, mark_price: Decimal, side: str) -> Decimal:
    if mark_price == 0:
        return Decimal("0")
    if side.lower() in {"buy", "long"}:
        return (fill_price - mark_price) / mark_price * Decimal("10000")
    return (mark_price - fill_price) / mark_price * Decimal("10000")


def validated_open_fields(*, invalidation: str, max_loss: str) -> tuple[str, str, Decimal]:
    return require_open_fields(invalidation=invalidation, max_loss=max_loss)
