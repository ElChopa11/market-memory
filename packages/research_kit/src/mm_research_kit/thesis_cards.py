"""Dedicated Crypto / Equities thesis cards (IMP-007). Research-only.

Generic ``thesis.md`` remains the lifecycle spine. These cards are desk-specific
companions. Membership keys follow IMP-005; closed verdicts follow IMP-001.
Must not import execution or ingest private keys.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mm_common.naming import sleeve_display
from mm_research_kit.artifacts import copy_template, isoformat_now, write_text
from mm_research_kit.markdown import set_field
from mm_research_kit.quant_review.language import assert_language_clean
from mm_research_kit.quant_review.models import VERDICT_VALUES

# Pinned to config/universe.yaml version 2026-09-17. Tests fail if membership expands.
LOCKED_UNIVERSE_VERSION = "2026-09-17"
CRYPTO_PERPS = ("BTC", "ETH", "UNI", "AAVE")
EQUITIES = ("NVDA", "AVGO", "SMH", "MSFT", "META", "JPM", "XLF", "XOM")
IN_UNIVERSE_CRYPTO = ("BTC",)
IN_UNIVERSE_EQUITIES = ("NVDA", "AVGO", "MSFT", "META", "JPM", "XOM")
WATCH_ONLY_CRYPTO = ("ETH", "UNI", "AAVE")
WATCH_ONLY_EQUITIES = ("SMH", "XLF")
DEFERRED_CRYPTO = ("HYPE", "SOL", "XRP", "ARB", "NEAR", "LINK")
DEFERRED_EQUITIES = ("GLD", "LLY")

CRYPTO_CARD = "crypto-thesis-card.md"
EQUITIES_CARD = "equities-thesis-card.md"
MEMBERSHIP_IN_UNIVERSE = "in_universe"
MEMBERSHIP_WATCH_ONLY = "watch_only"
MEMBERSHIP_DEFERRED = "deferred_must_cut"
MEMBERSHIP_UNSET = "not_in_membership"
CLOSED_VERDICTS = VERDICT_VALUES


@dataclass(frozen=True)
class DeskCardPlan:
    template: str
    destination: str
    desk: str
    asset_class: str
    membership: str


def normalize_instrument(raw: str) -> str:
    token = (raw or "").strip().split()[0].split(",")[0].strip()
    return "".join(ch for ch in token.upper() if ch.isalnum())


def watchlist_tier_for(instrument: str, repo_root: Path | None = None) -> str:
    """Read Intel-owned monitor.yaml. Unset if the name is not on the review list."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[4]
    path = root / "config" / "watchlist" / "monitor.yaml"
    if not path.is_file():
        return "unset"
    try:
        import yaml
    except ImportError:
        return "unset"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return "unset"
    want = normalize_instrument(instrument)
    raw = instrument.strip().upper()
    for row in data.get("names") or []:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "")
        key = str(row.get("membership_key") or "")
        alias = str(row.get("tape_alias") or "")
        if want in {normalize_instrument(ticker), normalize_instrument(key), normalize_instrument(alias)} or raw == ticker.upper():
            return str(row.get("tier") or "monitor")
    return "unset"


def membership_for(instrument: str) -> str:
    inst = normalize_instrument(instrument)
    if inst in IN_UNIVERSE_CRYPTO or inst in IN_UNIVERSE_EQUITIES:
        return MEMBERSHIP_IN_UNIVERSE
    if inst in WATCH_ONLY_CRYPTO or inst in WATCH_ONLY_EQUITIES:
        return MEMBERSHIP_WATCH_ONLY
    if inst in DEFERRED_CRYPTO or inst in DEFERRED_EQUITIES:
        return MEMBERSHIP_DEFERRED
    return MEMBERSHIP_UNSET


def plan_desk_card(instrument: str) -> DeskCardPlan | None:
    inst = normalize_instrument(instrument)
    if inst in CRYPTO_PERPS or inst in DEFERRED_CRYPTO:
        return DeskCardPlan(
            template=CRYPTO_CARD,
            destination=CRYPTO_CARD,
            desk=sleeve_display("crypto"),
            asset_class="crypto_perp",
            membership=membership_for(inst),
        )
    if inst in EQUITIES or inst in DEFERRED_EQUITIES:
        return DeskCardPlan(
            template=EQUITIES_CARD,
            destination=EQUITIES_CARD,
            desk=sleeve_display("equities"),
            asset_class="equity",
            membership=membership_for(inst),
        )
    return None


def fill_thesis_card(
    text: str,
    *,
    slug: str,
    status: str,
    author_role: str,
    instrument: str,
    horizon: str,
    desk: str,
    asset_class: str,
    membership: str,
    knowledge_watermark: str,
) -> str:
    text = set_field(text, "Thesis id", slug)
    text = set_field(text, "Status / version", status)
    text = set_field(text, "Desk", desk)
    text = set_field(text, "Author role", author_role)
    text = set_field(text, "Instrument", instrument)
    text = set_field(text, "Asset class", asset_class)
    text = set_field(text, "Time horizon", horizon)
    text = set_field(text, "Principal membership", membership)
    text = set_field(text, "Watchlist tier", watchlist_tier_for(instrument))
    text = set_field(text, "Working Quant verdict", "unset")
    text = set_field(text, "Knowledge watermark (as_of_knowledge)", knowledge_watermark)
    text = set_field(text, "Independent Skeptic verdict", "pending (not claimed as pass)")
    return text


def attach_desk_thesis_card(
    *,
    workspace: Path,
    templates_root: Path,
    instrument: str,
    slug: str,
    status: str,
    author_role: str,
    horizon: str = "",
    opened_at: str = "",
    knowledge_watermark: str | None = None,
) -> Path | None:
    """Copy the matching desk card next to thesis.md. Skip if instrument is not in the locked set."""
    plan = plan_desk_card(instrument)
    if plan is None:
        return None
    dest = workspace / plan.destination
    text = fill_thesis_card(
        copy_template(templates_root, plan.template, dest),
        slug=slug,
        status=status,
        author_role=author_role,
        instrument=normalize_instrument(instrument) or instrument,
        horizon=horizon,
        desk=plan.desk,
        asset_class=plan.asset_class,
        membership=plan.membership,
        knowledge_watermark=knowledge_watermark or opened_at or isoformat_now(),
    )
    assert_language_clean(text)
    write_text(dest, text)
    return dest
