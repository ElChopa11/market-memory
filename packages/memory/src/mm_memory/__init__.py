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
from mm_memory.brief_repository import BriefRepository
from mm_memory.paper_repository import PaperRepository
from mm_memory.queries import (
    get_thesis_by_slug,
    list_paper_trades,
    list_research_runs,
    list_theses,
    what_did_we_know,
    what_did_we_know_statement,
)
from mm_memory.repository import ObservationRepository, PutResult
from mm_memory.run_repository import ResearchRunRepository
from mm_memory.thesis_repository import ThesisRecord, ThesisRepository, UnknownObservationError

__phase__ = 4
LIVE_TRADING_ENABLED = False

__all__ = [
    "BriefRepository",
    "InMemoryObjectStore",
    "LIVE_TRADING_ENABLED",
    "NullObjectStore",
    "ObjectPointer",
    "ObservationRepository",
    "PaperRepository",
    "PutResult",
    "ResearchRunRepository",
    "S3ObjectStore",
    "ThesisRecord",
    "ThesisRepository",
    "UnknownObservationError",
    "dsn_from_env",
    "get_thesis_by_slug",
    "list_paper_trades",
    "list_research_runs",
    "list_theses",
    "make_engine",
    "object_store_from_env",
    "session_scope",
    "upgrade_head",
    "what_did_we_know",
    "what_did_we_know_statement",
]
