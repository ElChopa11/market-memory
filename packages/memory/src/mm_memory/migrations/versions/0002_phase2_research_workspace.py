"""Phase 2 research workspace indexes.

Revision ID: 0002_phase2
Revises: 0001_phase1
Create Date: 2026-09-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase2"
down_revision: Union[str, None] = "0001_phase1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "thesis",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("author_role", sa.Text(), nullable=False, server_default="Research"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("artifact_git_path", sa.Text(), nullable=False),
        sa.Column("artifact_content_hash", sa.String(length=64), nullable=False),
        sa.Column("instrument", sa.Text(), nullable=True),
        sa.Column("horizon", sa.Text(), nullable=True),
        sa.Column("invalidation_summary", sa.Text(), nullable=True),
        sa.Column("risk_budget_bps", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "status IN ('draft','in_research','in_skeptic','paper','live','rejected','retired')",
            name="thesis_status_check",
        ),
        sa.UniqueConstraint("slug", name="thesis_slug_key"),
    )
    op.create_index("thesis_status_idx", "thesis", ["status"])

    op.create_table(
        "thesis_evidence",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("thesis_id", sa.String(length=26), sa.ForeignKey("thesis.id"), nullable=False),
        sa.Column("observation_id", sa.String(length=26), sa.ForeignKey("observation.id"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "role IN ('supports','opposes','context')",
            name="thesis_evidence_role_check",
        ),
        sa.UniqueConstraint("thesis_id", "observation_id", "role", name="thesis_evidence_unique"),
    )
    op.create_index("thesis_evidence_thesis_id_idx", "thesis_evidence", ["thesis_id"])
    op.create_index("thesis_evidence_observation_id_idx", "thesis_evidence", ["observation_id"])

    op.create_table(
        "skeptic_review",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("thesis_id", sa.String(length=26), sa.ForeignKey("thesis.id"), nullable=False),
        sa.Column("reviewer_id_or_role", sa.Text(), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=False),
        sa.Column(
            "findings_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("artifact_git_path", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "verdict IN ('pass','revise','reject')",
            name="skeptic_review_verdict_check",
        ),
    )
    op.create_index("skeptic_review_thesis_id_idx", "skeptic_review", ["thesis_id"])


def downgrade() -> None:
    op.drop_index("skeptic_review_thesis_id_idx", table_name="skeptic_review")
    op.drop_table("skeptic_review")
    op.drop_index("thesis_evidence_observation_id_idx", table_name="thesis_evidence")
    op.drop_index("thesis_evidence_thesis_id_idx", table_name="thesis_evidence")
    op.drop_table("thesis_evidence")
    op.drop_index("thesis_status_idx", table_name="thesis")
    op.drop_table("thesis")
