"""OK | THIN | UNTRADEABLE_AT_SIZE from slippage at configured clips. Never invent depth."""

from __future__ import annotations

from datetime import datetime

from mm_flow.config import FlowConfig
from mm_flow.models import (
    VERDICT_OK,
    VERDICT_THIN,
    VERDICT_UNAVAILABLE,
    VERDICT_UNTRADEABLE,
    ClipSlippage,
    LiquidityVerdict,
    OK,
    UNAVAILABLE,
)

VERDICT_OK = VERDICT_OK
VERDICT_THIN = VERDICT_THIN
VERDICT_UNTRADEABLE = VERDICT_UNTRADEABLE
VERDICT_UNAVAILABLE = VERDICT_UNAVAILABLE


def estimate_book_slippage_bps(
    clip_usd: float,
    *,
    spread_bps: float,
    depth_usd: float,
    impact_coeff: float,
) -> float | None:
    if clip_usd <= 0 or depth_usd <= 0 or spread_bps < 0:
        return None
    impact = (clip_usd / depth_usd) * 10_000.0 * impact_coeff
    return spread_bps / 2.0 + impact


def estimate_adv_slippage_bps(
    clip_usd: float,
    *,
    adv_notional: float,
    adv_k: float,
) -> float | None:
    if clip_usd <= 0 or adv_notional <= 0 or adv_k <= 0:
        return None
    return adv_k * ((clip_usd / adv_notional) ** 0.5) * 10_000.0


def classify_verdict(
    clips: tuple[ClipSlippage, ...],
    *,
    watermark: datetime,
    config: FlowConfig,
) -> LiquidityVerdict:
    budget = config.slippage.budget_bps
    feasible = [row for row in clips if row.status == OK and row.slippage_bps is not None and row.slippage_bps <= budget]
    attempted = [row for row in clips if row.status == OK and row.slippage_bps is not None]
    max_clip = max((row.clip_usd for row in feasible), default=None)
    if not attempted:
        return LiquidityVerdict(
            verdict=VERDICT_UNAVAILABLE,
            as_of_knowledge=watermark,
            status=UNAVAILABLE,
            max_clip_usd=None,
            slippage_budget_bps=budget,
            clips=clips,
            reason="no slippage estimate; book and ADV unavailable (not invented)",
            thresholds_version=config.version,
        )
    if max_clip is None:
        return LiquidityVerdict(
            verdict=VERDICT_UNTRADEABLE,
            as_of_knowledge=watermark,
            status=OK,
            max_clip_usd=None,
            slippage_budget_bps=budget,
            clips=clips,
            reason="every configured clip exceeds slippage budget",
            thresholds_version=config.version,
        )
    ref = None
    for row in clips:
        if row.status == OK and row.slippage_bps is not None and abs(row.clip_usd - config.thin_max_clip_usd) < 1e-9:
            ref = row.slippage_bps
            break
    if ref is None and feasible:
        ref = feasible[-1].slippage_bps
    thin = max_clip < config.thin_max_clip_usd or (ref is not None and ref > config.slippage.thin_bps)
    if thin:
        return LiquidityVerdict(
            verdict=VERDICT_THIN,
            as_of_knowledge=watermark,
            status=OK,
            max_clip_usd=max_clip,
            slippage_budget_bps=budget,
            clips=clips,
            reason="max clip under budget is thin vs YAML thin_max_clip_usd / thin_bps",
            thresholds_version=config.version,
        )
    return LiquidityVerdict(
        verdict=VERDICT_OK,
        as_of_knowledge=watermark,
        status=OK,
        max_clip_usd=max_clip,
        slippage_budget_bps=budget,
        clips=clips,
        reason="largest configured clip under slippage budget",
        thresholds_version=config.version,
    )
