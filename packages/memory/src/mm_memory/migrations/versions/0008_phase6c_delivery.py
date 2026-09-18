"""Phase 6c Alembic: delivery FAILED rows, inbound audit, LLM call ledger.

Revision ID: 0008_phase6c_delivery
Revises: 0007_phase6a_desk_mesh
Create Date: 2026-09-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0008_phase6c_delivery"
down_revision: Union[str, None] = "0007_phase6a_desk_mesh"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "delivery_event",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("desk", sa.String(length=64), nullable=False),
        sa.Column("as_of_knowledge", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("notes_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('DRY_RUN','SENT','FAILED','DEDUPE')", name="delivery_event_status_check"),
    )
    op.create_index("delivery_event_desk_as_of_idx", "delivery_event", ["desk", "as_of_knowledge"])
    op.create_index("delivery_event_content_hash_idx", "delivery_event", ["content_hash"])

    op.create_table(
        "inbound_audit",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("uid", sa.Text(), nullable=False),
        sa.Column("command", sa.Text(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("inbound_audit_uid_idx", "inbound_audit", ["uid"])

    op.create_table(
        "llm_call",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("desk_slug", sa.String(length=32), nullable=False),
        sa.Column("artifact_type", sa.String(length=32), nullable=False),
        sa.Column("prompt_file", sa.Text(), nullable=False),
        sa.Column("prompt_hash", sa.String(length=64), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("model_version", sa.Text(), nullable=False),
        sa.Column("temperature", sa.Numeric(4, 3), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cached_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("cost", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("schema_valid", sa.Boolean(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("llm_call_run_id_idx", "llm_call", ["run_id"])
    op.create_index("llm_call_desk_idx", "llm_call", ["desk_slug"])


def downgrade() -> None:
    op.drop_index("llm_call_desk_idx", table_name="llm_call")
    op.drop_index("llm_call_run_id_idx", table_name="llm_call")
    op.drop_table("llm_call")
    op.drop_index("inbound_audit_uid_idx", table_name="inbound_audit")
    op.drop_table("inbound_audit")
    op.drop_index("delivery_event_content_hash_idx", table_name="delivery_event")
    op.drop_index("delivery_event_desk_as_of_idx", table_name="delivery_event")
    op.drop_table("delivery_event")
