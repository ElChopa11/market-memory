"""Phase 5d desk runners (Tier 3a/3b orchestration plus Intel/Quant/Skeptic/Risk/Coord).

Must not depend on the mm_execution module or signing surfaces. Intel ingest
must not import this package. Telegram send is Phase 5e.
"""

from mm_desks.crypto import CRYPTO_DESK, CRYPTO_TIER
from mm_desks.equities import EQUITIES_DESK, EQUITIES_TIER
from mm_desks.orchestrator import PIPELINE, run_desks, run_from_fixture
from mm_desks.protocol import DEGRADED, FAILED, OK, DeskOutput, DeskStatus

__phase__ = 5
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
    "run_desks",
    "run_from_fixture",
]
