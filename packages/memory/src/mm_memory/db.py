"""SQLAlchemy DSN + session helpers. Never logs credentials."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from urllib.parse import urlparse

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from mm_memory.persistence_env import POSTGRES_DSN_ENV

DEFAULT_DSN = "postgresql://lab:lab@localhost:5432/market_memory"


def normalize_dsn(dsn: str) -> str:
    """Rewrite ``postgres://`` / ``postgresql://`` to the psycopg driver.

    Query strings (``sslmode``, ``channel_binding``) are preserved. Neon
    console strings use those parameters; do not strip them.
    """
    if dsn.startswith("postgresql+psycopg://"):
        return dsn
    if dsn.startswith("postgresql://"):
        return "postgresql+psycopg://" + dsn[len("postgresql://") :]
    if dsn.startswith("postgres://"):
        return "postgresql+psycopg://" + dsn[len("postgres://") :]
    return dsn


def dsn_from_env(*, default: str = DEFAULT_DSN) -> str:
    return os.environ.get(POSTGRES_DSN_ENV, default)


def _hostname(url: str) -> str:
    return (urlparse(url).hostname or "").lower().rstrip(".")


def engine_kwargs_for_dsn(url: str, *, echo: bool = False) -> dict[str, object]:
    """Engine kwargs that do not connect.

    Neon (including a later pooler DSN used for reads) cannot rely on
    psycopg server-side prepares. Local and CI Postgres keep the defaults.
    """
    kwargs: dict[str, object] = {"echo": echo, "future": True}
    host = _hostname(url)
    if host.endswith(".neon.tech"):
        kwargs["pool_pre_ping"] = True
        kwargs["connect_args"] = {"prepare_threshold": None}
    return kwargs


def make_engine(dsn: str | None = None, *, echo: bool = False) -> Engine:
    url = normalize_dsn(dsn or dsn_from_env())
    return create_engine(url, **engine_kwargs_for_dsn(url, echo=echo))


def make_session_factory(engine: Engine | None = None, dsn: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=engine or make_engine(dsn), autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def session_scope(dsn: str | None = None) -> Iterator[Session]:
    factory = make_session_factory(dsn=dsn)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
