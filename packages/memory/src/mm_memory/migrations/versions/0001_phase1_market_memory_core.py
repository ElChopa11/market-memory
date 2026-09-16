"""Phase 1 Market Memory core tables.

Revision ID: 0001_phase1
Revises:
Create Date: 2026-09-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_phase1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("trust_tier", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("tos_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "kind IN ('exchange','onchain','macro','news','internal')",
            name="source_kind_check",
        ),
        sa.UniqueConstraint("name", name="source_name_key"),
    )

    op.create_table(
        "raw_object",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("bucket", sa.Text(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=True),
        sa.Column("byte_size", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("bucket", "object_key", name="raw_object_bucket_key_uidx"),
    )

    op.create_table(
        "observation",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("source_id", sa.String(length=26), sa.ForeignKey("source.id"), nullable=False),
        sa.Column("source_url_or_id", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("market_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("claim_hash", sa.String(length=64), nullable=False),
        sa.Column("identity_hash", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("evidence_type", sa.String(length=32), nullable=False),
        sa.Column("data_quality", sa.String(length=32), nullable=False, server_default="ok"),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("raw_object_key", sa.Text(), nullable=True),
        sa.Column("raw_object_checksum", sa.String(length=64), nullable=True),
        sa.Column("as_of_knowledge", sa.DateTime(timezone=True), nullable=False),
        sa.Column("instrument", sa.Text(), nullable=False),
        sa.Column("metric", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "evidence_type IN ('fact','quote','metric','commentary','derived')",
            name="observation_evidence_type_check",
        ),
        sa.CheckConstraint(
            "data_quality IN ('ok','stale','partial','contradicted','rejected')",
            name="observation_data_quality_check",
        ),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="observation_confidence_check"),
        sa.UniqueConstraint("claim_hash", name="observation_claim_hash_uidx"),
    )
    op.create_index("observation_ingested_at_idx", "observation", ["ingested_at"])
    op.create_index("observation_market_time_idx", "observation", ["market_time"])
    op.create_index("observation_source_id_idx", "observation", ["source_id"])
    op.create_index("observation_identity_hash_idx", "observation", ["identity_hash"])
    op.create_index("observation_identity_idx", "observation", ["source_id", "instrument", "metric", "market_time"])

    op.create_table(
        "observation_link",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("observation_id", sa.String(length=26), sa.ForeignKey("observation.id"), nullable=False),
        sa.Column(
            "related_observation_id",
            sa.String(length=26),
            sa.ForeignKey("observation.id"),
            nullable=False,
        ),
        sa.Column("relation", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "relation IN ('supports','contradicts','duplicate','updates')",
            name="observation_link_relation_check",
        ),
        sa.CheckConstraint("observation_id <> related_observation_id", name="observation_link_no_self"),
        sa.UniqueConstraint(
            "observation_id",
            "related_observation_id",
            "relation",
            name="observation_link_unique",
        ),
    )
    op.create_index("observation_link_observation_id_idx", "observation_link", ["observation_id"])
    op.create_index("observation_link_related_idx", "observation_link", ["related_observation_id"])


def downgrade() -> None:
    op.drop_index("observation_link_related_idx", table_name="observation_link")
    op.drop_index("observation_link_observation_id_idx", table_name="observation_link")
    op.drop_table("observation_link")
    op.drop_index("observation_identity_idx", table_name="observation")
    op.drop_index("observation_identity_hash_idx", table_name="observation")
    op.drop_index("observation_source_id_idx", table_name="observation")
    op.drop_index("observation_market_time_idx", table_name="observation")
    op.drop_index("observation_ingested_at_idx", table_name="observation")
    op.drop_table("observation")
    op.drop_table("raw_object")
    op.drop_table("source")
