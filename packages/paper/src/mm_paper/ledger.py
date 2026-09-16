"""Open / close shadow paper trades bound to theses. No live orders."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from mm_common.enums import PaperTradeStatus, SkepticVerdict, ThesisStatus
from mm_common.ids import new_ulid
from mm_common.time import utcnow
from mm_paper.artifacts import list_paper_artifacts, write_paper_artifacts
from mm_paper.errors import LIVE_NOT_ALLOWED, MISSING_EXIT_REASON, PaperError, PaperGateError
from mm_paper.gates import require_open_fields
from mm_paper.models import FillRecord, MarkRecord, PaperTradeRecord, compute_slippage_bps
from mm_research_kit.artifacts import artifact_content_hash
from mm_research_kit.errors import GateError
from mm_research_kit.lifecycle import advance_status, read_status, recorded_skeptic_verdict
from mm_research_kit.workspace import find_workspace


def open_paper_trade(
    *,
    research_root: Path,
    templates_root: Path,
    repo_root: Path,
    slug: str,
    size: str,
    max_loss: str,
    invalidation: str,
    instrument: str = "BTC",
    side: str = "long",
    expected_path: list[str] | None = None,
    notes: str = "",
    fill_price: str | None = None,
    mark_price: str | None = None,
    opened_at: datetime | None = None,
    thesis_id: str | None = None,
) -> PaperTradeRecord:
    """Open a paper trade. Refuses without invalidation + max loss. No live path."""
    if side.lower() in {"live"}:
        raise PaperGateError(LIVE_NOT_ALLOWED)
    workspace = find_workspace(research_root, slug)
    invalidation_text, max_loss_text, max_loss_amount = require_open_fields(
        invalidation=invalidation,
        max_loss=max_loss,
    )
    if not size.strip():
        raise PaperGateError("paper trade cannot open without size")

    verdict = recorded_skeptic_verdict(workspace)
    if verdict != SkepticVerdict.PASS.value:
        raise PaperGateError("cannot open paper without a skeptic pass")

    opened = opened_at or utcnow()
    fills: list[FillRecord] = []
    marks: list[MarkRecord] = []
    slippage: Decimal | None = None
    if fill_price:
        fills.append(
            FillRecord(
                as_of=opened,
                side="buy" if side.lower() in {"buy", "long"} else "sell",
                qty=size.strip(),
                price=fill_price.strip(),
                mark=mark_price.strip() if mark_price else None,
                note="entry",
            )
        )
    if mark_price:
        marks.append(MarkRecord(as_of=opened, price=mark_price.strip(), note="entry mark"))
    if fill_price and mark_price:
        slippage = compute_slippage_bps(
            fill_price=Decimal(fill_price),
            mark_price=Decimal(mark_price),
            side=side,
        )

    record = PaperTradeRecord(
        id=new_ulid(),
        thesis_slug=workspace.name,
        thesis_id=thesis_id,
        instrument=instrument.strip() or "BTC",
        size=size.strip(),
        side=side.strip() or "long",
        invalidation=invalidation_text,
        max_loss=max_loss_text,
        max_loss_amount=max_loss_amount,
        opened_at=opened,
        expected_path=[item.strip() for item in (expected_path or []) if item.strip()],
        fills=fills,
        marks=marks,
        slippage_bps=slippage,
        notes=notes.strip(),
        entry_thesis_snapshot_hash=artifact_content_hash(workspace),
    )
    record = write_paper_artifacts(workspace, record, templates_root=templates_root, repo_root=repo_root)

    current = read_status(workspace)
    if current != ThesisStatus.PAPER.value:
        try:
            advance_status(workspace, ThesisStatus.PAPER.value)
        except GateError as exc:
            raise PaperGateError(str(exc)) from exc
    return record


def close_paper_trade(
    *,
    research_root: Path,
    templates_root: Path,
    repo_root: Path,
    slug: str,
    trade_id: str | None = None,
    exit_reason: str,
    pnl: str | None = None,
    slippage_bps: str | None = None,
    fill_price: str | None = None,
    mark_price: str | None = None,
    notes: str = "",
    closed_at: datetime | None = None,
) -> PaperTradeRecord:
    if not (exit_reason or "").strip():
        raise PaperGateError(MISSING_EXIT_REASON)
    workspace = find_workspace(research_root, slug)
    rows = list_paper_artifacts(workspace)
    if not rows:
        raise PaperError(f"no paper trades in {workspace}")
    chosen: dict | None = None
    if trade_id:
        for row in rows:
            if row.get("id") == trade_id:
                chosen = row
                break
        if chosen is None:
            raise PaperError(f"unknown paper trade id: {trade_id}")
    else:
        open_rows = [row for row in rows if row.get("status") == PaperTradeStatus.OPEN.value]
        if len(open_rows) != 1:
            raise PaperError("pass --id when there is not exactly one open paper trade")
        chosen = open_rows[0]

    record = PaperTradeRecord.model_validate(chosen)
    if record.status == PaperTradeStatus.CLOSED.value:
        raise PaperError(f"paper trade {record.id} is already closed")
    closed = closed_at or utcnow()
    record.closed_at = closed
    record.status = PaperTradeStatus.CLOSED.value
    record.exit_reason = exit_reason.strip()
    if notes.strip():
        record.notes = (record.notes + "\n" + notes.strip()).strip()
    if pnl is not None and pnl.strip():
        try:
            record.pnl = Decimal(pnl.strip())
        except InvalidOperation as exc:
            raise PaperError(f"invalid pnl {pnl!r}") from exc
    if slippage_bps is not None and slippage_bps.strip():
        record.slippage_bps = Decimal(slippage_bps.strip())
    if fill_price:
        record.fills = list(record.fills) + [
            FillRecord(
                as_of=closed,
                side="sell" if record.side.lower() in {"buy", "long"} else "buy",
                qty=record.size,
                price=fill_price.strip(),
                mark=mark_price.strip() if mark_price else None,
                note="exit",
            )
        ]
    if mark_price:
        record.marks = list(record.marks) + [MarkRecord(as_of=closed, price=mark_price.strip(), note="exit mark")]
        if fill_price and record.slippage_bps is None:
            record.slippage_bps = compute_slippage_bps(
                fill_price=Decimal(fill_price),
                mark_price=Decimal(mark_price),
                side="sell" if record.side.lower() in {"buy", "long"} else "buy",
            )
    record.realised_path = list(record.realised_path) + [f"exit:{record.exit_reason}@{closed.isoformat()}"]
    return write_paper_artifacts(workspace, record, templates_root=templates_root, repo_root=repo_root)
