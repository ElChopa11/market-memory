"""PIT-safe flow metrics from HL structure + equity/crypto tape. Degrade, never invent."""

from __future__ import annotations

import math
from datetime import datetime

from mm_common.time import as_utc
from mm_flow.config import FlowConfig
from mm_flow.models import (
    OK,
    PARTIAL,
    UNAVAILABLE,
    ClipSlippage,
    MetricValue,
)
from mm_flow.series import latest_point, points_for, visible_closes
from mm_flow.verdict import estimate_adv_slippage_bps, estimate_book_slippage_bps
from mm_quant.models import MarketPanel, ProvenanceRef, SeriesBar, StructurePoint

FUNDING_METRICS = ("funding",)
OI_METRICS = ("open_interest", "oi", "openInterest")
BASIS_METRICS = ("basis_mark_oracle", "basis_perp_spot")
SPREAD_METRICS = ("l2_spread",)
BID_NOTIONAL_METRICS = ("l2_bid_notional",)
ASK_NOTIONAL_METRICS = ("l2_ask_notional",)
MID_METRICS = ("l2_mid", "mark_px", "mid_px")


def _zscore(values: tuple[float, ...], window: int) -> float | None:
    if window < 2 or len(values) < window:
        return None
    sl = values[-window:]
    mean = sum(sl) / window
    var = sum((x - mean) ** 2 for x in sl) / (window - 1)
    if var <= 0:
        return None
    return (sl[-1] - mean) / math.sqrt(var)


def _refs(point: StructurePoint | SeriesBar | None, *, metric: str) -> tuple[ProvenanceRef, ...]:
    if point is None:
        return ()
    if isinstance(point, SeriesBar):
        return (point.provenance(),)
    return (
        ProvenanceRef(
            as_of_knowledge=as_utc(point.as_of_knowledge).isoformat(),
            observation_id=point.observation_id,
            fixture_id=point.fixture_id,
            instrument=point.instrument,
            metric=metric,
        ),
    )


def _unavailable(name: str, watermark: datetime, reason: str) -> MetricValue:
    return MetricValue(
        name=name,
        status=UNAVAILABLE,
        as_of_knowledge=watermark,
        reason=reason,
    )


def funding_z(panel: MarketPanel, instrument: str, watermark: datetime, config: FlowConfig) -> MetricValue:
    rows = points_for(panel, instrument, FUNDING_METRICS, watermark)
    values = tuple(float(row.value) for row in rows if row.value is not None)
    z = _zscore(values, config.funding_z_window)
    if z is None:
        return _unavailable(
            "funding_z",
            watermark,
            f"need {config.funding_z_window} funding prints; have {len(values)} (not invented)",
        )
    return MetricValue(
        name="funding_z",
        status=OK,
        as_of_knowledge=watermark,
        value=z,
        unit="z",
        payload={"n": len(values[-config.funding_z_window :]), "window": config.funding_z_window, "last": values[-1]},
        provenance=_refs(rows[-1], metric="funding"),
        reason="sample z-score of last funding vs YAML window",
    )


def oi_delta(panel: MarketPanel, instrument: str, watermark: datetime, config: FlowConfig) -> MetricValue:
    rows = points_for(panel, instrument, OI_METRICS, watermark)
    if len(rows) < config.oi_lookback + 1:
        return _unavailable(
            "oi_delta",
            watermark,
            f"need {config.oi_lookback + 1} OI prints; have {len(rows)} (not invented)",
        )
    last = rows[-1]
    prev = rows[-1 - config.oi_lookback]
    if last.value is None or prev.value is None:
        return _unavailable("oi_delta", watermark, "OI value missing (not invented)")
    delta = float(last.value) - float(prev.value)
    pct = delta / float(prev.value) if prev.value else None
    return MetricValue(
        name="oi_delta",
        status=OK,
        as_of_knowledge=watermark,
        value=delta,
        unit="contracts",
        payload={"pct": pct, "last": last.value, "prev": prev.value},
        provenance=_refs(last, metric=last.metric) + _refs(prev, metric=prev.metric),
        reason="last minus lookback OI",
    )


def basis(panel: MarketPanel, instrument: str, watermark: datetime) -> MetricValue:
    point = latest_point(panel, instrument, BASIS_METRICS, watermark)
    if point is None or point.value is None:
        return _unavailable("basis", watermark, "basis_mark_oracle / basis_perp_spot missing (not invented)")
    return MetricValue(
        name="basis",
        status=OK,
        as_of_knowledge=watermark,
        value=float(point.value),
        unit="fraction",
        payload={"metric": point.metric},
        provenance=_refs(point, metric=point.metric),
        reason="latest visible basis",
    )


def spread_proxy(panel: MarketPanel, instrument: str, watermark: datetime) -> MetricValue:
    point = latest_point(panel, instrument, SPREAD_METRICS, watermark)
    mid = latest_point(panel, instrument, MID_METRICS, watermark)
    if point is None or point.value is None:
        return _unavailable("spread_bps", watermark, "l2_spread missing (not invented)")
    spread = float(point.value)
    mid_px = float(mid.value) if mid is not None and mid.value not in (None, 0) else None
    bps = (spread / mid_px) * 10_000.0 if mid_px else None
    status = OK if bps is not None else PARTIAL
    return MetricValue(
        name="spread_bps",
        status=status,
        as_of_knowledge=watermark,
        value=bps if bps is not None else spread,
        unit="bps" if bps is not None else "px",
        payload={"spread_px": spread, "mid": mid_px, "spread_bps": bps},
        provenance=_refs(point, metric="l2_spread") + _refs(mid, metric="l2_mid"),
        reason="spread / mid * 1e4 when mid exists, else raw spread px",
    )


def depth_usd(panel: MarketPanel, instrument: str, watermark: datetime) -> MetricValue:
    bid = latest_point(panel, instrument, BID_NOTIONAL_METRICS, watermark)
    ask = latest_point(panel, instrument, ASK_NOTIONAL_METRICS, watermark)
    if bid is None or ask is None or bid.value is None or ask.value is None:
        return _unavailable("depth_usd", watermark, "l2 bid/ask notional missing (not invented)")
    total = float(bid.value) + float(ask.value)
    return MetricValue(
        name="depth_usd",
        status=OK,
        as_of_knowledge=watermark,
        value=total,
        unit="usd",
        payload={"bid": bid.value, "ask": ask.value},
        provenance=_refs(bid, metric="l2_bid_notional") + _refs(ask, metric="l2_ask_notional"),
        reason="top-of-book bid+ask notional",
    )


def adv_turnover(panel: MarketPanel, instrument: str, watermark: datetime, config: FlowConfig) -> MetricValue:
    bars = visible_closes(panel, instrument, watermark)
    window = config.adv_window
    if len(bars) < window:
        return _unavailable(
            "adv_notional",
            watermark,
            f"need {window} volume bars; have {len(bars)} (not invented)",
        )
    notionals: list[float] = []
    for bar in bars[-window:]:
        if bar.volume is None:
            continue
        notionals.append(float(bar.volume) * float(bar.close))
    if len(notionals) < window:
        return _unavailable(
            "adv_notional",
            watermark,
            f"need {window} volume*close bars; have {len(notionals)} (not invented)",
        )
    adv = sum(notionals) / len(notionals)
    last = notionals[-1]
    turnover = last / adv if adv else None
    return MetricValue(
        name="adv_notional",
        status=OK,
        as_of_knowledge=watermark,
        value=adv,
        unit="usd",
        payload={"turnover": turnover, "window": window, "last_notional": last},
        provenance=_refs(bars[-1], metric="ohlcv_close"),
        reason="mean volume*close over YAML window",
    )


def clip_estimates(
    *,
    spread: MetricValue,
    depth: MetricValue,
    adv: MetricValue,
    config: FlowConfig,
) -> tuple[ClipSlippage, ...]:
    spread_bps = None
    if spread.status in {OK, PARTIAL} and spread.payload.get("spread_bps") is not None:
        spread_bps = float(spread.payload["spread_bps"])
    elif spread.status == OK and spread.unit == "bps" and spread.value is not None:
        spread_bps = float(spread.value)
    depth_val = depth.value if depth.status == OK else None
    adv_val = adv.value if adv.status == OK else None
    out: list[ClipSlippage] = []
    for clip in config.clip_sizes_usd:
        if spread_bps is not None and depth_val is not None:
            bps = estimate_book_slippage_bps(
                clip,
                spread_bps=spread_bps,
                depth_usd=depth_val,
                impact_coeff=config.slippage.impact_coeff,
            )
            out.append(
                ClipSlippage(
                    clip_usd=clip,
                    slippage_bps=bps,
                    status=OK if bps is not None else UNAVAILABLE,
                    method="book",
                    reason="half-spread + clip/depth impact",
                )
            )
            continue
        if adv_val is not None:
            bps = estimate_adv_slippage_bps(clip, adv_notional=adv_val, adv_k=config.slippage.adv_k)
            out.append(
                ClipSlippage(
                    clip_usd=clip,
                    slippage_bps=bps,
                    status=OK if bps is not None else UNAVAILABLE,
                    method="adv",
                    reason="k * sqrt(clip/ADV) bps proxy (no L2)",
                )
            )
            continue
        out.append(
            ClipSlippage(
                clip_usd=clip,
                slippage_bps=None,
                status=UNAVAILABLE,
                method="none",
                reason="no book or ADV (not invented)",
            )
        )
    return tuple(out)
