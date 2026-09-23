"""Stage A data-health score. Coverage of observed states, not a confidence bar.

Replaces the worst-slot header rollup. A structural miss (VIX entitlement)
is listed and excluded from the denominator so it cannot stamp the brief
``unavailable``. Icons are data state only. Green is not a direction.

Only do this if the methodology is fully defined and the historical data is
actually stored. Otherwise you create fake precision. This score uses states
that are already on the prints. It does not invent regime, precision, or a
confidence percentage. If nothing is scored, the panel says INSUFFICIENT DATA.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mm_briefing.config import load_yaml, repo_root
from mm_briefing.models import AssetPrint, HLInstrumentState, pulse_quality

HEALTH_STATES = ("fresh", "degraded", "stale", "unavailable")
CARD_ORDER = (
    "executive",
    "dashboard",
    "macro",
    "crypto",
    "positioning",
    "catalysts",
    "scenarios",
    "audit",
)
INSUFFICIENT_DATA = "INSUFFICIENT DATA"
STRUCTURAL_NOTE = "structural (entitlement; not a Neon gap)"

_DEFAULT_ICONS = {
    "fresh": "🟢",
    "degraded": "🟡",
    "stale": "🟠",
    "unavailable": "⚪",
}
_DEFAULT_WEIGHTS = {
    "fresh": 1.0,
    "degraded": 0.5,
    "stale": 0.0,
    "unavailable": 0.0,
}
_STATE_RANK = {name: index for index, name in enumerate(HEALTH_STATES)}


@dataclass(frozen=True)
class DomainSpec:
    id: str
    label: str
    symbols: tuple[str, ...] = ()
    from_hl: bool = False


@dataclass(frozen=True)
class PresentationConfig:
    version: str
    card_order: tuple[str, ...]
    icons: dict[str, str]
    weights: dict[str, float]
    domains: tuple[DomainSpec, ...]
    insufficient_data: str = INSUFFICIENT_DATA


@dataclass(frozen=True)
class DomainHealth:
    id: str
    label: str
    state: str
    excluded: bool
    detail: str

    @property
    def icon(self) -> str:
        return _DEFAULT_ICONS.get(self.state, "")


@dataclass(frozen=True)
class HealthReport:
    version: str
    domains: tuple[DomainHealth, ...]
    pct: int | None
    fresh: int
    degraded: int
    stale: int
    unavailable: int
    scored: int
    structural_excluded: tuple[str, ...]
    insufficient: bool

    def header_lines(self, *, icons: dict[str, str]) -> list[str]:
        note = (
            "Icons mark data state only (fresh / degraded / stale / unavailable). "
            "Green is not a direction."
        )
        regime = "Regime: INSUFFICIENT DATA"
        if self.insufficient or self.pct is None:
            return [
                "Data health: INSUFFICIENT DATA",
                note,
                regime,
            ]
        excluded = ", ".join(self.structural_excluded) if self.structural_excluded else "none"
        summary = (
            f"{self.fresh} fresh, {self.degraded} degraded, {self.stale} stale, "
            f"{self.unavailable} unavailable / {self.scored} scored; "
            f"structural excluded: {excluded}"
        )
        return [
            f"Data health: {self.pct}% ({summary})",
            "Coverage of observed data states with versioned weights. Not a confidence score.",
            note,
            regime,
        ]

    def section_lines(self, *, icons: dict[str, str]) -> list[str]:
        lines = [
            "## Data health",
            "",
            "Per-domain state. Icons are data state only, never direction.",
            "",
            "| Domain | State | Detail |",
            "|---|---|---|",
        ]
        if not self.domains:
            lines.append(f"| — | {INSUFFICIENT_DATA} | no scored inputs |")
            return lines
        for row in self.domains:
            icon = icons.get(row.state, "")
            lines.append(f"| {row.label} | {icon} {row.state} | {row.detail} |")
        return lines


def default_presentation_config() -> PresentationConfig:
    return PresentationConfig(
        version="brief-v2-stage-a",
        card_order=CARD_ORDER,
        icons=dict(_DEFAULT_ICONS),
        weights=dict(_DEFAULT_WEIGHTS),
        domains=(
            DomainSpec("equities", "Equities", ("ES", "NQ")),
            DomainSpec("rates", "Rates", ("US10Y",)),
            DomainSpec("usd", "USD", ("DXY",)),
            DomainSpec("oil", "Oil", ("CL",)),
            DomainSpec("vol", "Vol", ("VIX",)),
            DomainSpec("crypto", "Crypto", ("BTC", "ETH")),
            DomainSpec("hyperliquid", "Hyperliquid", from_hl=True),
        ),
    )


def load_presentation_config(root: Path | None = None) -> PresentationConfig:
    path = (root or repo_root()) / "config" / "briefing" / "presentation.yaml"
    raw = load_yaml(path)
    if not raw:
        return default_presentation_config()
    return _parse_presentation(raw)


def _parse_presentation(raw: dict[str, Any]) -> PresentationConfig:
    base = default_presentation_config()
    icons = dict(base.icons)
    weights = dict(base.weights)
    states = raw.get("states")
    if isinstance(states, dict):
        for name, spec in states.items():
            key = str(name).strip().lower()
            if key not in _STATE_RANK or not isinstance(spec, dict):
                continue
            if spec.get("icon"):
                icons[key] = str(spec["icon"])
            if spec.get("weight") is not None:
                weights[key] = float(spec["weight"])
    order_raw = raw.get("card_order")
    if isinstance(order_raw, list) and order_raw:
        order = tuple(str(item).strip() for item in order_raw if str(item).strip())
    else:
        order = base.card_order
    domains: list[DomainSpec] = []
    raw_domains = raw.get("domains")
    if isinstance(raw_domains, list):
        for item in raw_domains:
            if not isinstance(item, dict):
                continue
            symbols = tuple(str(sym).upper() for sym in (item.get("symbols") or []))
            domains.append(
                DomainSpec(
                    id=str(item.get("id") or "").strip(),
                    label=str(item.get("label") or item.get("id") or "").strip(),
                    symbols=symbols,
                    from_hl=str(item.get("from") or "").strip().lower() == "hl",
                )
            )
    return PresentationConfig(
        version=str(raw.get("version") or base.version),
        card_order=order,
        icons=icons,
        weights=weights,
        domains=tuple(domains) if domains else base.domains,
        insufficient_data=str(raw.get("insufficient_data") or INSUFFICIENT_DATA),
    )


def pulse_to_health_state(quality: str | None) -> str:
    """Map pulse quality onto the four data-state labels. Partial → degraded."""
    label = pulse_quality(quality)
    if label == "partial":
        return "degraded"
    if label in _STATE_RANK:
        return label
    return "degraded"


def worst_health_state(states: list[str]) -> str:
    if not states:
        return "unavailable"
    return max(states, key=lambda name: _STATE_RANK.get(name, 1))


def score_data_health(
    assets: tuple[AssetPrint, ...] | list[AssetPrint],
    hl: tuple[HLInstrumentState, ...] | list[HLInstrumentState] = (),
    *,
    config: PresentationConfig | None = None,
) -> HealthReport:
    """Coverage rollup. Structural-unavailable prints do not enter the denominator."""
    cfg = config or load_presentation_config()
    by_symbol = {row.symbol.upper(): row for row in assets}
    domains: list[DomainHealth] = []
    for spec in cfg.domains:
        if spec.from_hl:
            domains.append(_hl_domain(spec, tuple(hl)))
        else:
            domains.append(_symbol_domain(spec, by_symbol))
    scored = [row for row in domains if not row.excluded]
    structural = tuple(row.label for row in domains if row.excluded)
    if not scored:
        return HealthReport(
            version=cfg.version,
            domains=tuple(domains),
            pct=None,
            fresh=0,
            degraded=0,
            stale=0,
            unavailable=0,
            scored=0,
            structural_excluded=structural,
            insufficient=True,
        )
    counts = {name: 0 for name in HEALTH_STATES}
    weight_sum = 0.0
    for row in scored:
        counts[row.state] = counts.get(row.state, 0) + 1
        weight_sum += float(cfg.weights.get(row.state, 0.0))
    pct = int(round(100.0 * weight_sum / len(scored)))
    return HealthReport(
        version=cfg.version,
        domains=tuple(domains),
        pct=pct,
        fresh=counts["fresh"],
        degraded=counts["degraded"],
        stale=counts["stale"],
        unavailable=counts["unavailable"],
        scored=len(scored),
        structural_excluded=structural,
        insufficient=False,
    )


def _symbol_domain(spec: DomainSpec, by_symbol: dict[str, AssetPrint]) -> DomainHealth:
    if not spec.symbols:
        return DomainHealth(spec.id, spec.label, "unavailable", False, "no symbols configured")
    rows = [by_symbol[sym] for sym in spec.symbols if sym in by_symbol]
    if rows and all(row.structural_unavailable for row in rows):
        names = ", ".join(row.symbol for row in rows)
        return DomainHealth(spec.id, spec.label, "unavailable", True, f"{names} {STRUCTURAL_NOTE}")
    active = [row for row in rows if not row.structural_unavailable]
    missing = [sym for sym in spec.symbols if sym not in by_symbol]
    if not active and not missing:
        return DomainHealth(spec.id, spec.label, "unavailable", True, STRUCTURAL_NOTE)
    states: list[str] = [pulse_to_health_state(row.data_quality) for row in active]
    states.extend("unavailable" for _ in missing)
    detail_bits: list[str] = []
    for row in active:
        shown = (row.quoted_symbol or row.symbol).strip()
        if row.quoted_symbol and row.quoted_symbol.upper() != row.symbol.upper():
            detail_bits.append(f"{shown} (slot {row.symbol})")
        else:
            detail_bits.append(shown)
    detail_bits.extend(f"{sym} missing" for sym in missing)
    return DomainHealth(
        spec.id,
        spec.label,
        worst_health_state(states),
        False,
        ", ".join(detail_bits) if detail_bits else "n/a",
    )


def _hl_domain(spec: DomainSpec, hl: tuple[HLInstrumentState, ...]) -> DomainHealth:
    if not hl:
        return DomainHealth(spec.id, spec.label, "unavailable", False, "no observations")
    states = [pulse_to_health_state(state.data_quality) for state in hl]
    detail = ", ".join(f"{state.instrument} {pulse_to_health_state(state.data_quality)}" for state in hl)
    return DomainHealth(spec.id, spec.label, worst_health_state(states), False, detail)
