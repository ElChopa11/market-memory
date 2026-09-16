"""Persist paper_trade ledger rows. Git artifacts remain the human-review source."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from mm_common.enums import PaperTradeStatus
from mm_memory.models import PaperTrade, Thesis


class PaperRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, trade_id: str) -> PaperTrade | None:
        return self.session.get(PaperTrade, trade_id)

    def insert(
        self,
        *,
        trade_id: str,
        thesis_id: str,
        opened_at: datetime,
        instrument: str,
        size: str,
        invalidation: str,
        max_loss: str,
        max_loss_amount: Decimal,
        intent_json: dict[str, Any],
        fills_json: list[Any],
        expected_path: list[Any],
        artifact_git_path: str,
        entry_thesis_snapshot_hash: str,
        slippage_bps: Decimal | None = None,
        notes: str | None = None,
        status: str = PaperTradeStatus.OPEN.value,
    ) -> PaperTrade:
        if self.session.get(Thesis, thesis_id) is None:
            raise ValueError(f"unknown thesis id: {thesis_id}")
        row = PaperTrade(
            id=trade_id,
            thesis_id=thesis_id,
            opened_at=opened_at,
            status=status,
            instrument=instrument,
            size=size,
            invalidation=invalidation,
            max_loss=max_loss,
            max_loss_amount=max_loss_amount,
            intent_json=intent_json,
            fills_json=fills_json,
            expected_path=expected_path,
            realised_path=[],
            slippage_bps=slippage_bps,
            notes=notes,
            artifact_git_path=artifact_git_path,
            entry_thesis_snapshot_hash=entry_thesis_snapshot_hash,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def close(
        self,
        trade_id: str,
        *,
        closed_at: datetime,
        exit_reason: str,
        fills_json: list[Any] | None = None,
        realised_path: list[Any] | None = None,
        pnl: Decimal | None = None,
        slippage_bps: Decimal | None = None,
        notes: str | None = None,
    ) -> PaperTrade:
        row = self.get(trade_id)
        if row is None:
            raise ValueError(f"unknown paper trade id: {trade_id}")
        row.closed_at = closed_at
        row.status = PaperTradeStatus.CLOSED.value
        row.exit_reason = exit_reason
        if fills_json is not None:
            row.fills_json = fills_json
        if realised_path is not None:
            row.realised_path = realised_path
        if pnl is not None:
            row.pnl = pnl
        if slippage_bps is not None:
            row.slippage_bps = slippage_bps
        if notes is not None:
            row.notes = notes
        self.session.flush()
        return row

    def list_trades(
        self,
        *,
        thesis_id: str | None = None,
        status: str | None = None,
    ) -> list[PaperTrade]:
        stmt = select(PaperTrade).order_by(PaperTrade.opened_at.asc(), PaperTrade.id.asc())
        if thesis_id is not None:
            stmt = stmt.where(PaperTrade.thesis_id == thesis_id)
        if status is not None:
            stmt = stmt.where(PaperTrade.status == status)
        return list(self.session.scalars(stmt).all())
