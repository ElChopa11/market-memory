"""Phase 5d no-send payload prep. Telegram Bot API send is Phase 5e."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mm_common.hashing import sha256_hex

SEND_ENABLED = False
CHANNEL = "telegram"


@dataclass(frozen=True)
class DeliveryPayload:
    """Dry-run string payload. Never sent in Phase 5d."""

    channel: str
    text: str
    content_hash: str
    send: bool = False
    reason: str = "phase_5e_not_enabled"

    def canonical(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "text": self.text,
            "content_hash": self.content_hash,
            "send": self.send,
            "reason": self.reason,
            "send_enabled": SEND_ENABLED,
        }


def prepare_payload(markdown: str, *, channel: str = CHANNEL) -> DeliveryPayload:
    """Build a no-send payload string. Does not open a network connection."""
    text = markdown
    return DeliveryPayload(
        channel=channel,
        text=text,
        content_hash=sha256_hex(text.encode("utf-8")),
        send=False,
        reason="phase_5e_not_enabled",
    )


def assert_no_send(*, send_requested: bool = False) -> None:
    if send_requested or SEND_ENABLED:
        raise RuntimeError("Telegram send is Phase 5e; SEND_ENABLED is false")
