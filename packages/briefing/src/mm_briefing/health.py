"""Stage A data-health score. Coverage of observed states, not a confidence bar.

A structural miss (VIX entitlement) is listed on the price row and excluded
from the denominator. Icons are data state only. If nothing is scored, the
morning renderer omits the line. It does not print INSUFFICIENT DATA.
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


@dataclass(frozen=True)
class DomainHealth:
    id: str
    label: str
    state: str
    excluded: bool
    detail: str


@dataclass(frozen=True)
class HealthReport:
    version: str
    domains: tuple[DomainHealth, ...]
    pct: int | None
    scored: int
    structural_excluded: tuple[str, ...]
    insufficient: bool

    def morning_line(self, *, icons: dict[str, str]) -> str | None:
        """One varying coverage line. Omitted when nothing is scored.

        Structural domains stay off this line (they do not change). The
        percentage and the states that can move are the information.
        """
        if self.insufficient or self.pct is None:
            return None
        parts: list[str] = []
        for row in self.domains:
            if row.excluded:
                continue
            icon = icons.get(row.state, "")
            prefix = f"{icon} " if icon else ""
            parts.append(f"{row.label} {prefix}{row.state}".strip())
        if not parts:
            return None
        return f"Data health: {self.pct}% | " + " | ".join(parts)


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
            scored=0,
            structural_excluded=structural,
            insufficient=True,
        )
    weight_sum = 0.0
    for row in scored:
        weight_sum += float(cfg.weights.get(row.state, 0.0))
    pct = int(round(100.0 * weight_sum / len(scored)))
    return HealthReport(
        version=cfg.version,
        domains=tuple(domains),
        pct=pct,
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
        return DomainHealth(spec.id, spec.label, "unavailable", True, names)
    active = [row for row in rows if not row.structural_unavailable]
    missing = [sym for sym in spec.symbols if sym not in by_symbol]
    if not active and not missing:
        return DomainHealth(spec.id, spec.label, "unavailable", True, spec.label)
    states: list[str] = [pulse_to_health_state(row.data_quality) for row in active]
    states.extend("unavailable" for _ in missing)
    return DomainHealth(spec.id, spec.label, worst_health_state(states), False, "")


def _hl_domain(spec: DomainSpec, hl: tuple[HLInstrumentState, ...]) -> DomainHealth:
    if not hl:
        return DomainHealth(spec.id, spec.label, "unavailable", False, "")
    states = [pulse_to_health_state(state.data_quality) for state in hl]
    return DomainHealth(spec.id, spec.label, worst_health_state(states), False, "")
