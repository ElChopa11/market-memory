"""Phase 5a thesis status transition log (actor, ts, reason).

Revision ID: 0006_phase5a_status_events
Revises: 0005_knowledge_lockstep
Create Date: 2026-09-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_phase5a_status_events"
down_revision: Union[str, None] = "0005_knowledge_lockstep"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUSES = ("draft", "in_research", "in_skeptic", "paper", "live", "rejected", "retired")
RISK_DECISIONS = ("pending", "allow", "block")


def upgrade() -> None:
    op.create_table(
        "thesis_status_event",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("thesis_id", sa.String(length=26), sa.ForeignKey("thesis.id"), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=False),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("risk_decision", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("principal_override", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "from_status IN ('" + "','".join(STATUSES) + "')",
            name="thesis_status_event_from_status_check",
        ),
        sa.CheckConstraint(
            "to_status IN ('" + "','".join(STATUSES) + "')",
            name="thesis_status_event_to_status_check",
        ),
        sa.CheckConstraint(
            "risk_decision IN ('" + "','".join(RISK_DECISIONS) + "')",
            name="thesis_status_event_risk_decision_check",
        ),
    )
    op.create_index("thesis_status_event_thesis_id_idx", "thesis_status_event", ["thesis_id"])
    op.create_index("thesis_status_event_ts_idx", "thesis_status_event", ["ts"])


def downgrade() -> None:
    op.drop_index("thesis_status_event_ts_idx", table_name="thesis_status_event")
    op.drop_index("thesis_status_event_thesis_id_idx", table_name="thesis_status_event")
    op.drop_table("thesis_status_event")
