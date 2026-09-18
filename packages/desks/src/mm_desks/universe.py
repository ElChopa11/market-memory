"""Locked-universe membership helpers for desk runners. Not a Quant verdict."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_FALLBACK_CRYPTO = ("BTC", "ETH", "UNI", "AAVE")
_FALLBACK_EQUITIES = ("NVDA", "AVGO", "SMH", "MSFT", "META", "JPM", "XLF", "XOM")


@lru_cache(maxsize=8)
def _load(repo_root: str) -> dict[str, Any]:
    path = Path(repo_root) / "config" / "universe.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def universe_crypto(repo_root: Path) -> tuple[str, ...]:
    data = _load(str(repo_root.resolve()))
    names = data.get("crypto_perps") or _FALLBACK_CRYPTO
    return tuple(str(item).upper() for item in names)


def universe_equities(repo_root: Path) -> tuple[str, ...]:
    data = _load(str(repo_root.resolve()))
    names = data.get("equities") or _FALLBACK_EQUITIES
    return tuple(str(item).upper() for item in names)


def membership_of(instrument: str, repo_root: Path) -> str:
    data = _load(str(repo_root.resolve()))
    name = instrument.upper()
    in_u = {str(x).upper() for group in (data.get("in_universe") or {}).values() if isinstance(group, list) for x in group}
    watch = {str(x).upper() for group in (data.get("watch_only") or {}).values() if isinstance(group, list) for x in group}
    if name in in_u:
        return "in_universe"
    if name in watch:
        return "watch_only"
    crypto = set(universe_crypto(repo_root))
    equities = set(universe_equities(repo_root))
    if name in crypto or name in equities:
        return "watch_only"
    return "not_in_membership"
