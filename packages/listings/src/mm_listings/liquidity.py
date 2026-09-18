"""Listings liquidity verdict. Reuses mm_flow clip/slippage math. Never invents depth."""

from __future__ import annotations

from datetime import datetime

from mm_common.time import as_utc
from mm_flow.config import FlowConfig, load_flow_config
from mm_flow.metrics import clip_estimates
from mm_flow.models import OK, UNAVAILABLE, MetricValue
from mm_flow.verdict import VERDICT_UNAVAILABLE, VERDICT_UNTRADEABLE, classify_verdict
from mm_listings.models import ListingDeal


def _metric(name: str, value: float | None, watermark: datetime) -> MetricValue:
    if value is None:
        return MetricValue(
            name=name,
            status=UNAVAILABLE,
            as_of_knowledge=watermark,
            value=None,
            reason=f"{name} unavailable (not invented)",
        )
    unit = "bps" if name == "spread_bps" else ("usd" if name in {"depth_usd", "adv_notional"} else "")
    return MetricValue(name=name, status=OK, as_of_knowledge=watermark, value=float(value), unit=unit)


def listings_liquidity_verdict(
    deal: ListingDeal,
    watermark: datetime,
    *,
    flow_config: FlowConfig | None = None,
    repo_root=None,
) -> str:
    cfg = flow_config or load_flow_config(repo_root)
    cut = as_utc(watermark)
    spread = _metric("spread_bps", deal.spread_bps, cut)
    depth = _metric("depth_usd", deal.depth_usd, cut)
    adv = _metric("adv_notional", deal.adv_notional, cut)
    clips = clip_estimates(spread=spread, depth=depth, adv=adv, config=cfg)
    verdict = classify_verdict(clips, watermark=cut, config=cfg)
    if verdict.verdict == VERDICT_UNAVAILABLE:
        return VERDICT_UNAVAILABLE
    if verdict.verdict == VERDICT_UNTRADEABLE:
        return VERDICT_UNTRADEABLE
    return verdict.verdict
