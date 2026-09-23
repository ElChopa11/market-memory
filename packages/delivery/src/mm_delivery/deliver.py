"""Deliver a desk pack: dry-run default, optional gated Telegram send."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.http import missing_env_notes
from mm_common.naming import require_route_slug
from mm_common.time import as_utc, utcnow
from mm_common.env import PRINCIPAL_DM_CHAT_ID_ENV
from mm_delivery.config import (
    BOT_TOKEN_ENV,
    CHAT_ID_ENV,
    TelegramSettings,
    bot_token_from_env,
    chat_id_from_env,
    load_telegram_settings,
    principal_dm_chat_id_from_env,
    repo_root,
)
from mm_delivery.gates import (
    REASON_DEDUPE,
    REASON_DM_IS_GROUP,
    REASON_MISSING_CHAT,
    REASON_MISSING_PRINCIPAL_DM,
    REASON_MISSING_TOKEN,
    REASON_NO_SEND,
    REASON_OK,
    REASON_RATE_LIMITED,
    evaluate_send_gates,
)
from mm_delivery.idempotency import DedupeStore
from mm_delivery.payload import SEND_ENABLED, DeliveryPayload, build_payload
from mm_delivery.rate_limit import RateLimitBudget, budget_from_settings
from mm_delivery.telegram import TelegramApiResult, TelegramClient


@dataclass(frozen=True)
class DeliveryResult:
    payload: DeliveryPayload
    sent: bool
    reason: str
    notes: tuple[str, ...]
    results: tuple[TelegramApiResult, ...] = ()
    written: dict[str, str] | None = None

    @property
    def payload_hash(self) -> str:
        return self.payload.payload_hash()

    def as_public_dict(self) -> dict[str, Any]:
        payload = {
            "as_of": self.payload.as_of,
            "channel": self.payload.channel,
            "chunks": len(self.payload.chunks),
            "content_hash": self.payload.content_hash,
            "desk": self.payload.desk,
            "idempotency_key": self.payload.idempotency_key,
            "kind": self.payload.kind,
            "chat_id_env": self.payload.chat_id_env,
            "notes": list(self.notes),
            "payload_hash": self.payload_hash,
            "reason": self.reason,
            "send_enabled": SEND_ENABLED,
            "sent": self.sent,
            "source": "lab.deliver",
            "written": self.written or {},
        }
        if self.payload.desk:
            payload["desk_display"] = require_route_slug(self.payload.desk).display
        return payload


def write_payload_files(payload: DeliveryPayload, *, out_root: Path, session_date: str) -> dict[str, str]:
    """Write exact dry-run bytes under briefs/YYYY-MM-DD/. No secrets, no network."""
    day_dir = out_root / "briefs" / session_date
    day_dir.mkdir(parents=True, exist_ok=True)
    envelope = canonical_json(payload.canonical()) + "\n"
    payload_path = day_dir / "telegram-payload.json"
    hash_path = day_dir / "telegram-payload.sha256"
    payload_path.write_text(envelope, encoding="utf-8")
    digest = sha256_hex(envelope.encode("utf-8"))
    hash_path.write_text(digest + "\n", encoding="utf-8")
    return {"telegram_payload": str(payload_path), "telegram_sha256": str(hash_path)}


REASON_RETRIES_EXHAUSTED = "retries_exhausted"


def _record_failed(sink: list[dict[str, Any]] | None, payload: DeliveryPayload, reason: str, notes: tuple[str, ...]) -> None:
    if sink is None:
        return
    sink.append(
        {
            "status": "FAILED",
            "desk": payload.desk,
            "as_of": payload.as_of,
            "content_hash": payload.content_hash,
            "reason": reason,
            "notes": list(notes),
            "escalation": "ops: delivery FAILED — never silent drop (Coord orchestrates, does not publish)",
        }
    )


def deliver(
    markdown: str,
    *,
    desk: str,
    as_of: datetime,
    send: bool = False,
    kind: str = "desk_pack",
    completeness_pct: float | None = None,
    repo: Path | None = None,
    settings: TelegramSettings | None = None,
    out_root: Path | None = None,
    session_date: str | None = None,
    client: TelegramClient | None = None,
    now: datetime | None = None,
    dedupe: DedupeStore | None = None,
    environ: dict[str, str] | None = None,
    respect_quiet_hours: bool = True,
    budget: RateLimitBudget | None = None,
    content_hash_override: str | None = None,
    png: bytes | None = None,
    png_filename: str | None = None,
    failed_sink: list[dict[str, Any]] | None = None,
    chat_id_env_override: str | None = None,
    message_texts: tuple[str, ...] | None = None,
) -> DeliveryResult:
    """Build the exact payload. POST only when send=True and every gate passes.

    Tests must pass a mock ``client`` (never the live Bot API). ``SEND_ENABLED`` stays false.
    ``chat_id_env_override`` may be ``TELEGRAM_CHAT_ID_PRINCIPAL_DM`` (DM-only).
    It must never resolve a POST to ``TELEGRAM_CHAT_ID`` (Hive group).
    """
    root = repo_root(repo)
    cfg = settings or load_telegram_settings(root)
    clock = as_utc(now or utcnow())
    route = cfg.route(desk)
    desk_enabled = True if route is None else route.enabled
    gate = evaluate_send_gates(
        cfg,
        kind=kind,
        now=clock,
        completeness_pct=completeness_pct,
        desk_enabled=desk_enabled,
        respect_quiet_hours=respect_quiet_hours if send else False,
    )
    notes: list[str] = list(gate.notes)
    payload = build_payload(
        markdown,
        desk=desk,
        as_of=as_of,
        settings=cfg,
        kind=kind,
        reason=REASON_NO_SEND,
        environ=environ,
        content_hash_override=content_hash_override,
        chat_id_env_override=chat_id_env_override,
        message_texts=message_texts,
    )
    written: dict[str, str] | None = None
    if out_root is not None:
        day = session_date or as_utc(as_of).date().isoformat()
        written = write_payload_files(payload, out_root=out_root, session_date=day)

    if not send:
        return DeliveryResult(
            payload=payload,
            sent=False,
            reason=REASON_NO_SEND,
            notes=tuple(notes) if notes else ("dry-run; exact payload written; live Telegram not contacted",),
            written=written,
        )

    if not gate.allow:
        return DeliveryResult(payload=payload, sent=False, reason=gate.reason, notes=tuple(notes), written=written)

    if client is None and not bot_token_from_env(environ):
        return DeliveryResult(
            payload=payload,
            sent=False,
            reason=REASON_MISSING_TOKEN,
            notes=missing_env_notes(BOT_TOKEN_ENV, source="telegram"),
            written=written,
        )
    env = environ if environ is not None else os.environ
    if chat_id_env_override == PRINCIPAL_DM_CHAT_ID_ENV:
        chat_id = principal_dm_chat_id_from_env(env)
        if not chat_id:
            return DeliveryResult(
                payload=payload,
                sent=False,
                reason=REASON_MISSING_PRINCIPAL_DM,
                notes=missing_env_notes(PRINCIPAL_DM_CHAT_ID_ENV, source="telegram")
                + ("DM-only path; never falls back to TELEGRAM_CHAT_ID (group)",),
                written=written,
            )
        group_id = (env.get(CHAT_ID_ENV) or "").strip()
        if group_id and chat_id == group_id:
            return DeliveryResult(
                payload=payload,
                sent=False,
                reason=REASON_DM_IS_GROUP,
                notes=(
                    "TELEGRAM_CHAT_ID_PRINCIPAL_DM must not equal TELEGRAM_CHAT_ID; "
                    "DM-only path never POSTs to the Hive group",
                ),
                written=written,
            )
    else:
        chat_id = chat_id_from_env(desk, cfg, environ)
        if not chat_id:
            return DeliveryResult(
                payload=payload,
                sent=False,
                reason=REASON_MISSING_CHAT,
                notes=missing_env_notes(CHAT_ID_ENV, source="telegram"),
                written=written,
            )
        if payload.chat_id_env == PRINCIPAL_DM_CHAT_ID_ENV:
            return DeliveryResult(
                payload=payload,
                sent=False,
                reason=REASON_DM_IS_GROUP,
                notes=("group/desk send must not resolve to TELEGRAM_CHAT_ID_PRINCIPAL_DM",),
                written=written,
            )

    store = dedupe or DedupeStore(ttl_seconds=cfg.dedupe_ttl_seconds)
    store.load()
    if store.seen(payload.idempotency_key, clock):
        return DeliveryResult(
            payload=payload,
            sent=False,
            reason=REASON_DEDUPE,
            notes=("idempotency key already sent within dedupe TTL; not double-posted",),
            written=written,
        )

    limiter = budget or budget_from_settings(cfg.rate_limit)
    if client is None:
        api = TelegramClient.from_settings(cfg, environ=environ)
        owns = True
    else:
        api = client
        owns = False
    results: list[TelegramApiResult] = []
    try:
        for chunk in payload.chunks:
            if not limiter.allow():
                fail_notes = ("telegram rate_limit exhausted; remaining chunks not sent",)
                _record_failed(failed_sink, payload, REASON_RATE_LIMITED, fail_notes)
                return DeliveryResult(
                    payload=payload,
                    sent=False,
                    reason=REASON_RATE_LIMITED,
                    notes=fail_notes,
                    results=tuple(results),
                    written=written,
                )
            result = api.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=payload.parse_mode,
                message_thread_id=payload.message_thread_id,
                disable_web_page_preview=payload.disable_web_page_preview,
            )
            results.append(result)
            if not result.ok:
                fail_notes = result.notes or ("telegram sendMessage failed",)
                reason = REASON_RETRIES_EXHAUSTED if result.error_class in {"http_5xx", "rate_limited"} else result.error_class
                _record_failed(failed_sink, payload, reason, fail_notes + ("never silent drop", "ops escalation: delivery FAILED"))
                return DeliveryResult(
                    payload=payload,
                    sent=False,
                    reason=reason,
                    notes=fail_notes + ("never silent drop",),
                    results=tuple(results),
                    written=written,
                )
        if png is not None:
            caption = payload.chunks[0] if payload.chunks else ""
            if len(caption) > 1024:
                photo = api.send_document(
                    chat_id=chat_id,
                    document=png_filename or f"{payload.content_hash}.png",
                    caption=None,
                    message_thread_id=payload.message_thread_id,
                    files={"document": (png_filename or f"{payload.content_hash}.png", png, "image/png")},
                )
                results.append(photo)
            else:
                photo = api.send_photo(
                    chat_id=chat_id,
                    photo=png_filename or f"{payload.content_hash}.png",
                    caption=caption,
                    message_thread_id=payload.message_thread_id,
                    files={"photo": (png_filename or f"{payload.content_hash}.png", png, "image/png")},
                )
                results.append(photo)
            if not results[-1].ok:
                fail_notes = results[-1].notes or ("telegram media send failed",)
                _record_failed(failed_sink, payload, REASON_RETRIES_EXHAUSTED, fail_notes + ("never silent drop",))
                return DeliveryResult(
                    payload=payload,
                    sent=False,
                    reason=REASON_RETRIES_EXHAUSTED,
                    notes=fail_notes + ("never silent drop",),
                    results=tuple(results),
                    written=written,
                )
    finally:
        if owns:
            api.close()

    store.remember(payload.idempotency_key, clock)
    return DeliveryResult(
        payload=payload,
        sent=True,
        reason=REASON_OK,
        notes=("sent",),
        results=tuple(results),
        written=written,
    )
