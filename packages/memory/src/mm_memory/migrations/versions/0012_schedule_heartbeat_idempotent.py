"""Ensure schedule_heartbeat exists + allow wrong_anchor status.

Revision ID: 0012_schedule_heartbeat_idempotent
Revises: 0011_schedule_heartbeat
Create Date: 2026-09-20

Live boxes reported ProgrammingError: relation "schedule_heartbeat" does not
exist even after 0011 landed in git (migrate not applied, or revision stamped
without the table). This revision is safe to re-run: IF NOT EXISTS for table
and indexes; DROP/ADD for the status check.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect, text

revision: str = "0012_schedule_heartbeat_idempotent"
down_revision: Union[str, None] = "0011_schedule_heartbeat"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "schedule_heartbeat"
STATUS_CHECK = "schedule_heartbeat_status_check"
NEW_STATUSES = "('ok','late','missed','skipped','wrong_anchor')"
OLD_STATUSES = "('ok','late','missed','skipped')"


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE} (
                id VARCHAR(26) PRIMARY KEY,
                routine_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                scheduled_anchor_ts TIMESTAMPTZ NOT NULL,
                fired_at_ts TIMESTAMPTZ,
                delta_seconds INTEGER,
                status VARCHAR(16) NOT NULL,
                as_of_knowledge TIMESTAMPTZ NOT NULL,
                source TEXT NOT NULL DEFAULT 'lab',
                payload_json JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                CONSTRAINT {STATUS_CHECK} CHECK (status IN {NEW_STATUSES}),
                CONSTRAINT schedule_heartbeat_routine_anchor_uidx UNIQUE (routine_id, scheduled_anchor_ts)
            )
            """
        )
    )
    bind.execute(text(f"CREATE INDEX IF NOT EXISTS schedule_heartbeat_as_of_idx ON {TABLE} (as_of_knowledge)"))
    bind.execute(text(f"CREATE INDEX IF NOT EXISTS schedule_heartbeat_routine_idx ON {TABLE} (routine_id)"))
    # Table may already exist from 0011 with the narrower CHECK. Replace it.
    bind.execute(text(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {STATUS_CHECK}"))
    bind.execute(
        text(f"ALTER TABLE {TABLE} ADD CONSTRAINT {STATUS_CHECK} CHECK (status IN {NEW_STATUSES})")
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table(TABLE):
        return
    bind.execute(text(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {STATUS_CHECK}"))
    bind.execute(
        text(f"ALTER TABLE {TABLE} ADD CONSTRAINT {STATUS_CHECK} CHECK (status IN {OLD_STATUSES})")
    )
