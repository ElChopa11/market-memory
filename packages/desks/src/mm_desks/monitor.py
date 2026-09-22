"""Principal-locked watchlist monitor.yaml (IMP-033 + IMP-034 ticker resolutions).

Intel owns ticker resolution and lockup watch. Research scans the list and
must state tier on every idea. Does not promote names into universe.yaml.
Gate 5 event blackout (earnings and other verified gate5_relevant rows) loads
config/macro/event_calendar.yaml via mm_desks.event_calendar. Lockup blackout
still reads fail_closed_blackout_until from this monitor file.
# Boundary comment: packages here must not import mm_execution (statement form is gated).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from mm_common.time import as_utc
from mm_desks.event_calendar import event_blackout_reason
from mm_desks.universe import (
    MEMBERSHIP_DEFERRED,
    MEMBERSHIP_IN_UNIVERSE,
    MEMBERSHIP_UNSET,
    MEMBERSHIP_WATCH_ONLY,
    membership_of,
)

MONITOR_CFG_REL = Path("config/watchlist/monitor.yaml")
LISTINGS_FEED_REL = Path("config/listings/watchlist_new_listings.yaml")
ENGINE_VERSION = "imp-034.1"

TIER_UNIVERSE = "universe"
TIER_MONITOR = "monitor"
TIER_BLOCKED = "blocked"
RESOLUTION_RESOLVED = "resolved"
RESOLUTION_UNRESOLVED = "unresolved"
UNSIZED_REASON = "not in locked universe — promotion requires Principal PR"
SMA200_MIN_BARS = 200
UNRESOLVED_TICKERS: tuple[str, ...] = ()
CLUSTERS = (
    "crypto_major",
    "crypto_alt",
    "privacy",
    "meme_t3",
    "crypto_beta_equity",
    "semis_ai",
    "index_futures",
    "energy",
    "idio",
    "unresolved",
)


@dataclass(frozen=True)
class MonitorName:
    ticker: str
    membership_key: str
    tape_alias: str
    round: str
    tier: str
    cluster: str
    archive: bool
    new_listing: bool
    cluster_note: str
    membership: str
    resolution_status: str
    qualified_id: str | None
    venue: str | None

    def canonical(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "membership_key": self.membership_key,
            "tape_alias": self.tape_alias,
            "round": self.round,
            "tier": self.tier,
            "cluster": self.cluster,
            "archive": self.archive,
            "new_listing": self.new_listing,
            "cluster_note": self.cluster_note,
            "membership": self.membership,
            "resolution_status": self.resolution_status,
            "qualified_id": self.qualified_id,
            "venue": self.venue,
        }


@dataclass(frozen=True)
class LockupWatch:
    ticker: str
    confirmed: bool
    assume_180d: bool
    fail_closed_blackout_until: date | None
    terms: str
    url: str
    cik: str


def _parse_day(value: Any) -> date | None:
    if not value or value in {"unresolved", "unavailable"}:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


@lru_cache(maxsize=8)
def _load(repo_root: str) -> dict[str, Any]:
    path = Path(repo_root) / MONITOR_CFG_REL
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_monitor_spec(repo_root: Path) -> dict[str, Any]:
    data = _load(str(Path(repo_root).resolve()))
    if not data:
        raise FileNotFoundError(f"missing Principal watchlist {MONITOR_CFG_REL}")
    if data.get("promote"):
        raise ValueError("monitor.yaml must not enable promotion")
    if data.get("llm"):
        raise ValueError("monitor.yaml must not enable LLM")
    if data.get("send"):
        raise ValueError("monitor.yaml must not enable send")
    if str(data.get("owner") or "").strip().lower() != "intel":
        raise ValueError("monitor.yaml owner must be intel")
    return data


def resolution_of(ticker: str, spec: dict[str, Any]) -> dict[str, Any]:
    block = spec.get("resolution") if isinstance(spec.get("resolution"), dict) else {}
    row = block.get(ticker) if isinstance(block, dict) else None
    if not isinstance(row, dict):
        return {"status": RESOLUTION_UNRESOLVED, "qualified_id": None, "venue": None}
    status = str(row.get("status") or RESOLUTION_UNRESOLVED).lower()
    if status not in {RESOLUTION_RESOLVED, RESOLUTION_UNRESOLVED}:
        status = RESOLUTION_UNRESOLVED
    qid = row.get("qualified_id")
    return {
        "status": status,
        "qualified_id": None if qid in (None, "", "unresolved") else str(qid),
        "venue": None if row.get("venue") in (None, "", "unresolved") else str(row.get("venue")),
        "note": str(row.get("note") or ""),
    }


def _membership_for_key(key: str, repo_root: Path) -> str:
    return membership_of(key, repo_root)


def monitor_names(repo_root: Path) -> tuple[MonitorName, ...]:
    """Principal complete review list. Never invents unresolved ids. Never promotes."""
    root = Path(repo_root).resolve()
    spec = load_monitor_spec(root)
    rows = spec.get("names") or []
    out: list[MonitorName] = []
    seen: set[str] = set()
    for raw in rows:
        if not isinstance(raw, dict) or not raw.get("ticker"):
            continue
        ticker = str(raw["ticker"]).strip()
        if ticker in seen:
            raise ValueError(f"duplicate monitor ticker {ticker}")
        seen.add(ticker)
        key = str(raw.get("membership_key") or ticker).strip()
        res = resolution_of(ticker, spec)
        membership = _membership_for_key(key, root)
        tier = str(raw.get("tier") or TIER_MONITOR)
        if ticker in set(spec.get("blocked_names") or ()):
            tier = TIER_BLOCKED
        if tier == TIER_UNIVERSE and membership != MEMBERSHIP_IN_UNIVERSE:
            raise ValueError(
                f"{ticker} marked universe but membership_key {key} is {membership}; "
                "universe tier must match locked in_universe"
            )
        if membership == MEMBERSHIP_IN_UNIVERSE and tier not in {TIER_UNIVERSE, TIER_BLOCKED}:
            # Sizeable in-universe names on this list must carry the universe tier.
            raise ValueError(f"{ticker} is in_universe and must be tier=universe")
        out.append(
            MonitorName(
                ticker=ticker,
                membership_key=key.upper(),
                tape_alias=str(raw.get("tape_alias") or key).upper(),
                round=str(raw.get("round") or ""),
                tier=tier,
                cluster=str(raw.get("cluster") or "idio"),
                archive=bool(raw.get("archive")),
                new_listing=bool(raw.get("new_listing")),
                cluster_note=str(raw.get("cluster_note") or ""),
                membership=membership,
                resolution_status=res["status"],
                qualified_id=res["qualified_id"],
                venue=res["venue"],
            )
        )
    return tuple(out)


def monitor_tickers(repo_root: Path) -> tuple[str, ...]:
    return tuple(row.ticker for row in monitor_names(repo_root))


def name_by_ticker(ticker: str, repo_root: Path) -> MonitorName | None:
    want = str(ticker or "").strip()
    want_up = want.upper()
    for row in monitor_names(repo_root):
        if row.ticker == want or row.ticker.upper() == want_up:
            return row
        if row.membership_key == want_up or row.tape_alias == want_up:
            return row
    return None


def watchlist_tier_for(instrument: str, repo_root: Path) -> str:
    row = name_by_ticker(instrument, repo_root)
    return row.tier if row is not None else "unset"


def sma200_display(n_bars: int | None) -> str:
    """Never '?' and never a silent shorter MA substitute."""
    if n_bars is None:
        return "n/a (insufficient history: unavailable bars)"
    n = int(n_bars)
    if n < SMA200_MIN_BARS:
        return f"n/a (insufficient history: {n} bars)"
    return "available (compute on listings / tape path; not invented here)"


def is_new_listing(row: MonitorName, *, n_bars: int | None) -> bool:
    if row.new_listing:
        return True
    if n_bars is not None and int(n_bars) < SMA200_MIN_BARS:
        return True
    return False


def scan_pod_for(row: MonitorName, *, n_bars: int | None) -> str:
    if is_new_listing(row, n_bars=n_bars):
        return "listings"
    return "watchlist"


def lockup_watches(repo_root: Path) -> tuple[LockupWatch, ...]:
    spec = load_monitor_spec(repo_root)
    block = spec.get("lockup_watch") if isinstance(spec.get("lockup_watch"), dict) else {}
    names = block.get("names") if isinstance(block, dict) else {}
    if not isinstance(names, dict):
        return ()
    out: list[LockupWatch] = []
    for ticker, raw in names.items():
        if not isinstance(raw, dict):
            continue
        if raw.get("assume_180d"):
            raise ValueError(f"{ticker} lockup must not assume flat 180d")
        out.append(
            LockupWatch(
                ticker=str(ticker),
                confirmed=bool(raw.get("confirmed")),
                assume_180d=False,
                fail_closed_blackout_until=_parse_day(raw.get("fail_closed_blackout_until")),
                terms=str(raw.get("lockup_period") or "").strip(),
                url=str(raw.get("url") or ""),
                cik=str(raw.get("cik") or ""),
            )
        )
    return tuple(out)


def lockup_inside_horizon(ticker: str, as_of: datetime, repo_root: Path) -> bool:
    """Fail closed: material lockup still active unless as_of is after the documented bound."""
    cut = as_utc(as_of).date()
    for watch in lockup_watches(repo_root):
        if watch.ticker.upper() != str(ticker).upper():
            continue
        if watch.fail_closed_blackout_until is None:
            return True
        return cut < watch.fail_closed_blackout_until
    return False


def idea_eligible(
    row: MonitorName,
    *,
    as_of: datetime | None,
    repo_root: Path,
    horizon: Any = None,
) -> tuple[bool, str]:
    """Whether a general (non-listings) idea may be published for this name.

    ``horizon`` is the candidate window (days, ``5d``, or an end date). When it
    is omitted, the event calendar's ``default_horizon_days`` is the window.
    A verified gate-5 event blocks when that window crosses the event date.
    """
    if row.resolution_status == RESOLUTION_UNRESOLVED:
        return False, "unresolved ticker; excluded from ideas"
    if row.tier == TIER_BLOCKED:
        return False, "blocked; state only; never idea/size"
    if as_of is not None and lockup_inside_horizon(row.ticker, as_of, repo_root):
        return False, "lockup inside horizon; gate 5 (Skeptic) blackout"
    if as_of is not None:
        event_reason = event_blackout_reason(row, as_of=as_of, repo_root=repo_root, horizon=horizon)
        if event_reason:
            return False, event_reason
    if row.new_listing:
        return False, "NEW_LISTING; route to listings sleeve, not general equities scan"
    if row.tier == TIER_MONITOR:
        return True, UNSIZED_REASON
    if row.tier == TIER_UNIVERSE:
        return True, "universe tier; size still subject to cluster netting and Risk"
    return False, "not on locked monitor"


def idea_size_policy(row: MonitorName) -> str:
    if row.tier == TIER_BLOCKED or row.resolution_status == RESOLUTION_UNRESOLVED:
        return "none"
    if row.cluster == "meme_t3":
        return "zero"
    if row.tier == TIER_MONITOR:
        return "UNSIZED"
    return "cluster_capped"


def net_sized_ideas(
    ideas: tuple[dict[str, Any], ...],
    *,
    repo_root: Path,
    as_of: datetime | None = None,
    corr: float | None = None,
) -> tuple[dict[str, Any], ...]:
    """Apply Principal cluster caps before publish. Does not invent corr or size math."""
    spec = load_monitor_spec(repo_root)
    net = spec.get("netting") if isinstance(spec.get("netting"), dict) else {}
    max_per_cluster = int(net.get("max_sized_per_cluster") or 1)
    max_per_round = int(net.get("max_sized_per_round") or 3)
    threshold = float(net.get("corr_threshold") or 0.65)
    out: list[dict[str, Any]] = []
    sized_by_cluster: dict[str, int] = {}
    sized_by_round: dict[str, int] = {}
    sized_clusters: set[str] = set()
    for raw in ideas:
        ticker = str(raw.get("instrument") or raw.get("ticker") or "")
        row = name_by_ticker(ticker, repo_root)
        item = dict(raw)
        if row is None:
            item["idea_eligible"] = False
            item["size_policy"] = "none"
            item["reason"] = "not on locked monitor"
            continue
        ok, reason = idea_eligible(
            row,
            as_of=as_of,
            repo_root=repo_root,
            horizon=raw.get("horizon") or raw.get("horizon_end"),
        )
        item["ticker"] = row.ticker
        item["tier"] = row.tier
        item["cluster"] = row.cluster
        item["round"] = row.round
        item["idea_eligible"] = ok
        item["reason"] = reason
        policy = idea_size_policy(row)
        item["size_policy"] = policy
        if not ok:
            continue
        sized = policy == "cluster_capped"
        if sized and row.cluster == "index_futures" and "semis_ai" in sized_clusters:
            if corr is None or float(corr) >= threshold:
                sized = False
                item["size_policy"] = "UNSIZED"
                item["reason"] = "index_futures nets semis_ai (corr fail-closed or >= threshold)"
        if sized and row.cluster == "semis_ai" and "index_futures" in sized_clusters:
            if corr is None or float(corr) >= threshold:
                sized = False
                item["size_policy"] = "UNSIZED"
                item["reason"] = "index_futures nets semis_ai (corr fail-closed or >= threshold)"
        if sized:
            if sized_by_cluster.get(row.cluster, 0) >= max_per_cluster:
                sized = False
                item["size_policy"] = "UNSIZED"
                item["reason"] = f"max {max_per_cluster} sized per cluster {row.cluster}"
            elif sized_by_round.get(row.round, 0) >= max_per_round:
                sized = False
                item["size_policy"] = "UNSIZED"
                item["reason"] = f"max {max_per_round} sized per round"
        if sized:
            sized_by_cluster[row.cluster] = sized_by_cluster.get(row.cluster, 0) + 1
            sized_by_round[row.round] = sized_by_round.get(row.round, 0) + 1
            sized_clusters.add(row.cluster)
        if policy == "UNSIZED" and "reason" in item and item["reason"] == UNSIZED_REASON:
            item["size_policy"] = "UNSIZED"
        out.append(item)
    return tuple(out)


def assert_monitor_invariants(repo_root: Path) -> None:
    spec = load_monitor_spec(repo_root)
    names = monitor_names(repo_root)
    tickers = [row.ticker for row in names]
    crypto = list((spec.get("rounds") or {}).get("crypto", {}).get("names") or [])
    base = list((spec.get("rounds") or {}).get("base", {}).get("names") or [])
    if tickers != crypto + base:
        raise ValueError("monitor names must match crypto then base round lists exactly")
    unresolved = {str(x) for x in (spec.get("unresolved") or ())}
    if unresolved != set(UNRESOLVED_TICKERS):
        raise ValueError(f"unresolved set must be {UNRESOLVED_TICKERS}; do not guess")
    for row in names:
        if row.ticker in unresolved:
            if row.resolution_status != RESOLUTION_UNRESOLVED or row.qualified_id is not None:
                raise ValueError(f"{row.ticker} must stay unresolved")
        elif row.resolution_status != RESOLUTION_RESOLVED or not row.qualified_id:
            raise ValueError(f"{row.ticker} must have an exchange-qualified id")
        if row.tier == TIER_UNIVERSE and row.membership != MEMBERSHIP_IN_UNIVERSE:
            raise ValueError(f"{row.ticker} universe tier without in_universe membership")
        if row.membership == MEMBERSHIP_IN_UNIVERSE and row.tier != TIER_UNIVERSE:
            raise ValueError(f"{row.ticker} in_universe must stay universe tier")
        if row.membership == MEMBERSHIP_DEFERRED and not row.archive:
            raise ValueError(f"{row.ticker} is deferred_must_cut and must be archive/monitor")
        if row.membership == MEMBERSHIP_WATCH_ONLY and row.tier == TIER_UNIVERSE:
            raise ValueError(f"{row.ticker} watch_only cannot be universe tier")
    for watch in lockup_watches(repo_root):
        if watch.assume_180d:
            raise ValueError(f"{watch.ticker} must not assume flat 180d")
        if not watch.confirmed:
            raise ValueError(f"{watch.ticker} lockup was Principal-confirmed")
    if spec.get("promote"):
        raise ValueError("promote must stay false")
