"""Phase 6d Alembic: listing_outcome cohort history for own-history base rates.

Revision ID: 0009_phase6d_listings
Revises: 0008_phase6c_delivery
Create Date: 2026-09-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0009_phase6d_listings"
down_revision: Union[str, None] = "0008_phase6c_delivery"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "listing_outcome",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("instrument", sa.Text(), nullable=False),
        sa.Column("listing_date", sa.String(length=10), nullable=False),
        sa.Column("as_of_knowledge", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("offer_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("ret_30d", sa.Numeric(16, 8), nullable=True),
        sa.Column("ret_90d", sa.Numeric(16, 8), nullable=True),
        sa.Column("reclaimed_offer", sa.Boolean(), nullable=True),
        sa.Column("reclaimed_day1_vwap", sa.Boolean(), nullable=True),
        sa.Column("observation_id", sa.Text(), nullable=True),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "as_of_knowledge = ingested_at",
            name="listing_outcome_as_of_knowledge_eq_ingested_at",
        ),
    )
    op.create_index("listing_outcome_as_of_idx", "listing_outcome", ["as_of_knowledge"])
    op.create_index("listing_outcome_instrument_idx", "listing_outcome", ["instrument"])


def downgrade() -> None:
    op.drop_index("listing_outcome_instrument_idx", table_name="listing_outcome")
    op.drop_index("listing_outcome_as_of_idx", table_name="listing_outcome")
    op.drop_table("listing_outcome")
