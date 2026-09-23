# Schema at Alembic head `0012_heartbeat_if_not_exists`

Evidence for an empty Neon database after `uv run lab migrate`. Nothing here was applied. No DSN was read.

`alembic_head()` in `packages/memory/src/mm_memory/migrate.py` returns `0012_heartbeat_if_not_exists` (28 characters; `0012` states `version_num` is `varchar(32)`).

## How this was rendered

`lab migrate` on this branch has no `--sql` flag. `cmd_migrate` calls `upgrade_head`, which is Alembic `upgrade` to `head`.

Offline SQL for base → `0010_unconditional_base_rates` is in [2026-09-23-migrate-through-0010.sql](2026-09-23-migrate-through-0010.sql). It was produced with `alembic.command.upgrade(cfg, "0010_unconditional_base_rates", sql=True)`, which uses `run_migrations_offline` in `packages/memory/src/mm_memory/migrations/env.py`. `POSTGRES_DSN` was unset. The placeholder URL does not appear in the SQL. The file ends with `COMMIT;`.

`upgrade` to `0011_schedule_heartbeat` with `sql=True` prints `-- Running upgrade 0010_unconditional_base_rates -> 0011_schedule_heartbeat` and then raises `NoInspectionAvailable: No inspection system is available for object of type <class 'sqlalchemy.engine.mock.MockConnection'>`. That matches `0011`, which calls `inspect(bind)` before `op.create_table`. Head DDL below is quoted from the revision files, not invented as rendered SQL.

PR #105 (open, not merged) adds `lab migrate --sql-out` and rewrites `0011` and `0012`. That SQL is a different revision text. It is not copied here.

## Extensions

None. No revision file under `packages/memory/src/mm_memory/migrations/versions/` contains an extension statement. The offline SQL through `0010_unconditional_base_rates` contains no extension statement. `JSONB` in these revisions is the built-in Postgres type used by `sqlalchemy.dialects.postgresql.JSONB`.

## Revision ids (base → head)

Quoted from each file's `revision` / `down_revision`:

| Order | `revision` | `down_revision` | File |
|---|---|---|---|
| 1 | `0001_phase1` | `None` | `0001_phase1_market_memory_core.py` |
| 2 | `0002_phase2` | `0001_phase1` | `0002_phase2_research_workspace.py` |
| 3 | `0003_phase3` | `0002_phase2` | `0003_phase3_briefs.py` |
| 4 | `0004_phase4` | `0003_phase3` | `0004_phase4_backtest_paper.py` |
| 5 | `0005_knowledge_lockstep` | `0004_phase4` | `0005_as_of_knowledge_lockstep.py` |
| 6 | `0006_phase5a_status_events` | `0005_knowledge_lockstep` | `0006_phase5a_status_events.py` |
| 7 | `0007_phase6a_desk_mesh` | `0006_phase5a_status_events` | `0007_phase6a_desk_mesh.py` |
| 8 | `0008_phase6c_delivery` | `0007_phase6a_desk_mesh` | `0008_phase6c_delivery.py` |
| 9 | `0009_phase6d_listings` | `0008_phase6c_delivery` | `0009_phase6d_listings.py` |
| 10 | `0010_unconditional_base_rates` | `0009_phase6d_listings` | `0010_unconditional_base_rates.py` |
| 11 | `0011_schedule_heartbeat` | `0010_unconditional_base_rates` | `0011_schedule_heartbeat.py` |
| 12 | `0012_heartbeat_if_not_exists` | `0011_schedule_heartbeat` | `0012_heartbeat_if_not_exists.py` |

Source lines:

```python
revision: str = "0001_phase1"
down_revision: Union[str, None] = None
```

```python
revision: str = "0002_phase2"
down_revision: Union[str, None] = "0001_phase1"
```

```python
revision: str = "0003_phase3"
down_revision: Union[str, None] = "0002_phase2"
```

```python
revision: str = "0004_phase4"
down_revision: Union[str, None] = "0003_phase3"
```

```python
revision: str = "0005_knowledge_lockstep"
down_revision: Union[str, None] = "0004_phase4"
```

```python
revision: str = "0006_phase5a_status_events"
down_revision: Union[str, None] = "0005_knowledge_lockstep"
```

```python
revision: str = "0007_phase6a_desk_mesh"
down_revision: Union[str, None] = "0006_phase5a_status_events"
```

```python
revision: str = "0008_phase6c_delivery"
down_revision: Union[str, None] = "0007_phase6a_desk_mesh"
```

```python
revision: str = "0009_phase6d_listings"
down_revision: Union[str, None] = "0008_phase6c_delivery"
```

```python
revision: str = "0010_unconditional_base_rates"
down_revision: Union[str, None] = "0009_phase6d_listings"
```

```python
revision: str = "0011_schedule_heartbeat"
down_revision: Union[str, None] = "0010_unconditional_base_rates"
```

```python
revision: str = "0012_heartbeat_if_not_exists"
down_revision: Union[str, None] = "0011_schedule_heartbeat"
```

After a successful `lab migrate`, Alembic stamps `alembic_version.version_num` with `0012_heartbeat_if_not_exists`. The offline SQL creates that table as:

```sql
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
```

## Tables

Nineteen tables are created by the offline SQL (base → `0010_unconditional_base_rates`). `schedule_heartbeat` is created by `0011` / ensured by `0012`. Total at head: 20 tables.

| Table | First revision that creates it |
|---|---|
| `alembic_version` | Alembic bookkeeping, before `0001_phase1` (not a revision file) |
| `source` | `0001_phase1` |
| `raw_object` | `0001_phase1` |
| `observation` | `0001_phase1` |
| `observation_link` | `0001_phase1` |
| `thesis` | `0002_phase2` |
| `thesis_evidence` | `0002_phase2` |
| `skeptic_review` | `0002_phase2` |
| `brief` | `0003_phase3` |
| `research_run` | `0004_phase4` |
| `paper_trade` | `0004_phase4` |
| `thesis_status_event` | `0006_phase5a_status_events` |
| `desk_envelope` | `0007_phase6a_desk_mesh` |
| `desk_health` | `0007_phase6a_desk_mesh` |
| `delivery_event` | `0008_phase6c_delivery` |
| `inbound_audit` | `0008_phase6c_delivery` |
| `llm_call` | `0008_phase6c_delivery` |
| `listing_outcome` | `0009_phase6d_listings` |
| `event_base_rate` | `0010_unconditional_base_rates` |
| `schedule_heartbeat` | `0011_schedule_heartbeat` (`0012_heartbeat_if_not_exists` uses `CREATE TABLE IF NOT EXISTS`) |

`0005_knowledge_lockstep` creates no table. It adds a check and an index on `observation`:

```python
op.create_check_constraint(
    "observation_as_of_knowledge_eq_ingested_at",
    "observation",
    "as_of_knowledge = ingested_at",
)
op.create_index("observation_as_of_knowledge_idx", "observation", ["as_of_knowledge"])
```

Column lists for the first nineteen tables are the `CREATE TABLE` statements in the offline SQL file. They match the `op.create_table` calls in revisions `0001_phase1` through `0010_unconditional_base_rates`.

## Indexes

### Secondary indexes (`CREATE INDEX`) through `0010_unconditional_base_rates`

Quoted from the offline SQL, in revision order:

- `observation_ingested_at_idx` on `observation (ingested_at)`
- `observation_market_time_idx` on `observation (market_time)`
- `observation_source_id_idx` on `observation (source_id)`
- `observation_identity_hash_idx` on `observation (identity_hash)`
- `observation_identity_idx` on `observation (source_id, instrument, metric, market_time)`
- `observation_link_observation_id_idx` on `observation_link (observation_id)`
- `observation_link_related_idx` on `observation_link (related_observation_id)`
- `thesis_status_idx` on `thesis (status)`
- `thesis_evidence_thesis_id_idx` on `thesis_evidence (thesis_id)`
- `thesis_evidence_observation_id_idx` on `thesis_evidence (observation_id)`
- `skeptic_review_thesis_id_idx` on `skeptic_review (thesis_id)`
- `brief_session_date_idx` on `brief (session_date)`
- `brief_kind_idx` on `brief (kind)`
- `research_run_thesis_id_idx` on `research_run (thesis_id)`
- `research_run_params_hash_idx` on `research_run (params_hash)`
- `research_run_kind_idx` on `research_run (kind)`
- `paper_trade_thesis_id_idx` on `paper_trade (thesis_id)`
- `paper_trade_status_idx` on `paper_trade (status)`
- `observation_as_of_knowledge_idx` on `observation (as_of_knowledge)`
- `thesis_status_event_thesis_id_idx` on `thesis_status_event (thesis_id)`
- `thesis_status_event_ts_idx` on `thesis_status_event (ts)`
- `desk_envelope_desk_as_of_idx` on `desk_envelope (desk, as_of_knowledge)`
- `desk_envelope_channel_idx` on `desk_envelope (channel)`
- `desk_envelope_as_of_idx` on `desk_envelope (as_of_knowledge)`
- `delivery_event_desk_as_of_idx` on `delivery_event (desk, as_of_knowledge)`
- `delivery_event_content_hash_idx` on `delivery_event (content_hash)`
- `inbound_audit_uid_idx` on `inbound_audit (uid)`
- `llm_call_run_id_idx` on `llm_call (run_id)`
- `llm_call_desk_idx` on `llm_call (desk_slug)`
- `listing_outcome_as_of_idx` on `listing_outcome (as_of_knowledge)`
- `listing_outcome_instrument_idx` on `listing_outcome (instrument)`
- `event_base_rate_as_of_idx` on `event_base_rate (as_of_knowledge)`
- `event_base_rate_params_idx` on `event_base_rate (params_hash)`

### Unique constraints (unique indexes) through `0010_unconditional_base_rates`

Quoted from `CONSTRAINT <name> UNIQUE` in the offline SQL:

- `source_name_key`
- `raw_object_bucket_key_uidx`
- `observation_claim_hash_uidx`
- `observation_link_unique`
- `thesis_slug_key`
- `thesis_evidence_unique`
- `brief_kind_session_hash_uidx`
- `desk_envelope_desk_as_of_hash_uidx`
- `event_base_rate_class_params_as_of_uidx`

### Named primary-key constraint in the offline SQL

`alembic_version_pkc` on `alembic_version (version_num)`.

Other tables declare an inline `PRIMARY KEY` column in the `CREATE TABLE` statement (see the SQL file). Those constraint names are not spelled in the revision files, so they are not invented here.

### `schedule_heartbeat` indexes at head

From `0011_schedule_heartbeat.py`:

```python
op.create_index("schedule_heartbeat_as_of_idx", TABLE, ["as_of_knowledge"])
op.create_index("schedule_heartbeat_routine_idx", TABLE, ["routine_id"])
```

```python
sa.UniqueConstraint(
    "routine_id",
    "scheduled_anchor_ts",
    name="schedule_heartbeat_routine_anchor_uidx",
),
```

From `0012_heartbeat_if_not_exists.py` (same index names, `IF NOT EXISTS`):

```python
bind.execute(text(f"CREATE INDEX IF NOT EXISTS schedule_heartbeat_as_of_idx ON {TABLE} (as_of_knowledge)"))
bind.execute(text(f"CREATE INDEX IF NOT EXISTS schedule_heartbeat_routine_idx ON {TABLE} (routine_id)"))
```

## `schedule_heartbeat` on an empty database

`0011` on a database that does not already have the table (`inspector.has_table(TABLE)` is false) runs `op.create_table` and then both `op.create_index` calls. Quoted from `0011_schedule_heartbeat.py`:

```python
if not inspector.has_table(TABLE):
    op.create_table(
        TABLE,
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("routine_id", sa.Text(), nullable=False),
        sa.Column("run_id", sa.Text(), nullable=False),
        sa.Column("scheduled_anchor_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fired_at_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delta_seconds", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("as_of_knowledge", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.Text(), nullable=False, server_default=sa.text("'lab'")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('ok','late','missed','skipped')",
            name="schedule_heartbeat_status_check",
        ),
        sa.UniqueConstraint(
            "routine_id",
            "scheduled_anchor_ts",
            name="schedule_heartbeat_routine_anchor_uidx",
        ),
    )
```

`TABLE = "schedule_heartbeat"`.

`0012` then runs this SQL (`TABLE = "schedule_heartbeat"`, `STATUS_CHECK = "schedule_heartbeat_status_check"`, `NEW_STATUSES = "('ok','late','missed','skipped','wrong_anchor')"`). Quoted from `0012_heartbeat_if_not_exists.py`:

```python
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
bind.execute(text(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {STATUS_CHECK}"))
bind.execute(
    text(f"ALTER TABLE {TABLE} ADD CONSTRAINT {STATUS_CHECK} CHECK (status IN {NEW_STATUSES})")
)
```

When `0011` has already created `schedule_heartbeat`, `CREATE TABLE IF NOT EXISTS` does not replace the table. The following `CREATE INDEX IF NOT EXISTS` statements do not add a second copy of `schedule_heartbeat_as_of_idx` or `schedule_heartbeat_routine_idx`. The `ALTER TABLE` drops `schedule_heartbeat_status_check` and adds it again with `status IN ('ok','late','missed','skipped','wrong_anchor')`.

Objects present for this table after both revisions succeed:

- table `schedule_heartbeat`
- primary key on `id` (`primary_key=True` in `0011`; `id VARCHAR(26) PRIMARY KEY` in the `0012` statement)
- unique constraint `schedule_heartbeat_routine_anchor_uidx` on `(routine_id, scheduled_anchor_ts)`
- index `schedule_heartbeat_as_of_idx` on `(as_of_knowledge)`
- index `schedule_heartbeat_routine_idx` on `(routine_id)`
- check `schedule_heartbeat_status_check` with `status IN ('ok','late','missed','skipped','wrong_anchor')` (`0012` `NEW_STATUSES`, replacing the narrower `0011` check `status IN ('ok','late','missed','skipped')`)

`0012` does not create another table.
