"""Adapter licence_verdict (Principal 2026-09-19).

Standing rule: sources whose terms prohibit redistribution may be used
for internal computation but values must never appear in published artifacts.

Verdicts live next to each adapter in ``config/ingest.yaml``, not only in docs.
Unknown / missing verdicts fail closed (no published value).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from mm_ingest.config import load_ingest_settings, load_yaml, repo_root

STANDING_RULE = (
    "Sources whose terms prohibit redistribution may be used for internal "
    "computation but values must never appear in published artifacts."
)

VERDICT_OK_GOV = "ok_gov"
VERDICT_OK_ATTR = "ok_attr"
VERDICT_RESTRICTED = "restricted"
VERDICT_PROHIBITED = "prohibited"
VERDICT_PENDING_TERMS = "pending_terms"
VERDICT_MISSING = "missing"

CLOSED_SET = frozenset(
    {
        VERDICT_OK_GOV,
        VERDICT_OK_ATTR,
        VERDICT_RESTRICTED,
        VERDICT_PROHIBITED,
        VERDICT_PENDING_TERMS,
        VERDICT_MISSING,
    }
)
PUBLISHABLE = frozenset({VERDICT_OK_GOV, VERDICT_OK_ATTR})

# Adapter id → where the verdict sits in ingest.yaml (human path for errors).
REQUIRED_ADAPTERS = (
    "hyperliquid",
    "polygon",
    "coingecko",
    "binance",
    "fred",
    "calendar",
    "stooq",
    "edgar",
    "treasury",
    "yahoo",
    "tiingo",
    "finnhub",
    "binance.vision",
)


@dataclass(frozen=True)
class LicenceVerdict:
    adapter: str
    verdict: str
    notes: str = ""
    attribution: str = ""

    @property
    def may_publish_value(self) -> bool:
        return self.verdict in PUBLISHABLE

    def canonical(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "licence_verdict": self.verdict,
            "may_publish_value": self.may_publish_value,
            "notes": self.notes,
            "attribution": self.attribution,
        }


def normalize_verdict(raw: Any) -> str:
    value = str(raw or "").strip().lower().replace("-", "_").replace(" ", "_")
    if value not in CLOSED_SET:
        return VERDICT_MISSING
    return value


def _adapter_block(settings: Mapping[str, Any], name: str) -> dict[str, Any]:
    adapters = settings.get("adapters")
    if isinstance(adapters, dict) and isinstance(adapters.get(name), dict):
        return dict(adapters[name])
    return {}


def verdict_for(adapter: str, settings: Mapping[str, Any] | None = None) -> LicenceVerdict:
    loaded = settings if settings is not None else load_ingest_settings()
    block = _adapter_block(loaded, adapter)
    if not block:
        # Fall back to nested adapter maps (equities / macro / spot_cross_check).
        if adapter == "polygon":
            block = dict(loaded.get("equities") or {})
        elif adapter == "fred":
            block = dict((loaded.get("macro") or {}).get("fred") or {})
        elif adapter == "calendar":
            block = dict((loaded.get("macro") or {}).get("calendar") or {})
        elif adapter == "coingecko":
            spot = (loaded.get("crypto") or {}).get("spot_cross_check") or {}
            block = dict(spot.get("coingecko") or {})
        elif adapter == "binance":
            spot = (loaded.get("crypto") or {}).get("spot_cross_check") or {}
            block = dict(spot.get("binance") or {})
        elif adapter == "hyperliquid":
            block = {
                "licence_verdict": (loaded.get("venue_licence_verdict") or loaded.get("licence_verdict")),
                "notes": loaded.get("licence_notes") or "",
            }
    verdict = normalize_verdict(block.get("licence_verdict"))
    return LicenceVerdict(
        adapter=adapter,
        verdict=verdict,
        notes=str(block.get("licence_notes") or block.get("notes") or ""),
        attribution=str(block.get("attribution") or ""),
    )


def standing_rule(settings: Mapping[str, Any] | None = None) -> str:
    loaded = settings if settings is not None else load_ingest_settings()
    licence = loaded.get("licence") if isinstance(loaded.get("licence"), dict) else {}
    text = str(licence.get("standing_rule") or "").strip()
    return text or STANDING_RULE


def load_all_verdicts(path: Path | None = None) -> dict[str, LicenceVerdict]:
    settings = load_ingest_settings(path)
    out: dict[str, LicenceVerdict] = {}
    adapters = settings.get("adapters") if isinstance(settings.get("adapters"), dict) else {}
    names = set(REQUIRED_ADAPTERS) | set(adapters)
    for name in sorted(names):
        out[str(name)] = verdict_for(str(name), settings)
    return out


def assert_licence_invariants(path: Path | None = None) -> None:
    """Fail closed: every required adapter has a recorded closed-set verdict."""
    settings_path = path or (repo_root() / "config" / "ingest.yaml")
    settings = load_yaml(settings_path) if settings_path.is_file() else load_ingest_settings(path)
    licence = settings.get("licence") if isinstance(settings.get("licence"), dict) else {}
    if STANDING_RULE.split()[0] not in standing_rule(settings):
        # Accept the canonical sentence; do not invent a second rule.
        if "prohibit redistribution" not in standing_rule(settings).lower():
            raise ValueError("ingest.yaml licence.standing_rule must record the Principal redistribution rule")
    adapters = settings.get("adapters") if isinstance(settings.get("adapters"), dict) else {}
    missing: list[str] = []
    for name in REQUIRED_ADAPTERS:
        block = adapters.get(name) if isinstance(adapters.get(name), dict) else {}
        raw = block.get("licence_verdict") if block else None
        if normalize_verdict(raw) == VERDICT_MISSING:
            missing.append(name)
    if missing:
        raise ValueError(
            "licence_verdict missing next to adapter(s): "
            + ", ".join(missing)
            + "; record a closed-set verdict in config/ingest.yaml adapters"
        )
    closed = {str(x) for x in (licence.get("closed_set") or CLOSED_SET)}
    if not PUBLISHABLE <= closed:
        raise ValueError("licence.closed_set must include ok_gov and ok_attr")


def may_publish_value(adapter: str, settings: Mapping[str, Any] | None = None) -> bool:
    return verdict_for(adapter, settings).may_publish_value


def filter_published_values(
    rows: list[dict[str, Any]],
    *,
    source_key: str = "source",
    value_key: str = "value",
    settings: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Drop values whose adapter licence forbids redistribution into published artifacts."""
    out: list[dict[str, Any]] = []
    for raw in rows:
        item = dict(raw)
        source = str(item.get(source_key) or "")
        if not may_publish_value(source, settings):
            item[value_key] = None
            item["value_redacted"] = True
            item["redact_reason"] = "licence_verdict forbids published values; internal compute only"
        else:
            item["value_redacted"] = False
        item["licence_verdict"] = verdict_for(source, settings).verdict
        out.append(item)
    return out
