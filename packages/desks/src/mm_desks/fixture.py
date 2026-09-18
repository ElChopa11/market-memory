"""Load a Phase 5d frozen-day fixture. No network. Degrade, never invent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mm_common.time import parse_utc
from mm_desks.models import (
    CalendarRow,
    FeedRow,
    FrozenDay,
    RiskIntentSpec,
    TapeRow,
    ThesisSnapshot,
)
from mm_quant.models import MarketPanel
from mm_quant.panel import load_panel_file, panel_from_mapping

INTEL_INVENTORY: tuple[str, ...] = (
    "hyperliquid.info",
    "hyperliquid.structure",
    "coingecko",
    "binance.public",
    "stooq",
    "fred",
    "polygon",
    "calendar.yaml",
    "postgres",
    "object_store",
)

REQUIRED_FEEDS: frozenset[str] = frozenset(
    {
        "hyperliquid.info",
        "hyperliquid.structure",
        "polygon",
        "calendar.yaml",
    }
)


def load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON/YAML object")
    return data


def _feeds(intel: dict[str, Any], inventory: tuple[str, ...]) -> tuple[FeedRow, ...]:
    listed = {str(row.get("source_id")): row for row in (intel.get("feeds") or []) if row.get("source_id")}
    out: list[FeedRow] = []
    for source_id in inventory:
        raw = listed.get(source_id) or {}
        status = str(raw.get("status") or "unavailable")
        freshness = str(raw.get("freshness") or ("fresh" if status == "ok" else "unavailable"))
        out.append(
            FeedRow(
                source_id=source_id,
                status=status,
                freshness=freshness,
                observation_id=None if raw.get("observation_id") is None else str(raw.get("observation_id")),
                notes=str(raw.get("notes") or ""),
                required=source_id in REQUIRED_FEEDS,
            )
        )
    return tuple(out)


def _tape(rows: list[dict[str, Any]] | None) -> tuple[TapeRow, ...]:
    out: list[TapeRow] = []
    for raw in rows or []:
        value = raw.get("value")
        out.append(
            TapeRow(
                instrument=str(raw.get("instrument") or "").upper(),
                metric=str(raw.get("metric") or ""),
                value=None if value in (None, "", "unavailable") else str(value),
                source=str(raw.get("source") or "unavailable"),
                freshness=str(raw.get("freshness") or "unavailable"),
                observation_id=None if raw.get("observation_id") is None else str(raw.get("observation_id")),
                asset_class=str(raw.get("asset_class") or "unknown"),
                membership=str(raw.get("membership") or "not_in_membership"),
            )
        )
    return tuple(out)


def _calendar(rows: list[dict[str, Any]] | None) -> tuple[CalendarRow, ...]:
    out: list[CalendarRow] = []
    for raw in rows or []:
        when_raw = raw.get("when") or raw.get("datetime")
        if not when_raw:
            continue
        out.append(
            CalendarRow(
                when=parse_utc(str(when_raw)),
                name=str(raw.get("name") or "event"),
                importance=str(raw.get("importance") or "medium").lower(),
                region=str(raw.get("region") or "US"),
                notes=str(raw.get("notes") or ""),
                source=str(raw.get("source") or "fixture"),
            )
        )
    return tuple(sorted(out, key=lambda row: (row.when, row.name)))


def _thesis(raw: dict[str, Any] | None) -> ThesisSnapshot:
    data = raw or {}
    evidence = tuple(str(item) for item in (data.get("evidence_ids") or ()))
    return ThesisSnapshot(
        slug=str(data.get("slug") or "THESIS-5D-FIXTURE"),
        status=str(data.get("status") or "in_skeptic"),
        author=str(data.get("author") or "Crypto Desk"),
        instrument=str(data.get("instrument") or "BTC").upper(),
        invalidation=str(data.get("invalidation") or ""),
        max_loss=str(data.get("max_loss") or ""),
        intent=str(data.get("intent") or ""),
        horizon=str(data.get("horizon") or ""),
        membership=str(data.get("membership") or "in_universe"),
        evidence_ids=evidence,
        look_ahead=bool(data.get("look_ahead")),
        leakage=bool(data.get("leakage")),
        already_priced=bool(data.get("already_priced")),
        crowding=str(data.get("crowding") or "noted"),
        invalidation_quality=str(data.get("invalidation_quality") or "ok"),
        reviewer=str(data.get("reviewer") or "Independent Skeptic"),
    )


def _risk(raw: dict[str, Any] | None, thesis: ThesisSnapshot) -> RiskIntentSpec:
    data = raw or {}
    intent = data.get("intent") if isinstance(data.get("intent"), dict) else data
    return RiskIntentSpec(
        instrument=str(intent.get("instrument") or thesis.instrument).upper(),
        invalidation=str(intent.get("invalidation") or thesis.invalidation),
        max_loss=str(intent.get("max_loss") or thesis.max_loss),
        leverage=float(intent.get("leverage") or 1.0),
        environment=str(data.get("environment") or intent.get("environment") or "paper"),
        requested_target=None if not (data.get("requested_target") or intent.get("requested_target")) else str(
            data.get("requested_target") or intent.get("requested_target")
        ),
        halt=bool(data.get("halt") or intent.get("halt")),
    )


def _panel(data: dict[str, Any], *, repo_root: Path) -> MarketPanel:
    if data.get("panel_path"):
        return load_panel_file(repo_root / str(data["panel_path"]))
    if isinstance(data.get("panel"), dict):
        return panel_from_mapping(data["panel"])
    return MarketPanel(fixture_id=str(data.get("fixture_id") or "empty"))


def frozen_day_from_mapping(data: dict[str, Any], *, repo_root: Path) -> FrozenDay:
    intel = data.get("intel") if isinstance(data.get("intel"), dict) else {}
    inventory = tuple(str(item) for item in (intel.get("inventory") or INTEL_INVENTORY))
    if not inventory:
        inventory = INTEL_INVENTORY
    as_of = data.get("as_of_knowledge") or data.get("as_of")
    if not as_of:
        raise ValueError("frozen day fixture missing as_of_knowledge")
    thesis = _thesis(data.get("thesis") if isinstance(data.get("thesis"), dict) else None)
    crypto_rows = (data.get("crypto") or {}).get("tape") if isinstance(data.get("crypto"), dict) else None
    equity_rows = (data.get("equities") or {}).get("tape") if isinstance(data.get("equities"), dict) else None
    tape = _tape(list(crypto_rows or []) + list(equity_rows or []) + list(data.get("tape") or []))
    quant = data.get("quant") if isinstance(data.get("quant"), dict) else {}
    instruments = tuple(str(item).upper() for item in (quant.get("instruments") or ()))
    if not instruments:
        instruments = tuple(dict.fromkeys(row.instrument for row in tape if row.instrument))
    skeptic = data.get("skeptic") if isinstance(data.get("skeptic"), dict) else {}
    force = skeptic.get("force_verdict") or data.get("skeptic_force_verdict")
    return FrozenDay(
        fixture_id=str(data.get("fixture_id") or "phase5d"),
        as_of_knowledge=parse_utc(str(as_of)),
        session_date=str(data.get("session_date") or parse_utc(str(as_of)).date().isoformat()),
        inventory=inventory,
        feeds=_feeds(intel, inventory),
        tape=tape,
        calendar=_calendar(data.get("calendar") if isinstance(data.get("calendar"), list) else None),
        thesis=thesis,
        risk=_risk(data.get("risk") if isinstance(data.get("risk"), dict) else None, thesis),
        panel=_panel(data, repo_root=repo_root),
        quant_instruments=instruments,
        what_changed=str(data.get("what_changed") or "none"),
        skeptic_force_verdict=None if force in (None, "", "null") else str(force).lower(),
        raw=data,
    )


def load_frozen_day(path: Path, *, repo_root: Path | None = None) -> FrozenDay:
    root = Path(repo_root).resolve() if repo_root is not None else Path(".").resolve()
    return frozen_day_from_mapping(load_mapping(path), repo_root=root)
