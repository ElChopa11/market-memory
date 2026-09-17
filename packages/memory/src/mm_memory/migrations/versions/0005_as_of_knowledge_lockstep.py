"""Lock as_of_knowledge to ingested_at (sole PIT watermark).

Revision ID: 0005_knowledge_lockstep
Revises: 0004_phase4
Create Date: 2026-09-16
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0005_knowledge_lockstep"
down_revision: Union[str, None] = "0004_phase4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "observation_as_of_knowledge_eq_ingested_at",
        "observation",
        "as_of_knowledge = ingested_at",
    )
    op.create_index("observation_as_of_knowledge_idx", "observation", ["as_of_knowledge"])


def downgrade() -> None:
    op.drop_index("observation_as_of_knowledge_idx", table_name="observation")
    op.drop_constraint("observation_as_of_knowledge_eq_ingested_at", "observation", type_="check")
