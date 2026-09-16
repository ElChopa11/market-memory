"""Phase 3 Market Pulse brief index.

Revision ID: 0003_phase3
Revises: 0002_phase2
Create Date: 2026-09-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_phase3"
down_revision: Union[str, None] = "0002_phase2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BRIEF_KINDS = ("preopen", "close", "alert")
DATA_QUALITY = ("ok", "stale", "partial", "contradicted", "rejected")


def upgrade() -> None:
    op.create_table(
        "brief",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("as_of_knowledge", sa.DateTime(timezone=True), nullable=False),
        sa.Column("artifact_git_path", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("data_quality", sa.String(length=32), nullable=False),
        sa.Column(
            "payload_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "kind IN ('" + "','".join(BRIEF_KINDS) + "')",
            name="brief_kind_check",
        ),
        sa.CheckConstraint(
            "data_quality IN ('" + "','".join(DATA_QUALITY) + "')",
            name="brief_data_quality_check",
        ),
        sa.UniqueConstraint("kind", "session_date", "content_hash", name="brief_kind_session_hash_uidx"),
    )
    op.create_index("brief_session_date_idx", "brief", ["session_date"])
    op.create_index("brief_kind_idx", "brief", ["kind"])


def downgrade() -> None:
    op.drop_index("brief_kind_idx", table_name="brief")
    op.drop_index("brief_session_date_idx", table_name="brief")
    op.drop_table("brief")
