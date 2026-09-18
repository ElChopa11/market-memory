"""Per-desk fan-out + Ops mirror (same content_hash + footer, never re-rendered).

Publisher is Ops. Coord/Don orchestrates and is not the publisher.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from mm_common.naming import ALERTS, OPS, require_route_slug, telegram_header, with_telegram_header
from mm_delivery.config import TelegramSettings, load_telegram_settings
from mm_delivery.deliver import DeliveryResult, deliver
from mm_delivery.idempotency import DedupeStore
from mm_delivery.payload import DeliveryPayload, build_payload
from mm_delivery.telegram import TelegramClient

OPS_MIRROR_FOOTER = "\n\n_ops mirror — same content_hash; not re-rendered_"
COORD_MIRROR_FOOTER = OPS_MIRROR_FOOTER
ALERTS_DESK = ALERTS
OPS_DESK = OPS
PUBLISHER = OPS


@dataclass(frozen=True)
class FanoutResult:
    desk: str
    primary: DeliveryResult
    ops_mirror: DeliveryResult | None
    content_hash: str
    notes: tuple[str, ...] = ()
    publisher: str = PUBLISHER

    @property
    def coord_mirror(self) -> DeliveryResult | None:
        """Compat alias. The mirror desk is Ops; Coord does not publish."""
        return self.ops_mirror

    def as_public_dict(self) -> dict[str, Any]:
        mirror = None if self.ops_mirror is None else self.ops_mirror.as_public_dict()
        return {
            "desk": self.desk,
            "desk_display": require_route_slug(self.desk).display,
            "header": telegram_header(self.desk),
            "content_hash": self.content_hash,
            "publisher": self.publisher,
            "primary": self.primary.as_public_dict(),
            "ops_mirror": mirror,
            "coord_mirror": mirror,
            "notes": list(self.notes),
        }


def ops_mirror_text(markdown: str, *, content_hash: str) -> str:
    """Append footer only. Never re-render the body. Hash stays the original."""
    footer = f"{OPS_MIRROR_FOOTER}\n`{content_hash}`"
    return markdown + footer


coord_mirror_text = ops_mirror_text


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
    kind: str = "desk_pack",
    content_hash_override: str | None = None,
    artifact_type: str | None = None,
    sleeve: str | None = None,
) -> FanoutResult:
    cfg = settings or load_telegram_settings(repo)
    require_route_slug(desk)
    headed = with_telegram_header(markdown, desk, artifact_type=artifact_type, sleeve=sleeve)
    primary = deliver(
        headed,
        desk=desk,
        as_of=as_of,
        send=send,
        kind=kind,
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
        content_hash_override=content_hash_override,
    )
    notes: list[str] = []
    mirror = None
    if desk != OPS_DESK:
        mirrored = ops_mirror_text(headed, content_hash=primary.payload.content_hash)
        # Build payload then overwrite content_hash to the ORIGINAL (never re-render).
        mirror = deliver(
            mirrored,
            desk=OPS_DESK,
            as_of=as_of,
            send=send,
            kind=kind,
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
        notes.append("ops mirror uses original content_hash + footer; Coord does not publish")
    return FanoutResult(
        desk=desk,
        primary=primary,
        ops_mirror=mirror,
        content_hash=primary.payload.content_hash,
        notes=tuple(notes),
        publisher=PUBLISHER,
    )


def alert_payload(
    text: str,
    *,
    as_of: datetime,
    settings: TelegramSettings,
    environ: dict[str, str] | None = None,
) -> DeliveryPayload:
    return build_payload(text, desk=ALERTS_DESK, as_of=as_of, settings=settings, kind="alert", environ=environ)
