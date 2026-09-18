"""Run Alembic migrations against Market Memory Postgres."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from mm_memory.db import dsn_from_env, normalize_dsn

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def alembic_config(dsn: str | None = None) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", normalize_dsn(dsn or dsn_from_env()))
    cfg.set_main_option("prepend_sys_path", ".")
    cfg.set_main_option("path_separator", "os")
    return cfg


def upgrade_head(dsn: str | None = None) -> None:
    command.upgrade(alembic_config(dsn), "head")


def alembic_head() -> str:
    """Script-directory head revision. Tests should assert against this, not a frozen id.

    Reads migration files only — does not connect to Postgres.
    """
    from alembic.script import ScriptDirectory

    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    heads = ScriptDirectory.from_config(cfg).get_heads()
    if len(heads) != 1:
        raise RuntimeError(f"expected a single Alembic head, got {heads!r}")
    return heads[0]


def current_revision(dsn: str | None = None) -> str | None:
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine

    engine = create_engine(normalize_dsn(dsn or dsn_from_env()))
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        return context.get_current_revision()
