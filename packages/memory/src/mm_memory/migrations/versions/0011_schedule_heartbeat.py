"""IMP-042 Alembic: schedule_heartbeat (log). Miss sweep is the control.

Revision ID: 0011_schedule_heartbeat
Revises: 0010_unconditional_base_rates
Create Date: 2026-09-19

Safe/idempotent: CREATE TABLE / indexes are skipped when already present so a
box that stamped this revision (or retried after a partial apply) does not fail.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0011_schedule_heartbeat"
down_revision: Union[str, None] = "0010_unconditional_base_rates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "schedule_heartbeat"


def _index_names(inspector, table: str) -> set[str]:
    return {idx["name"] for idx in inspector.get_indexes(table) if idx.get("name")}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table(TABLE):
        op.create_table(
            TABLE,
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
        inspector = inspect(bind)
    existing = _index_names(inspector, TABLE)
    if "schedule_heartbeat_as_of_idx" not in existing:
        op.create_index("schedule_heartbeat_as_of_idx", TABLE, ["as_of_knowledge"])
    if "schedule_heartbeat_routine_idx" not in existing:
        op.create_index("schedule_heartbeat_routine_idx", TABLE, ["routine_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table(TABLE):
        return
    existing = _index_names(inspector, TABLE)
    if "schedule_heartbeat_routine_idx" in existing:
        op.drop_index("schedule_heartbeat_routine_idx", table_name=TABLE)
    if "schedule_heartbeat_as_of_idx" in existing:
        op.drop_index("schedule_heartbeat_as_of_idx", table_name=TABLE)
    op.drop_table(TABLE)
