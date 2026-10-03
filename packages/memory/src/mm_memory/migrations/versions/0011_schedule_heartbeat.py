"""IMP-042 Alembic: schedule_heartbeat (log). Miss sweep is the control.

Revision ID: 0011_schedule_heartbeat
Revises: 0010_unconditional_base_rates
Create Date: 2026-09-19

Safe/idempotent: CREATE TABLE / indexes use IF NOT EXISTS so a retry after a
partial apply does not fail. The statements are raw SQL so ``lab migrate --sql``
can render them with no database connection (inspect() cannot).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_schedule_heartbeat"
down_revision: Union[str, None] = "0010_unconditional_base_rates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Raw IF NOT EXISTS, not inspect(bind). Alembic offline mode
    # (``lab migrate --sql``) uses a MockConnection; inspect() raises
    # NoInspectionAvailable and was the first failure of a dry plan
    # (2026-09-23). Schema matches the previous create_table body.
    # 0012 widens the status CHECK to include wrong_anchor.
    op.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS schedule_heartbeat (
                id VARCHAR(26) PRIMARY KEY,
                routine_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                scheduled_anchor_ts TIMESTAMPTZ NOT NULL,
                fired_at_ts TIMESTAMPTZ,
                delta_seconds INTEGER,
                status VARCHAR(16) NOT NULL,
                as_of_knowledge TIMESTAMPTZ NOT NULL,
                source TEXT NOT NULL DEFAULT 'lab',
                payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                CONSTRAINT schedule_heartbeat_status_check CHECK (
                    status IN ('ok','late','missed','skipped')
                ),
                CONSTRAINT schedule_heartbeat_routine_anchor_uidx
                    UNIQUE (routine_id, scheduled_anchor_ts)
            )
            """
        )
    )
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS schedule_heartbeat_as_of_idx ON schedule_heartbeat (as_of_knowledge)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS schedule_heartbeat_routine_idx ON schedule_heartbeat (routine_id)"))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS schedule_heartbeat"))
