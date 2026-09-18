"""Ops-owned Telegram delivery of IMP-017 listings / IPO screen artifacts.

Does not invent prints, Quant R, or universe membership. Publisher is Ops.
`mm_delivery` must not import `mm_desks` — CLI/tests pass the Research canonical dict.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from mm_common.naming import LISTINGS, RESEARCH
from mm_common.time import parse_utc
from mm_delivery.config import TelegramSettings, load_telegram_settings
from mm_delivery.fanout import FanoutResult, fanout_desk
from mm_delivery.present import present_listings
from mm_delivery.telegram import TelegramClient
from mm_delivery.idempotency import DedupeStore


def deliver_listings(
    canonical: Mapping[str, Any],
    *,
    as_of: datetime | None = None,
    send: bool = False,
    repo: Path | None = None,
    settings: TelegramSettings | None = None,
    client: TelegramClient | None = None,
    dedupe: DedupeStore | None = None,
    environ: dict[str, str] | None = None,
    out_root: Path | None = None,
    now: datetime | None = None,
    failed_sink: list[dict[str, Any]] | None = None,
) -> FanoutResult:
    """Fan-out a Research listings screen on the research route + Ops mirror."""
    cfg = settings or load_telegram_settings(repo)
    product = cfg.product(LISTINGS)
    if product is None or not product.enabled:
        raise ValueError("listings delivery product is missing or disabled")
    if product.desk != RESEARCH:
        raise ValueError(f"listings delivery desk must be {RESEARCH!r}")
    markdown = present_listings(canonical)
    raw_as_of = as_of or canonical.get("as_of_knowledge")
    if raw_as_of is None:
        raise ValueError("listings delivery requires as_of_knowledge")
    watermark = raw_as_of if isinstance(raw_as_of, datetime) else parse_utc(str(raw_as_of))
    completeness = canonical.get("completeness")
    completeness_pct = None if completeness is None else float(completeness)
    digest = str(canonical.get("content_hash") or "") or None
    override = digest if product.inherit_content_hash else None
    return fanout_desk(
        markdown,
        desk=product.desk,
        as_of=watermark,
        send=send,
        completeness_pct=completeness_pct,
        repo=repo,
        settings=cfg,
        client=client,
        dedupe=dedupe,
        environ=environ,
        out_root=out_root,
        now=now,
        failed_sink=failed_sink,
        kind=product.kind,
        content_hash_override=override,
        sleeve=product.sleeve,
    )
