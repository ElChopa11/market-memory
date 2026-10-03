"""Run Alembic migrations against Market Memory Postgres."""

from __future__ import annotations

import io
from pathlib import Path
from urllib.parse import urlparse

from alembic import command
from alembic.config import Config

from mm_memory.db import dsn_from_env, normalize_dsn

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

# Dialect placeholder for ``render_upgrade_sql`` only. Never a live host.
# 192.0.2.1 is TEST-NET-1 (RFC 5737) and is not contacted: offline mode does not connect.
OFFLINE_SQL_DSN = "postgresql://offline:offline@192.0.2.1:9/offline"


class MigrationDsnError(RuntimeError):
    """Online migrate refused this DSN before connecting.

    The message must not include the DSN, the user, the password, or the host.
    """


def alembic_config(dsn: str | None = None) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", normalize_dsn(dsn or dsn_from_env()))
    cfg.set_main_option("prepend_sys_path", ".")
    cfg.set_main_option("path_separator", "os")
    return cfg


def migration_dsn_problem(dsn: str) -> str | None:
    """Return a secret-free refusal, or None when online migrate may try to connect.

    Neon transaction-pooler hosts break DDL (prepared statements, session state).
    SQLite cannot render ``JSONB``. Neither check opens a socket.
    """
    url = normalize_dsn(dsn)
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    scheme = (parsed.scheme or "").split("+", 1)[0]
    if scheme == "sqlite":
        return (
            "lab migrate refuses sqlite. Market Memory migrations are Postgres "
            "(JSONB, timestamptz). The first sqlite attempt fails compiling "
            "observation.payload_json. Use `lab migrate --sql` for an offline Postgres plan."
        )
    if scheme not in {"postgresql", "postgres"}:
        return "lab migrate requires a Postgres DSN (POSTGRES_DSN). The scheme was not postgresql."
    if not host:
        return "POSTGRES_DSN has no host. Refusing to migrate. The DSN is not printed."
    if "-pooler" in host or ".pooler." in host:
        return (
            "lab migrate refuses a Neon transaction-pooler host. "
            "DDL needs the direct (non-pooler) POSTGRES_DSN. The host is not printed."
        )
    return None


def upgrade_head(dsn: str | None = None) -> None:
    target = dsn or dsn_from_env()
    problem = migration_dsn_problem(target)
    if problem:
        raise MigrationDsnError(problem)
    command.upgrade(alembic_config(target), "head")


def render_upgrade_sql() -> str:
    """Render upgrade-to-head SQL for the Postgres dialect.

    Does not connect and does not read ``POSTGRES_DSN``. Safe to run with no
    Neon credentials.
    """
    cfg = alembic_config(OFFLINE_SQL_DSN)
    buf = io.StringIO()
    cfg.output_buffer = buf
    command.upgrade(cfg, "head", sql=True)
    sql = buf.getvalue()
    leaked = [token for token in ("offline:offline", "192.0.2.1") if token in sql]
    if leaked:
        raise RuntimeError("offline SQL included the dialect placeholder; refusing to emit it")
    if not sql.strip():
        raise RuntimeError("offline SQL was empty")
    return sql if sql.endswith("\n") else sql + "\n"


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
