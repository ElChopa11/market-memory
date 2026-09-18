"""Phase 5d desk runners + Phase 6a PG LISTEN/NOTIFY mesh + Phase 6b flow/macro sleeves + Phase 6c-1 five-desk roster (no Redis).

Must not depend on the mm_execution module or signing surfaces. Intel ingest
must not import this package. Telegram send is `mm_delivery.deliver` (Ops-owned).
# Boundary comment: packages here must not import mm_execution (statement form is gated).
"""

from mm_desks.mesh import mesh_from_fixture
from mm_desks.naming import sleeve_display, sleeve_tier
from mm_desks.orchestrator import PIPELINE, run_desks, run_from_fixture
from mm_desks.playbook import run_playbook_from_fixture
from mm_desks.listings import run_listings_from_fixture
from mm_desks.watchlist import run_watchlist_from_fixture
from mm_desks.scorecard import run_scorecard_from_fixture
from mm_desks.decay import run_decay_from_fixture
from mm_desks.protocol import DEGRADED, FAILED, OK, DeskOutput, DeskStatus
from mm_desks.research import RESEARCH, DISPLAY_NAME as RESEARCH_DESK
from mm_desks.roster import IC_RISK, INTEL, OPS, PUBLISHING_DESKS, QUANT

__phase__ = 6
LIVE_TRADING_ENABLED = False

CRYPTO_DESK = sleeve_display("crypto")
CRYPTO_TIER = sleeve_tier("crypto")
EQUITIES_DESK = sleeve_display("equities")
EQUITIES_TIER = sleeve_tier("equities")

__all__ = [
    "CRYPTO_DESK",
    "CRYPTO_TIER",
    "DEGRADED",
    "EQUITIES_DESK",
    "EQUITIES_TIER",
    "FAILED",
    "IC_RISK",
    "INTEL",
    "LIVE_TRADING_ENABLED",
    "OK",
    "OPS",
    "PIPELINE",
    "PUBLISHING_DESKS",
    "QUANT",
    "RESEARCH",
    "RESEARCH_DESK",
    "DeskOutput",
    "DeskStatus",
    "mesh_from_fixture",
    "run_decay_from_fixture",
    "run_desks",
    "run_from_fixture",
    "run_listings_from_fixture",
    "run_playbook_from_fixture",
    "run_scorecard_from_fixture",
    "run_watchlist_from_fixture",
]
