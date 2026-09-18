"""Locked-universe membership helpers for desk runners. Not a Quant verdict."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_FALLBACK_CRYPTO = ("BTC", "ETH", "UNI", "AAVE")
_FALLBACK_EQUITIES = ("NVDA", "AVGO", "SMH", "MSFT", "META", "JPM", "XLF", "XOM")
_FALLBACK_IN_UNIVERSE_CRYPTO = ("BTC",)
_FALLBACK_IN_UNIVERSE_EQUITIES = ("NVDA", "AVGO", "MSFT", "META", "JPM", "XOM")
_FALLBACK_WATCH_ONLY_CRYPTO = ("ETH", "UNI", "AAVE")
_FALLBACK_WATCH_ONLY_EQUITIES = ("SMH", "XLF")

MEMBERSHIP_IN_UNIVERSE = "in_universe"
MEMBERSHIP_WATCH_ONLY = "watch_only"
MEMBERSHIP_DEFERRED = "deferred_must_cut"
MEMBERSHIP_UNSET = "not_in_membership"
SLEEVE_CRYPTO = "crypto"
SLEEVE_EQUITIES = "equities"


@dataclass(frozen=True)
class MembershipName:
    """One locked-universe name. Membership is Principal lock, not a Quant verdict."""

    instrument: str
    membership: str
    sleeve: str
    asset_class: str

    def canonical(self) -> dict[str, str]:
        return {
            "instrument": self.instrument,
            "membership": self.membership,
            "sleeve": self.sleeve,
            "asset_class": self.asset_class,
        }


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


def _partition(data: dict[str, Any], key: str, group: str, fallback: tuple[str, ...]) -> tuple[str, ...]:
    block = data.get(key) if isinstance(data.get(key), dict) else {}
    names = block.get(group) if isinstance(block, dict) else None
    if not names:
        return fallback
    return tuple(str(item).upper() for item in names)


def in_universe_crypto(repo_root: Path) -> tuple[str, ...]:
    data = _load(str(repo_root.resolve()))
    return _partition(data, "in_universe", "crypto_perps", _FALLBACK_IN_UNIVERSE_CRYPTO)


def in_universe_equities(repo_root: Path) -> tuple[str, ...]:
    data = _load(str(repo_root.resolve()))
    return _partition(data, "in_universe", "equities", _FALLBACK_IN_UNIVERSE_EQUITIES)


def watch_only_crypto(repo_root: Path) -> tuple[str, ...]:
    data = _load(str(repo_root.resolve()))
    return _partition(data, "watch_only", "crypto_perps", _FALLBACK_WATCH_ONLY_CRYPTO)


def watch_only_equities(repo_root: Path) -> tuple[str, ...]:
    data = _load(str(repo_root.resolve()))
    return _partition(data, "watch_only", "equities", _FALLBACK_WATCH_ONLY_EQUITIES)


def deferred_must_cut(repo_root: Path) -> tuple[str, ...]:
    data = _load(str(repo_root.resolve()))
    crypto = _partition(data, "deferred_must_cut", "crypto", ())
    equities = _partition(data, "deferred_must_cut", "equities", ())
    return crypto + equities


def membership_of(instrument: str, repo_root: Path) -> str:
    data = _load(str(repo_root.resolve()))
    name = instrument.upper()
    in_u = {str(x).upper() for group in (data.get("in_universe") or {}).values() if isinstance(group, list) for x in group}
    watch = {str(x).upper() for group in (data.get("watch_only") or {}).values() if isinstance(group, list) for x in group}
    deferred = {str(x).upper() for group in (data.get("deferred_must_cut") or {}).values() if isinstance(group, list) for x in group}
    if name in in_u:
        return MEMBERSHIP_IN_UNIVERSE
    if name in watch:
        return MEMBERSHIP_WATCH_ONLY
    if name in deferred:
        return MEMBERSHIP_DEFERRED
    crypto = set(universe_crypto(repo_root))
    equities = set(universe_equities(repo_root))
    if name in crypto or name in equities:
        return MEMBERSHIP_WATCH_ONLY
    return MEMBERSHIP_UNSET


def locked_watchlist(repo_root: Path) -> tuple[MembershipName, ...]:
    """in_universe ∪ watch_only, universe.yaml order. Never deferred_must_cut. Never promotion."""
    crypto_in = in_universe_crypto(repo_root)
    crypto_watch = watch_only_crypto(repo_root)
    eq_in = in_universe_equities(repo_root)
    eq_watch = watch_only_equities(repo_root)
    deferred = set(deferred_must_cut(repo_root))
    out: list[MembershipName] = []
    seen: set[str] = set()
    for instrument in universe_crypto(repo_root):
        if instrument in deferred or instrument in seen:
            continue
        membership = MEMBERSHIP_IN_UNIVERSE if instrument in crypto_in else MEMBERSHIP_WATCH_ONLY
        if instrument not in crypto_in and instrument not in crypto_watch:
            membership = MEMBERSHIP_WATCH_ONLY
        out.append(
            MembershipName(
                instrument=instrument,
                membership=membership,
                sleeve=SLEEVE_CRYPTO,
                asset_class="crypto_perp",
            )
        )
        seen.add(instrument)
    for instrument in universe_equities(repo_root):
        if instrument in deferred or instrument in seen:
            continue
        membership = MEMBERSHIP_IN_UNIVERSE if instrument in eq_in else MEMBERSHIP_WATCH_ONLY
        if instrument not in eq_in and instrument not in eq_watch:
            membership = MEMBERSHIP_WATCH_ONLY
        out.append(
            MembershipName(
                instrument=instrument,
                membership=membership,
                sleeve=SLEEVE_EQUITIES,
                asset_class="equity",
            )
        )
        seen.add(instrument)
    return tuple(out)


def locked_instruments(repo_root: Path) -> tuple[str, ...]:
    return tuple(row.instrument for row in locked_watchlist(repo_root))
