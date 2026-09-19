"""IMP-039 Alembic: event_base_rate unconditional class snapshots.

Revision ID: 0010_unconditional_base_rates
Revises: 0009_phase6d_listings
Create Date: 2026-09-19
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0010_unconditional_base_rates"
down_revision: Union[str, None] = "0009_phase6d_listings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_base_rate",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("event_class", sa.String(length=32), nullable=False),
        sa.Column("as_of_knowledge", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("params_hash", sa.String(length=64), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("instrument_set", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("window_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("cost_model_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("n", sa.Integer(), nullable=False),
        sa.Column("n_min", sa.Integer(), nullable=False),
        sa.Column("claimed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hit_rate", sa.Numeric(16, 8), nullable=True),
        sa.Column("median_fwd_return", sa.Numeric(16, 8), nullable=True),
        sa.Column("mean_r_after_cost", sa.Numeric(16, 8), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("cites_candidate", sa.String(length=16), nullable=False),
        sa.Column("survivorship_tag", sa.Text(), nullable=False),
        sa.Column("fixture_id", sa.Text(), nullable=True),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "as_of_knowledge = ingested_at",
            name="event_base_rate_as_of_knowledge_eq_ingested_at",
        ),
        sa.CheckConstraint(
            "event_class IN ('dip_touch','zone_boundary_touch','pullback_ema_touch')",
            name="event_base_rate_event_class_check",
        ),
        sa.UniqueConstraint(
            "event_class",
            "params_hash",
            "as_of_knowledge",
            name="event_base_rate_class_params_as_of_uidx",
        ),
    )
    op.create_index("event_base_rate_as_of_idx", "event_base_rate", ["as_of_knowledge"])
    op.create_index("event_base_rate_params_idx", "event_base_rate", ["params_hash"])


def downgrade() -> None:
    op.drop_index("event_base_rate_params_idx", table_name="event_base_rate")
    op.drop_index("event_base_rate_as_of_idx", table_name="event_base_rate")
    op.drop_table("event_base_rate")
