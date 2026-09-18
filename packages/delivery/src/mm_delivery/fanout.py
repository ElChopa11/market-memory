"""Per-desk fan-out + coord mirror (same content_hash + footer, never re-rendered)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from mm_delivery.config import TelegramSettings, chat_id_from_env, load_telegram_settings
from mm_delivery.deliver import DeliveryResult, deliver
from mm_delivery.format import escape_markdown_v2
from mm_delivery.idempotency import DedupeStore
from mm_delivery.payload import DeliveryPayload, build_payload
from mm_delivery.telegram import TelegramClient

OPS_MIRROR_FOOTER = "\n\n_ops mirror — same content_hash; not re-rendered_"
COORD_MIRROR_FOOTER = OPS_MIRROR_FOOTER
ALERTS_DESK = "alerts"
OPS_DESK = "ops"


@dataclass(frozen=True)
class FanoutResult:
    desk: str
    primary: DeliveryResult
    coord_mirror: DeliveryResult | None
    content_hash: str
    notes: tuple[str, ...] = ()

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "desk": self.desk,
            "content_hash": self.content_hash,
            "primary": self.primary.as_public_dict(),
            "coord_mirror": None if self.coord_mirror is None else self.coord_mirror.as_public_dict(),
            "notes": list(self.notes),
        }


def coord_mirror_text(markdown: str, *, content_hash: str) -> str:
    """Append footer only. Never re-render the body. Hash stays the original."""
    footer = f"{OPS_MIRROR_FOOTER}\n`{content_hash}`"
    return markdown + footer


ops_mirror_text = coord_mirror_text


def fanout_desk(
    markdown: str,
    *,
    desk: str,
    as_of: datetime,
    send: bool = False,
    completeness_pct: float | None = None,
    repo: Path | None = None,
    settings: TelegramSettings | None = None,
    client: TelegramClient | None = None,
    dedupe: DedupeStore | None = None,
    environ: dict[str, str] | None = None,
    out_root: Path | None = None,
    now: datetime | None = None,
    png: bytes | None = None,
    png_filename: str | None = None,
    failed_sink: list[dict[str, Any]] | None = None,
) -> FanoutResult:
    cfg = settings or load_telegram_settings(repo)
    primary = deliver(
        markdown,
        desk=desk,
        as_of=as_of,
        send=send,
        kind="desk_pack",
        completeness_pct=completeness_pct,
        repo=repo,
        settings=cfg,
        client=client,
        dedupe=dedupe,
        environ=environ,
        out_root=out_root,
        now=now,
        png=png,
        png_filename=png_filename,
        failed_sink=failed_sink,
    )
    notes: list[str] = []
    mirror = None
    if desk != OPS_DESK:
        mirrored = coord_mirror_text(markdown, content_hash=primary.payload.content_hash)
        # Build payload then overwrite content_hash to the ORIGINAL (never re-render).
        mirror = deliver(
            mirrored,
            desk=OPS_DESK,
            as_of=as_of,
            send=send,
            kind="desk_pack",
            completeness_pct=completeness_pct,
            repo=repo,
            settings=cfg,
            client=client,
            dedupe=dedupe,
            environ=environ,
            now=now,
            content_hash_override=primary.payload.content_hash,
            failed_sink=failed_sink,
        )
        notes.append("ops mirror uses original content_hash + footer")
    return FanoutResult(
        desk=desk,
        primary=primary,
        coord_mirror=mirror,
        content_hash=primary.payload.content_hash,
        notes=tuple(notes),
    )


def alert_payload(
    text: str,
    *,
    as_of: datetime,
    settings: TelegramSettings,
    environ: dict[str, str] | None = None,
) -> DeliveryPayload:
    return build_payload(text, desk=ALERTS_DESK, as_of=as_of, settings=settings, kind="alert", environ=environ)
