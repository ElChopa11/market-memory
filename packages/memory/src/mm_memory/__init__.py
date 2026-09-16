"""Market Memory: DB models, migrations, query API.

Must not execute trades or store private keys.
"""

from mm_memory.db import dsn_from_env, make_engine, session_scope
from mm_memory.migrate import upgrade_head
from mm_memory.object_store import (
    InMemoryObjectStore,
    NullObjectStore,
    ObjectPointer,
    S3ObjectStore,
    object_store_from_env,
)
from mm_memory.queries import what_did_we_know, what_did_we_know_statement
from mm_memory.repository import ObservationRepository, PutResult

__phase__ = 1
LIVE_TRADING_ENABLED = False

__all__ = [
    "InMemoryObjectStore",
    "LIVE_TRADING_ENABLED",
    "NullObjectStore",
    "ObjectPointer",
    "ObservationRepository",
    "PutResult",
    "S3ObjectStore",
    "dsn_from_env",
    "make_engine",
    "object_store_from_env",
    "session_scope",
    "upgrade_head",
    "what_did_we_know",
    "what_did_we_know_statement",
]
