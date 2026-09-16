"""Phase 4 research_run + paper_trade.

Revision ID: 0004_phase4
Revises: 0003_phase3
Create Date: 2026-09-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_phase4"
down_revision: Union[str, None] = "0003_phase3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RUN_KINDS = ("scan", "backtest", "manual")
PAPER_STATUSES = ("open", "closed")


def upgrade() -> None:
    op.create_table(
        "research_run",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("thesis_id", sa.String(length=26), sa.ForeignKey("thesis.id"), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("params_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "result_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "artifact_paths",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "kind IN ('" + "','".join(RUN_KINDS) + "')",
            name="research_run_kind_check",
        ),
    )
    op.create_index("research_run_thesis_id_idx", "research_run", ["thesis_id"])
    op.create_index("research_run_params_hash_idx", "research_run", ["params_hash"])
    op.create_index("research_run_kind_idx", "research_run", ["kind"])

    op.create_table(
        "paper_trade",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("thesis_id", sa.String(length=26), sa.ForeignKey("thesis.id"), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("instrument", sa.Text(), nullable=False),
        sa.Column("size", sa.Text(), nullable=False),
        sa.Column("invalidation", sa.Text(), nullable=False),
        sa.Column("max_loss", sa.Text(), nullable=False),
        sa.Column("max_loss_amount", sa.Numeric(20, 8), nullable=False),
        sa.Column(
            "intent_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "fills_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "expected_path",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "realised_path",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("pnl", sa.Numeric(20, 8), nullable=True),
        sa.Column("slippage_bps", sa.Numeric(12, 4), nullable=True),
        sa.Column("exit_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("artifact_git_path", sa.Text(), nullable=False),
        sa.Column("entry_thesis_snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('" + "','".join(PAPER_STATUSES) + "')",
            name="paper_trade_status_check",
        ),
        sa.CheckConstraint("length(btrim(invalidation)) > 0", name="paper_trade_invalidation_check"),
        sa.CheckConstraint("length(btrim(max_loss)) > 0", name="paper_trade_max_loss_check"),
        sa.CheckConstraint("max_loss_amount > 0", name="paper_trade_max_loss_amount_check"),
    )
    op.create_index("paper_trade_thesis_id_idx", "paper_trade", ["thesis_id"])
    op.create_index("paper_trade_status_idx", "paper_trade", ["status"])


def downgrade() -> None:
    op.drop_index("paper_trade_status_idx", table_name="paper_trade")
    op.drop_index("paper_trade_thesis_id_idx", table_name="paper_trade")
    op.drop_table("paper_trade")
    op.drop_index("research_run_kind_idx", table_name="research_run")
    op.drop_index("research_run_params_hash_idx", table_name="research_run")
    op.drop_index("research_run_thesis_id_idx", table_name="research_run")
    op.drop_table("research_run")
