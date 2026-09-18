"""Phase 6a Alembic: persist desk mesh envelopes + health (PG NOTIFY bus).

Revision ID: 0007_phase6a_desk_mesh
Revises: 0006_phase5a_status_events
Create Date: 2026-09-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0007_phase6a_desk_mesh"
down_revision: Union[str, None] = "0006_phase5a_status_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ERROR_CLASSES = ("desk_missing", "desk_killed", "desk_error", "desk_timeout")


def upgrade() -> None:
    op.create_table(
        "desk_envelope",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("desk", sa.String(length=32), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("as_of_knowledge", sa.DateTime(timezone=True), nullable=False),
        sa.Column("as_of_sydney", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("n", sa.Integer(), nullable=False),
        sa.Column("completeness_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("regime", sa.Text(), nullable=False, server_default="unset"),
        sa.Column("op", sa.String(length=32), nullable=False),
        sa.Column("universe", sa.Text(), nullable=False),
        sa.Column("sources", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("missing", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("cadence", sa.String(length=32), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("error_class", sa.Text(), nullable=True),
        sa.Column("body_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("alert_channel", sa.Text(), nullable=True),
        sa.Column("dq_channel", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('OK','DEGRADED','FAILED')", name="desk_envelope_status_check"),
        sa.CheckConstraint("op IN ('paper','observation')", name="desk_envelope_op_check"),
        sa.CheckConstraint(
            "error_class IS NULL OR error_class IN ('" + "','".join(ERROR_CLASSES) + "')",
            name="desk_envelope_error_class_check",
        ),
        sa.CheckConstraint(
            "completeness_pct >= 0 AND completeness_pct <= 100",
            name="desk_envelope_completeness_check",
        ),
        sa.UniqueConstraint("desk", "as_of_knowledge", "content_hash", name="desk_envelope_desk_as_of_hash_uidx"),
    )
    op.create_index("desk_envelope_desk_as_of_idx", "desk_envelope", ["desk", "as_of_knowledge"])
    op.create_index("desk_envelope_channel_idx", "desk_envelope", ["channel"])
    op.create_index("desk_envelope_as_of_idx", "desk_envelope", ["as_of_knowledge"])

    op.create_table(
        "desk_health",
        sa.Column("desk", sa.String(length=32), primary_key=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("last_as_of", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_envelope_id", sa.String(length=26), nullable=True),
        sa.Column("last_content_hash", sa.String(length=64), nullable=True),
        sa.Column("error_class", sa.Text(), nullable=True),
        sa.Column("n", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completeness_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("desk_health")
    op.drop_index("desk_envelope_as_of_idx", table_name="desk_envelope")
    op.drop_index("desk_envelope_channel_idx", table_name="desk_envelope")
    op.drop_index("desk_envelope_desk_as_of_idx", table_name="desk_envelope")
    op.drop_table("desk_envelope")
