"""Phase 5d delivery: no-send payload strings only. Telegram send is Phase 5e.

Must not depend on the mm_execution module or grow a live send client here.
"""

from mm_delivery.payload import SEND_ENABLED, DeliveryPayload, assert_no_send, prepare_payload

__phase__ = 5
LIVE_TRADING_ENABLED = False

__all__ = [
    "LIVE_TRADING_ENABLED",
    "SEND_ENABLED",
    "DeliveryPayload",
    "assert_no_send",
    "prepare_payload",
]
