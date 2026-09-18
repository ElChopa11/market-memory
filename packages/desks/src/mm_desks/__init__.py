"""Phase 5d desk runners + Phase 6a PG LISTEN/NOTIFY mesh + Phase 6b flow/macro (no Redis).

Must not depend on the mm_execution module or signing surfaces. Intel ingest
must not import this package. Telegram send is `mm_delivery.deliver` (Phase 5e).
"""

from mm_desks.crypto import CRYPTO_DESK, CRYPTO_TIER
from mm_desks.equities import EQUITIES_DESK, EQUITIES_TIER
from mm_desks.mesh import mesh_from_fixture
from mm_desks.orchestrator import PIPELINE, run_desks, run_from_fixture
from mm_desks.protocol import DEGRADED, FAILED, OK, DeskOutput, DeskStatus

__phase__ = 6
LIVE_TRADING_ENABLED = False

__all__ = [
    "CRYPTO_DESK",
    "CRYPTO_TIER",
    "DEGRADED",
    "EQUITIES_DESK",
    "EQUITIES_TIER",
    "FAILED",
    "LIVE_TRADING_ENABLED",
    "OK",
    "PIPELINE",
    "DeskOutput",
    "DeskStatus",
    "mesh_from_fixture",
    "run_desks",
    "run_from_fixture",
]
