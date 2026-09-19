"""IMP-042 Alembic: schedule_heartbeat (log). Miss sweep is the control.

Revision ID: 0011_schedule_heartbeat
Revises: 0010_unconditional_base_rates
Create Date: 2026-09-19
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0011_schedule_heartbeat"
down_revision: Union[str, None] = "0010_unconditional_base_rates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "schedule_heartbeat",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("routine_id", sa.Text(), nullable=False),
        sa.Column("run_id", sa.Text(), nullable=False),
        sa.Column("scheduled_anchor_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fired_at_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delta_seconds", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("as_of_knowledge", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.Text(), nullable=False, server_default=sa.text("'lab'")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('ok','late','missed','skipped')",
            name="schedule_heartbeat_status_check",
        ),
        sa.UniqueConstraint(
            "routine_id",
            "scheduled_anchor_ts",
            name="schedule_heartbeat_routine_anchor_uidx",
        ),
    )
    op.create_index(
        "schedule_heartbeat_as_of_idx",
        "schedule_heartbeat",
        ["as_of_knowledge"],
    )
    op.create_index(
        "schedule_heartbeat_routine_idx",
        "schedule_heartbeat",
        ["routine_id"],
    )


def downgrade() -> None:
    op.drop_index("schedule_heartbeat_routine_idx", table_name="schedule_heartbeat")
    op.drop_index("schedule_heartbeat_as_of_idx", table_name="schedule_heartbeat")
    op.drop_table("schedule_heartbeat")
