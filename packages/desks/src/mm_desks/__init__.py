"""Phase 5a desk skeletons (Tier 3a Crypto / Tier 3b Equities).

No runners, no market-data adapters, no orders. Must not depend on the
mm_execution module or signing surfaces. Intel must not load this package.
"""

from mm_desks.crypto import CRYPTO_DESK, CRYPTO_TIER
from mm_desks.equities import EQUITIES_DESK, EQUITIES_TIER

__phase__ = 5
LIVE_TRADING_ENABLED = False

__all__ = [
    "CRYPTO_DESK",
    "CRYPTO_TIER",
    "EQUITIES_DESK",
    "EQUITIES_TIER",
    "LIVE_TRADING_ENABLED",
]
