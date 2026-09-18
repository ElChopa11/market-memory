"""QuantCard construction + markdown render (factor layer)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from mm_common.hashing import canonical_json, sha256_hex
from mm_quant.config import QuantConfig
from mm_quant.factors import FactorRegistry, factors_hash
from mm_quant.language import assert_language_clean
from mm_quant.models import (
    CARD_FOOTER,
    ENGINE_VERSION,
    FactorValue,
    MarketPanel,
    OK,
    PARTIAL,
    ProvenanceRef,
    QuantCard,
    UNAVAILABLE,
)
from mm_quant.regime import classify_regime
from mm_quant.sizing import fixed_fractional_budget_pct, vol_targeted_budget_pct

TEMPLATE_REL = Path("templates/quant-factor-card.md")


def _quality(factors: tuple[FactorValue, ...]) -> str:
    statuses = {row.status for row in factors}
    if statuses == {OK}:
        return OK
    if UNAVAILABLE in statuses and OK not in statuses and PARTIAL not in statuses:
        return UNAVAILABLE
    if UNAVAILABLE in statuses or PARTIAL in statuses:
        return PARTIAL
    return OK


def _gaps(factors: tuple[FactorValue, ...]) -> tuple[str, ...]:
    out: list[str] = []
    for row in factors:
        if row.status == UNAVAILABLE:
            out.append(f"{row.name}: {row.reason or UNAVAILABLE}")
        elif row.status == PARTIAL:
            out.append(f"{row.name}: partial ({row.reason})")
    return tuple(out)


def _provenance(factors: tuple[FactorValue, ...]) -> tuple[ProvenanceRef, ...]:
    seen: set[tuple] = set()
    out: list[ProvenanceRef] = []
    for row in factors:
        for ref in row.provenance:
            key = (ref.observation_id, ref.fixture_id, ref.as_of_knowledge, ref.metric, ref.instrument)
            if key in seen:
                continue
            seen.add(key)
            out.append(ref)
    return tuple(out)


def build_quant_card(
    instrument: str,
    panel: MarketPanel,
    watermark: datetime,
    *,
    config: QuantConfig | None = None,
    registry: FactorRegistry | None = None,
) -> QuantCard:
    cfg = config or QuantConfig.defaults()
    reg = registry or FactorRegistry(cfg)
    factors = reg.compute_all(instrument, panel, watermark)
    regime = classify_regime(factors, watermark=watermark, config=cfg)
    by_name = {row.name: row for row in factors}
    vol = by_name["realised_vol_short"]
    vol_hint = vol_targeted_budget_pct(
        vol.value if vol.status != UNAVAILABLE else None,
        target_vol=cfg.sizing.vol_target,
        base_fraction=cfg.sizing.vol_target_base_fraction,
        cap_pct=cfg.sizing.cap_pct,
        as_of_knowledge=watermark,
        provenance=vol.provenance,
    )
    frac_hint = fixed_fractional_budget_pct(
        cfg.sizing.fixed_fraction,
        cap_pct=cfg.sizing.cap_pct,
        as_of_knowledge=watermark,
        provenance=(),
    )
    digest = factors_hash(factors, config_version=cfg.version, watermark=watermark)
    params = sha256_hex(
        canonical_json(
            {
                "engine": ENGINE_VERSION,
                "config_version": cfg.version,
                "regime_version": cfg.regime.version,
                "instrument": instrument.upper(),
                "watermark": watermark.isoformat(),
                "factors_hash": digest,
            }
        )
    )
    card = QuantCard(
        instrument=instrument.upper(),
        as_of_knowledge=watermark,
        config_version=cfg.version,
        params_hash=params,
        data_quality=_quality(factors),
        factors=factors,
        regime=regime,
        sizing_hints=(vol_hint, frac_hint),
        gaps=_gaps(factors),
        provenance=_provenance(factors),
    )
    return card


def _fmt_num(value: float | None) -> str:
    if value is None:
        return UNAVAILABLE
    text = f"{value:.8g}"
    return text


def _prov_cell(row: FactorValue) -> str:
    if not row.provenance:
        return "none"
    bits: list[str] = []
    for ref in row.provenance[:3]:
        oid = ref.observation_id or "—"
        fid = ref.fixture_id or "—"
        bits.append(f"{oid}/{fid}@{ref.as_of_knowledge}")
    return "; ".join(bits)


def render_quant_card(card: QuantCard) -> str:
    factor_rows = "\n".join(
        f"| {row.name} | {row.status} | {_fmt_num(row.value)} | {row.unit or '—'} | "
        f"{row.window if row.window is not None else '—'} | {_prov_cell(row)} | {row.reason.replace('|', '/')} |"
        for row in card.factors
    )
    hint_rows = "\n".join(
        f"| {hint.method} | {hint.status} | {_fmt_num(hint.budget_fraction_pct)} | {hint.reason.replace('|', '/')} |"
        for hint in card.sizing_hints
    )
    gap_lines = "\n".join(f"- {gap}" for gap in card.gaps) or "- none"
    driving = card.regime.driving_inputs
    thresholds = driving.get("thresholds") if isinstance(driving, dict) else {}
    lines = [
        f"# Quant factor card — {card.instrument}",
        "",
        f"- **Instrument:** {card.instrument}",
        f"- **Knowledge watermark (as_of_knowledge):** {card.as_of_knowledge.isoformat()}",
        f"- **Config version:** {card.config_version}",
        f"- **Engine:** {card.engine_version}",
        f"- **params_hash:** `{card.params_hash}`",
        f"- **result_hash:** `{card.result_hash()}`",
        f"- **Data-quality status:** {card.data_quality}",
        f"- **Regime tag:** `{card.regime.tag}`",
        f"- **Regime confidence (0–1 coverage/sharpness; not a conviction label):** {_fmt_num(card.regime.confidence)}",
        f"- **Regime thresholds version:** {card.regime.thresholds_version}",
        f"- **Driving inputs:** vol={driving.get('realised_vol_short') if isinstance(driving, dict) else '—'}; "
        f"adx={driving.get('adx') if isinstance(driving, dict) else '—'}; "
        f"zscore={driving.get('zscore') if isinstance(driving, dict) else '—'}; "
        f"funding={driving.get('funding_carry') if isinstance(driving, dict) else '—'}",
        f"- **Thresholds (YAML):** {thresholds}",
        "",
        "## Factors",
        "",
        "| name | status | value | unit | window | provenance (observation/fixture@as_of_knowledge) | reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        factor_rows,
        "",
        "## Intent-level budget fraction",
        "",
        "Research helper only. `% of research budget`. Not an order, not a fill, not Execution.",
        "",
        "| method | status | budget_fraction_pct | reason |",
        "| --- | --- | --- | --- |",
        hint_rows,
        "",
        "## Data gaps",
        "",
        gap_lines,
        "",
        card.footer,
        "",
    ]
    text = "\n".join(lines)
    assert_language_clean(text)
    return text


def template_path(root: Path) -> Path:
    return root / TEMPLATE_REL
