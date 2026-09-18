"""Phase 5e delivery: Telegram Bot API for desk packs.

Dry-run (``--no-send``) is the default. ``SEND_ENABLED`` stays false so send is
never implicit. Live POSTs go through ``deliver(..., send=True)`` with threshold,
quiet-hours, dedupe, and rate-limit gates. Publisher is Ops; Coord orchestrates.

Must not import ``mm_execution`` or grow a signing surface.
"""

from mm_delivery.deliver import DeliveryResult, deliver, write_payload_files
from mm_delivery.inbound import handle_inbound
from mm_delivery.payload import SEND_ENABLED, DeliveryPayload, assert_no_send, build_payload, prepare_payload
from mm_delivery.telegram import TELEGRAM_API_BASE, TelegramClient
from mm_delivery.fanout import fanout_desk
from mm_delivery.present import format_pct, format_tick, present_listings, present_scorecard, present_watchlist
from mm_delivery.watchlist import deliver_watchlist
from mm_delivery.listings import deliver_listings
from mm_delivery.scorecard import deliver_scorecard
from mm_delivery.matrix import assert_channel_matrix

__phase__ = 5
LIVE_TRADING_ENABLED = False

__all__ = [
    "LIVE_TRADING_ENABLED",
    "SEND_ENABLED",
    "TELEGRAM_API_BASE",
    "DeliveryPayload",
    "DeliveryResult",
    "TelegramClient",
    "assert_channel_matrix",
    "assert_no_send",
    "build_payload",
    "deliver",
    "deliver_listings",
    "deliver_scorecard",
    "deliver_watchlist",
    "fanout_desk",
    "format_pct",
    "format_tick",
    "handle_inbound",
    "prepare_payload",
    "present_listings",
    "present_scorecard",
    "present_watchlist",
    "write_payload_files",
]
