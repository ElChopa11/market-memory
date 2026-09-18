"""Compute a PIT flow snapshot + liquidity verdict. Degrade, never invent."""

from __future__ import annotations

from datetime import datetime

from mm_common.time import as_utc
from mm_flow.config import FlowConfig, load_flow_config
from mm_flow.metrics import adv_turnover, basis, clip_estimates, depth_usd, funding_z, oi_delta, spread_proxy
from mm_flow.models import OK, PARTIAL, UNAVAILABLE, FlowSnapshot, MetricValue
from mm_flow.verdict import classify_verdict
from mm_quant.models import MarketPanel, ProvenanceRef


def _quality(metrics: tuple[MetricValue, ...]) -> str:
    statuses = {row.status for row in metrics}
    if statuses == {UNAVAILABLE}:
        return UNAVAILABLE
    if UNAVAILABLE in statuses or PARTIAL in statuses:
        return PARTIAL
    return OK


def compute_flow(
    instrument: str,
    panel: MarketPanel,
    watermark: datetime,
    *,
    config: FlowConfig | None = None,
    repo_root=None,
) -> FlowSnapshot:
    cfg = config or load_flow_config(repo_root)
    cut = as_utc(watermark)
    name = instrument.upper()
    rows = (
        funding_z(panel, name, cut, cfg),
        oi_delta(panel, name, cut, cfg),
        basis(panel, name, cut),
        spread_proxy(panel, name, cut),
        depth_usd(panel, name, cut),
        adv_turnover(panel, name, cut, cfg),
    )
    by_name = {row.name: row for row in rows}
    clips = clip_estimates(spread=by_name["spread_bps"], depth=by_name["depth_usd"], adv=by_name["adv_notional"], config=cfg)
    verdict = classify_verdict(clips, watermark=cut, config=cfg)
    gaps = tuple(row.name for row in rows if row.status != OK)
    provenance: list[ProvenanceRef] = []
    for row in rows:
        provenance.extend(row.provenance)
    return FlowSnapshot(
        instrument=name,
        as_of_knowledge=cut,
        config_version=cfg.version,
        data_quality=_quality(rows),
        metrics=rows,
        verdict=verdict,
        gaps=gaps,
        provenance=tuple(provenance),
    )
