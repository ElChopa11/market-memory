"""Desk mesh cadence metadata (Phase 6a + 6c-1 five-desk roster). YAML-backed; no Redis."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from mm_desks.naming import (
    ASSEMBLE_CHANNEL,
    DESK_META,
    DQ_CHANNEL,
    IC_RISK,
    INTEL,
    desk_display as naming_desk_display,
    desk_tier as naming_desk_tier,
    require_publishing_desk,
)

DEFAULT_CADENCE_REL = Path("config/desks/cadence.yaml")
REGIME_PLACEHOLDER = "unset"
DEFAULT_CADENCE = "daily"
DEFAULT_OP = "observation"
OP_VALUES = ("paper", "observation")

CHANNEL_OUTPUT = "desk.{slug}.output"
CHANNEL_ALERT = "desk.{slug}.alert"
CHANNEL_ASSEMBLE = ASSEMBLE_CHANNEL
CHANNEL_DQ = DQ_CHANNEL


@dataclass(frozen=True)
class DeskCadence:
    slug: str
    cadence: str
    op: str
    output_channel: str
    alert_channel: str
    dq_channel: str | None = None


@dataclass(frozen=True)
class CadenceConfig:
    version: str
    regime_placeholder: str
    channels: tuple[str, ...]
    desks: dict[str, DeskCadence]


def _fallback_desk(slug: str) -> DeskCadence:
    output = CHANNEL_OUTPUT.format(slug=slug)
    alert = CHANNEL_ALERT.format(slug=slug)
    dq = CHANNEL_DQ if slug == INTEL else None
    op = "paper" if slug == IC_RISK else DEFAULT_OP
    return DeskCadence(
        slug=slug,
        cadence=DEFAULT_CADENCE,
        op=op,
        output_channel=output,
        alert_channel=alert,
        dq_channel=dq,
    )


@lru_cache(maxsize=8)
def _load(repo_root: str) -> CadenceConfig:
    path = Path(repo_root) / DEFAULT_CADENCE_REL
    if not path.is_file():
        desks = {slug: _fallback_desk(slug) for slug in DESK_META}
        channels = tuple(
            sorted(
                {d.output_channel for d in desks.values()}
                | {d.alert_channel for d in desks.values()}
                | {CHANNEL_DQ, CHANNEL_ASSEMBLE}
            )
        )
        return CadenceConfig(
            version="imp-019.1",
            regime_placeholder=REGIME_PLACEHOLDER,
            channels=channels,
            desks=desks,
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    default = raw.get("default") if isinstance(raw.get("default"), dict) else {}
    default_cadence = str(default.get("cadence") or DEFAULT_CADENCE)
    default_op = str(default.get("op") or DEFAULT_OP)
    listed = raw.get("desks") if isinstance(raw.get("desks"), dict) else {}
    desks: dict[str, DeskCadence] = {}
    for slug in DESK_META:
        row = listed.get(slug) if isinstance(listed.get(slug), dict) else {}
        fb = _fallback_desk(slug)
        op = str(row.get("op") or default_op or fb.op)
        if op not in OP_VALUES:
            op = fb.op
        desks[slug] = DeskCadence(
            slug=slug,
            cadence=str(row.get("cadence") or default_cadence),
            op=op,
            output_channel=str(row.get("output_channel") or fb.output_channel),
            alert_channel=str(row.get("alert_channel") or fb.alert_channel),
            dq_channel=(str(row["dq_channel"]) if row.get("dq_channel") else fb.dq_channel),
        )
    channels_raw = raw.get("channels")
    if isinstance(channels_raw, list) and channels_raw:
        channels = tuple(str(item) for item in channels_raw)
    else:
        extra = [d.dq_channel for d in desks.values() if d.dq_channel]
        channels = tuple(
            sorted(
                {d.output_channel for d in desks.values()}
                | {d.alert_channel for d in desks.values()}
                | set(extra)
                | {CHANNEL_ASSEMBLE, CHANNEL_DQ}
            )
        )
    return CadenceConfig(
        version=str(raw.get("version") or "imp-019.1"),
        regime_placeholder=str(raw.get("regime_placeholder") or REGIME_PLACEHOLDER),
        channels=channels,
        desks=desks,
    )


def load_cadence(repo_root: Path | None = None) -> CadenceConfig:
    root = str((repo_root or Path(".")).resolve())
    return _load(root)


def cadence_for(slug: str, repo_root: Path | None = None) -> DeskCadence:
    require_publishing_desk(slug)
    cfg = load_cadence(repo_root)
    return cfg.desks.get(slug) or _fallback_desk(slug)


def all_channels(repo_root: Path | None = None) -> tuple[str, ...]:
    return load_cadence(repo_root).channels


def desk_display(slug: str) -> str:
    return naming_desk_display(slug)


def desk_tier(slug: str) -> str:
    return naming_desk_tier(slug)


def clear_cadence_cache() -> None:
    _load.cache_clear()
