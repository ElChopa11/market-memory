"""One schedule_heartbeat row per run_id. Early is its own status.

Revision ID: 0013_completion_per_run
Revises: 0012_heartbeat_if_not_exists
Create Date: 2026-09-25

Disk completions are the Actions evidence store. This table is the optional
DB copy. The previous unique key was (routine_id, scheduled_anchor_ts), so a
second trigger replaced the first row. The key is now
(routine_id, scheduled_anchor_ts, run_id). ``early`` is allowed so a fire
before the anchor is not stored as ``late`` and is not rejected by the check.

Idempotent: DROP CONSTRAINT IF EXISTS, CREATE UNIQUE INDEX IF NOT EXISTS.
Alembic version_num is varchar(32).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0013_completion_per_run"
down_revision: Union[str, None] = "0012_heartbeat_if_not_exists"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "schedule_heartbeat"
STATUS_CHECK = "schedule_heartbeat_status_check"
OLD_ANCHOR_UNIQUE = "schedule_heartbeat_routine_anchor_uidx"
RUN_UNIQUE = "schedule_heartbeat_routine_anchor_run_uidx"
NEW_STATUSES = "('ok','early','late','missed','skipped','wrong_anchor')"
OLD_STATUSES = "('ok','late','missed','skipped','wrong_anchor')"


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(text(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {OLD_ANCHOR_UNIQUE}"))
    bind.execute(
        text(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {RUN_UNIQUE} "
            f"ON {TABLE} (routine_id, scheduled_anchor_ts, run_id)"
        )
    )
    bind.execute(text(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {STATUS_CHECK}"))
    bind.execute(text(f"ALTER TABLE {TABLE} ADD CONSTRAINT {STATUS_CHECK} CHECK (status IN {NEW_STATUSES})"))


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(text(f"DROP INDEX IF EXISTS {RUN_UNIQUE}"))
    bind.execute(text(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {STATUS_CHECK}"))
    bind.execute(text(f"ALTER TABLE {TABLE} ADD CONSTRAINT {STATUS_CHECK} CHECK (status IN {OLD_STATUSES})"))
    bind.execute(
        text(
            f"ALTER TABLE {TABLE} ADD CONSTRAINT {OLD_ANCHOR_UNIQUE} "
            f"UNIQUE (routine_id, scheduled_anchor_ts)"
        )
    )
