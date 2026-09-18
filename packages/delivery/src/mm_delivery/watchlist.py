"""Ops-owned Telegram delivery of IMP-020 watchlist monitor artifacts.

Does not invent ideas, prints, or Quant verdicts. Publisher is Ops.
`mm_delivery` must not import `mm_desks` — CLI/tests pass the Research canonical dict.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from mm_common.naming import RESEARCH, WATCHLIST
from mm_common.time import parse_utc
from mm_delivery.config import TelegramSettings, load_telegram_settings
from mm_delivery.fanout import FanoutResult, fanout_desk
from mm_delivery.present import present_watchlist
from mm_delivery.telegram import TelegramClient
from mm_delivery.idempotency import DedupeStore


def deliver_watchlist(
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
    """Fan-out a Research watchlist scan on the research route + Ops mirror."""
    cfg = settings or load_telegram_settings(repo)
    product = cfg.product(WATCHLIST)
    if product is None or not product.enabled:
        raise ValueError("watchlist delivery product is missing or disabled")
    if product.desk != RESEARCH:
        raise ValueError(f"watchlist delivery desk must be {RESEARCH!r}")
    markdown = present_watchlist(canonical)
    raw_as_of = as_of or canonical.get("as_of_knowledge")
    if raw_as_of is None:
        raise ValueError("watchlist delivery requires as_of_knowledge")
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
