"""Load versioned listings screen YAML. Thresholds live in config, not model weights."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from mm_common.naming import RESEARCH

DEFAULT_DESK_REL = Path("config/listings/desk.yaml")
DEFAULT_CALENDAR_REL = Path("config/listings/calendar.yaml")
DEFAULT_INDEX_REL = Path("config/listings/index_events.yaml")


@dataclass(frozen=True)
class ListingsConfig:
    version: str = "imp-017.1"
    kind: str = "listings_ipo_screen"
    desk: str = RESEARCH
    n_min: int = 20
    reclaim_window_days: int = 90
    path_windows_days: tuple[int, ...] = (30, 90)
    lockup_near_days: int = 21
    thin_history_days: int = 20
    no_listing_day_is_complete: bool = True
    clip_sizes_usd: tuple[float, ...] = (10_000.0, 50_000.0, 100_000.0, 250_000.0)
    promote: bool = False
    llm: bool = False
    send: bool = False

    @classmethod
    def defaults(cls) -> ListingsConfig:
        return cls()


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a mapping")
    return data


def load_listings_config(root: Path | None = None) -> ListingsConfig:
    """Load `config/listings/desk.yaml`. Missing file raises — never invent n_min."""
    base = root if root is not None else Path.cwd()
    path = base / DEFAULT_DESK_REL
    raw = load_yaml(path)
    windows = raw.get("path_windows_days") or [30, 90]
    clips = raw.get("clip_sizes_usd") or [10_000, 50_000, 100_000, 250_000]
    if "n_min" not in raw:
        raise ValueError("listings config missing n_min")
    if raw.get("promote"):
        raise ValueError("listings config must not enable promotion")
    if raw.get("llm"):
        raise ValueError("listings config must not enable LLM")
    if raw.get("send"):
        raise ValueError("listings config must not enable send")
    desk = str(raw.get("desk") or RESEARCH)
    if desk != RESEARCH:
        raise ValueError(f"listings publishing desk must be {RESEARCH!r}, not a sixth desk")
    return ListingsConfig(
        version=str(raw.get("version") or "unknown"),
        kind=str(raw.get("kind") or "listings_ipo_screen"),
        desk=desk,
        n_min=int(raw["n_min"]),
        reclaim_window_days=int(raw.get("reclaim_window_days") or 90),
        path_windows_days=tuple(int(x) for x in windows),
        lockup_near_days=int(raw.get("lockup_near_days") or 21),
        thin_history_days=int(raw.get("thin_history_days") or 20),
        no_listing_day_is_complete=bool(raw.get("no_listing_day_is_complete", True)),
        clip_sizes_usd=tuple(float(x) for x in clips),
        promote=False,
        llm=False,
        send=False,
    )
