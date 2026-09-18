"""Phase 5e delivery: Telegram Bot API for desk packs.

Dry-run (``--no-send``) is the default. ``SEND_ENABLED`` stays false so send is
never implicit. Live POSTs go through ``deliver(..., send=True)`` with threshold,
quiet-hours, dedupe, and rate-limit gates.

Must not import ``mm_execution`` or grow a signing surface.
"""

from mm_delivery.deliver import DeliveryResult, deliver, write_payload_files
from mm_delivery.inbound import handle_inbound
from mm_delivery.payload import SEND_ENABLED, DeliveryPayload, assert_no_send, build_payload, prepare_payload
from mm_delivery.telegram import TELEGRAM_API_BASE, TelegramClient

__phase__ = 5
LIVE_TRADING_ENABLED = False

__all__ = [
    "LIVE_TRADING_ENABLED",
    "SEND_ENABLED",
    "TELEGRAM_API_BASE",
    "DeliveryPayload",
    "DeliveryResult",
    "TelegramClient",
    "assert_no_send",
    "build_payload",
    "deliver",
    "handle_inbound",
    "prepare_payload",
    "write_payload_files",
]
