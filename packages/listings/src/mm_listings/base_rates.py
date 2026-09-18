"""Base rates from our own Market Memory listing history. Never invent a cohort."""

from __future__ import annotations

from datetime import datetime
from statistics import median

from mm_listings.config import ListingsConfig
from mm_listings.models import BaseRateSummary, ListingOutcome
from mm_listings.series import visible_outcomes

NO_CLAIM_REASON = "n below configured minimum; no base-rate claim"


def compute_base_rates(
    history: tuple[ListingOutcome, ...],
    watermark: datetime,
    *,
    config: ListingsConfig,
) -> BaseRateSummary:
    visible = visible_outcomes(history, watermark)
    n = len(visible)
    if n < int(config.n_min):
        return BaseRateSummary(
            n=n,
            n_min=int(config.n_min),
            claimed=False,
            median_30d=None,
            reclaim_hit_rate=None,
            reason=NO_CLAIM_REASON,
        )
    rets = [row.ret_30d for row in visible if row.ret_30d is not None]
    reclaim_flags = [row.reclaimed_offer for row in visible if row.reclaimed_offer is not None]
    if not rets:
        return BaseRateSummary(
            n=n,
            n_min=int(config.n_min),
            claimed=False,
            median_30d=None,
            reclaim_hit_rate=None,
            reason="history rows lack 30d returns; no base-rate claim",
        )
    hit = None
    if reclaim_flags:
        hit = sum(1 for flag in reclaim_flags if flag) / len(reclaim_flags)
    return BaseRateSummary(
        n=n,
        n_min=int(config.n_min),
        claimed=True,
        median_30d=float(median(rets)),
        reclaim_hit_rate=hit,
        reason=f"own-history n={n} (min {config.n_min})",
    )
