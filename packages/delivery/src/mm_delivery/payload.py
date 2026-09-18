"""Dry-run Telegram payload envelopes. Byte-stable when inputs are frozen."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import as_utc
from mm_delivery.config import CHAT_ID_ENV, TelegramSettings, resolve_chat_id_env
from mm_delivery.format import chunk_markdown_v2
from mm_delivery.idempotency import idempotency_key

SEND_ENABLED = False
CHANNEL = "telegram"


@dataclass(frozen=True)
class DeliveryPayload:
    """Exact sendMessage envelope (chunked). Token and live chat_id values are never stored."""

    channel: str
    text: str
    content_hash: str
    send: bool = False
    reason: str = "no_send"
    desk: str = ""
    as_of: str = ""
    idempotency_key: str = ""
    chunks: tuple[str, ...] = ()
    chat_id_env: str = CHAT_ID_ENV
    message_thread_id: int | None = None
    parse_mode: str = "MarkdownV2"
    method: str = "sendMessage"
    disable_web_page_preview: bool = True
    kind: str = "desk_pack"
    send_enabled: bool = SEND_ENABLED

    def canonical(self) -> dict[str, Any]:
        return {
            "as_of": self.as_of,
            "channel": self.channel,
            "chat_id_env": self.chat_id_env,
            "chunks": [
                {"of": len(self.chunks), "seq": i, "text": chunk}
                for i, chunk in enumerate(self.chunks, start=1)
            ],
            "content_hash": self.content_hash,
            "desk": self.desk,
            "disable_web_page_preview": self.disable_web_page_preview,
            "idempotency_key": self.idempotency_key,
            "kind": self.kind,
            "message_thread_id": self.message_thread_id,
            "method": self.method,
            "parse_mode": self.parse_mode,
            "reason": self.reason,
            "send": False,
            "send_enabled": SEND_ENABLED,
            "text": self.text,
        }

    def payload_hash(self) -> str:
        return sha256_hex((canonical_json(self.canonical()) + "\n").encode("utf-8"))


def prepare_payload(markdown: str, *, channel: str = CHANNEL) -> DeliveryPayload:
    """Build a no-send payload string. Does not open a network connection."""
    text = markdown
    chunks = chunk_markdown_v2(text)
    return DeliveryPayload(
        channel=channel,
        text=text,
        content_hash=sha256_hex(text.encode("utf-8")),
        send=False,
        reason="no_send",
        chunks=chunks,
    )


def build_payload(
    markdown: str,
    *,
    desk: str,
    as_of: datetime,
    settings: TelegramSettings,
    kind: str = "desk_pack",
    reason: str = "no_send",
    environ: dict[str, str] | None = None,
    content_hash_override: str | None = None,
) -> DeliveryPayload:
    """Exact Telegram chunks + idempotency key. Secrets stay in env, not in this object."""
    watermark = as_utc(as_of)
    content_hash = content_hash_override or sha256_hex(markdown.encode("utf-8"))
    key = idempotency_key(desk=desk, as_of=watermark, content_hash=content_hash)
    chunks = chunk_markdown_v2(markdown, limit=settings.max_message_chars)
    route = settings.route(desk)
    thread_id = route.thread_id if route else None
    chat_env = resolve_chat_id_env(desk, settings, environ)
    return DeliveryPayload(
        channel=settings.channel,
        text=markdown,
        content_hash=content_hash,
        send=False,
        reason=reason,
        desk=desk,
        as_of=watermark.isoformat(),
        idempotency_key=key,
        chunks=chunks,
        chat_id_env=chat_env,
        message_thread_id=thread_id,
        parse_mode=settings.parse_mode,
        method="sendMessage",
        disable_web_page_preview=settings.disable_web_page_preview,
        kind=kind,
        send_enabled=SEND_ENABLED,
    )


def assert_no_send(*, send_requested: bool = False) -> None:
    """Dry-run guard. Module SEND_ENABLED stays false; explicit send uses deliver()."""
    if SEND_ENABLED:
        raise RuntimeError("SEND_ENABLED must stay false; pass send=True into deliver()")
    if send_requested:
        raise RuntimeError("explicit send must go through mm_delivery.deliver (not SEND_ENABLED)")
