"""SQLAlchemy DSN + session helpers. Never logs credentials."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DSN = "postgresql://lab:lab@localhost:5432/market_memory"


def normalize_dsn(dsn: str) -> str:
    if dsn.startswith("postgresql+psycopg://"):
        return dsn
    if dsn.startswith("postgresql://"):
        return "postgresql+psycopg://" + dsn[len("postgresql://") :]
    if dsn.startswith("postgres://"):
        return "postgresql+psycopg://" + dsn[len("postgres://") :]
    return dsn


def dsn_from_env(*, default: str = DEFAULT_DSN) -> str:
    return os.environ.get("POSTGRES_DSN", default)


def make_engine(dsn: str | None = None, *, echo: bool = False) -> Engine:
    return create_engine(normalize_dsn(dsn or dsn_from_env()), echo=echo, future=True)


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
