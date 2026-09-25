"""Assemble pre-open, close, and alert briefs from fixtures and/or Market Memory."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from mm_common.time import as_utc, parse_utc, utcnow
from mm_briefing.alerts import evaluate_alerts
from mm_briefing.calendar import DEFAULT_CALENDAR_SOURCE, events_from_rows, relevant_events
from mm_briefing.config import AlertSettings, BriefingSettings, load_briefing_settings
from mm_briefing.divergences import assumption_changes, evaluate_divergences, unexpected_moves
from mm_briefing.fetchers import (
    MacroFetcher,
    apply_crypto_pulse_from_hl,
    complete_cross_asset,
    crypto_pulse_source_of_record,
    fetcher_for_mode,
    live_macro_spec,
    snapshot_from_payload,
)
from mm_briefing.freshness import load_freshness_config
from mm_briefing.hl import (
    LIVE_INFO_SOURCE,
    ensure_hl_instruments,
    hl_from_live_info,
    hl_from_memory,
    hl_from_payload,
    hl_has_metrics,
)
from mm_briefing.models import (
    AlertDecision,
    BriefDocument,
    HLInstrumentState,
    MacroSnapshot,
    ThesisHook,
    overall_pulse_quality,
    worst_quality,
)
from mm_briefing.render import render_alerts, render_close, render_preopen
from mm_briefing.schedule import prior_us_cash_close, us_session_status
from mm_briefing.watchlist import build_watchlist


def load_fixture_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("briefing fixture must be a JSON/YAML object")
    return data


def as_of_for_kind(kind: str, fixture: dict[str, Any] | None, fallback: datetime) -> datetime:
    if fixture:
        times = fixture.get("kind_times") or {}
        if kind in times:
            return parse_utc(str(times[kind]))
        if fixture.get("as_of"):
            return parse_utc(str(fixture["as_of"]))
    return as_utc(fallback)


def prior_close_for(fixture: dict[str, Any] | None, as_of: datetime) -> datetime:
    if fixture and fixture.get("prior_us_close"):
        return parse_utc(str(fixture["prior_us_close"]))
    return prior_us_cash_close(as_of)


def theses_from_payload(rows: list[dict[str, Any]], session: MacroSnapshot | None) -> tuple[ThesisHook, ...]:
    session_map = session.by_symbol() if session is not None else {}
    out: list[ThesisHook] = []
    for row in rows:
        instrument = str(row.get("instrument") or "") or None
        direction = str(row.get("expected_direction") or "").lower() or None
        print_ = session_map.get(instrument) if instrument else None
        hook = _verdict_hook(direction, print_.change_pct if print_ is not None else None, instrument)
        out.append(
            ThesisHook(
                slug=str(row.get("slug") or ""),
                status=str(row.get("status") or ""),
                instrument=instrument,
                invalidation_summary=str(row.get("invalidation_summary") or "") or None,
                expected_direction=direction,
                verdict_hook=hook,
                hypothesis=str(row.get("hypothesis") or ""),
            )
        )
    return tuple(sorted(out, key=lambda row: row.slug))


def theses_from_memory(session: Session, snapshot: MacroSnapshot | None) -> tuple[ThesisHook, ...]:
    from mm_memory.queries import list_theses

    rows = list_theses(session)
    payload = [
        {
            "slug": row.slug,
            "status": row.status,
            "instrument": row.instrument,
            "invalidation_summary": row.invalidation_summary,
            "expected_direction": None,
            "hypothesis": "",
        }
        for row in rows
        if row.status not in {"rejected", "retired"}
    ]
    return theses_from_payload(payload, snapshot)


def _verdict_hook(direction: str | None, change_pct: float | None, instrument: str | None) -> str:
    inst = instrument or "instrument"
    if direction is None or change_pct is None:
        return f"insufficient session print to score {inst}; keep invalidation live"
    aligned = (direction == "long" and change_pct > 0) or (direction == "short" and change_pct < 0)
    if aligned:
        return f"lab right (so far): expected {direction} {inst}, session {change_pct:+.2f}%"
    if (direction == "long" and change_pct < 0) or (direction == "short" and change_pct > 0):
        return f"lab wrong (so far): expected {direction} {inst}, session {change_pct:+.2f}%"
    return f"flat vs expected {direction} {inst}"


def generate_preopen(
    *,
    as_of: datetime,
    settings: BriefingSettings,
    macro: MacroSnapshot,
    hl: tuple[HLInstrumentState, ...],
    generated_at: datetime | None = None,
    memory_watermark: datetime | None = None,
    hl_origin: str = "market_memory",
    calendar_source: str | None = None,
) -> BriefDocument:
    generated = as_utc(generated_at or as_of)
    filled = complete_cross_asset(macro, freshness=load_freshness_config(settings.macro))
    hl_filled = ensure_hl_instruments(hl, as_of=as_utc(as_of))
    filled = apply_crypto_pulse_from_hl(
        filled,
        hl_filled,
        source_of_record=crypto_pulse_source_of_record(settings.macro),
        macro_config=settings.macro,
    )
    cal_source = calendar_source or getattr(settings, "calendar_source", None) or DEFAULT_CALENDAR_SOURCE
    calendar = relevant_events(events_from_rows(settings.calendar_events, source=cal_source), as_of=as_of)
    divergences = evaluate_divergences(filled, settings.divergence_rules)
    watch = build_watchlist(settings.watchlist, hl_filled)
    quality = overall_pulse_quality(
        filled.data_quality,
        *(row.data_quality for row in filled.assets),
        *(row.data_quality for row in hl_filled),
    )
    return render_preopen(
        generated_at=generated,
        as_of=as_utc(as_of),
        macro=filled,
        calendar=calendar,
        divergences=divergences,
        hl=hl_filled,
        watchlist=watch,
        data_quality=quality,
        session_tz=settings.schedule.session_timezone,
        lab_tz=settings.schedule.lab_timezone,
        session_status=us_session_status(generated, session_tz=settings.schedule.session_timezone),
        memory_watermark=as_utc(memory_watermark) if memory_watermark is not None else as_utc(as_of),
        hl_origin=hl_origin,
        calendar_source=cal_source,
    )


def generate_close(
    *,
    as_of: datetime,
    settings: BriefingSettings,
    overnight: MacroSnapshot,
    session: MacroSnapshot,
    hl: tuple[HLInstrumentState, ...],
    theses: tuple[ThesisHook, ...],
    generated_at: datetime | None = None,
    prior_reader: object | None = None,
) -> BriefDocument:
    generated = as_utc(generated_at or as_of)
    freshness = load_freshness_config(settings.macro)
    sor = crypto_pulse_source_of_record(settings.macro)
    overnight_gated = apply_crypto_pulse_from_hl(
        complete_cross_asset(overnight, freshness=freshness),
        hl,
        source_of_record=sor,
        macro_config=settings.macro,
    )
    session_gated = apply_crypto_pulse_from_hl(
        complete_cross_asset(session, freshness=freshness),
        hl,
        source_of_record=sor,
        macro_config=settings.macro,
    )
    calendar = relevant_events(events_from_rows(settings.calendar_events), as_of=as_of, lookback_hours=0, horizon_hours=24)
    unexpected = unexpected_moves(session_gated, overnight_gated)
    assumptions = assumption_changes(session_gated, overnight_gated)
    quality = worst_quality(
        overnight_gated.data_quality,
        session_gated.data_quality,
        *(row.data_quality for row in hl),
    )
    return render_close(
        generated_at=generated,
        as_of=as_utc(as_of),
        overnight=overnight_gated,
        session=session_gated,
        calendar=calendar,
        unexpected=unexpected,
        theses=theses,
        assumptions=assumptions,
        hl=hl,
        data_quality=quality,
        session_tz=settings.schedule.session_timezone,
        lab_tz=settings.schedule.lab_timezone,
        prior_reader=prior_reader,
    )


def generate_alerts(
    *,
    as_of: datetime,
    settings: BriefingSettings,
    hl: tuple[HLInstrumentState, ...],
    generated_at: datetime | None = None,
    prior_identity_hashes: tuple[str, ...] = (),
    alert_settings: AlertSettings | None = None,
) -> tuple[AlertDecision, BriefDocument | None]:
    decision = evaluate_alerts(hl, alert_settings or settings.alerts, prior_identity_hashes=prior_identity_hashes)
    if not decision.pushed:
        return decision, None
    generated = as_utc(generated_at or as_of)
    quality = worst_quality(*(row.data_quality for row in hl)) if hl else "ok"
    doc = render_alerts(
        generated_at=generated,
        as_of=as_utc(as_of),
        events=decision.events,
        data_quality=quality,
        session_tz=settings.schedule.session_timezone,
        lab_tz=settings.schedule.lab_timezone,
    )
    return decision, doc


def generate_from_fixture(
    kind: str,
    fixture: dict[str, Any],
    *,
    settings: BriefingSettings | None = None,
    as_of: datetime | None = None,
    generated_at: datetime | None = None,
    alert_settings: AlertSettings | None = None,
) -> tuple[BriefDocument | None, AlertDecision | None]:
    cfg = settings or load_briefing_settings()
    moment = as_of_for_kind(kind, fixture, as_of or utcnow())
    generated = generated_at or moment
    prior = prior_close_for(fixture, moment)
    overnight = _macro_from_fixture(fixture, key="macro", as_of=moment, prior=prior)
    session_snap = _macro_from_fixture(fixture, key="session", as_of=moment, prior=prior)
    hl = hl_from_payload(fixture.get("hyperliquid") or {})
    if kind == "preopen":
        origin = str((fixture.get("hyperliquid") or {}).get("source") or "hyperliquid.info")
        return (
            generate_preopen(
                as_of=moment,
                settings=cfg,
                macro=overnight,
                hl=hl,
                generated_at=generated,
                memory_watermark=moment,
                hl_origin=origin,
            ),
            None,
        )
    if kind == "close":
        theses = theses_from_payload(list(fixture.get("theses") or []), session_snap)
        return (
            generate_close(
                as_of=moment,
                settings=cfg,
                overnight=overnight,
                session=session_snap,
                hl=hl,
                theses=theses,
                generated_at=generated,
            ),
            None,
        )
    if kind == "alert":
        decision, doc = generate_alerts(
            as_of=moment,
            settings=cfg,
            hl=hl,
            generated_at=generated,
            alert_settings=alert_settings,
        )
        return doc, decision
    raise ValueError(f"unknown brief kind {kind!r}")


def generate_from_sources(
    kind: str,
    *,
    settings: BriefingSettings,
    as_of: datetime,
    macro_fetcher: MacroFetcher,
    session: Session | None = None,
    fixture: dict[str, Any] | None = None,
    generated_at: datetime | None = None,
    alert_settings: AlertSettings | None = None,
    live: bool = False,
    hl_client=None,
) -> tuple[BriefDocument | None, AlertDecision | None]:
    if fixture is not None:
        return generate_from_fixture(
            kind,
            fixture,
            settings=settings,
            as_of=as_of,
            generated_at=generated_at,
            alert_settings=alert_settings,
        )
    generated = as_utc(generated_at or as_of)
    prior = prior_us_cash_close(as_of)
    fetcher = macro_fetcher
    if live:
        fetcher = fetcher_for_mode("live", macro_spec=live_macro_spec(settings.macro))
    overnight = complete_cross_asset(
        fetcher.fetch(as_of, prior_us_close=prior),
        freshness=load_freshness_config(settings.macro),
    )
    session_snap = overnight
    hl: tuple[HLInstrumentState, ...] = ()
    theses: tuple[ThesisHook, ...] = ()
    hl_origin = "none"
    owns_client = False
    if session is not None:
        hl = hl_from_memory(session, as_of)
        hl_origin = "market_memory"
        theses = theses_from_memory(session, session_snap if kind == "close" else overnight)
    if live and not hl_has_metrics(hl):
        from mm_ingest.hl_info import HyperliquidInfoClient

        client = hl_client
        if client is None:
            client = HyperliquidInfoClient()
            owns_client = True
        try:
            hl = hl_from_live_info(client, captured_at=generated)
            hl_origin = LIVE_INFO_SOURCE
        finally:
            if owns_client:
                client.close()
    if kind == "preopen":
        return (
            generate_preopen(
                as_of=as_of,
                settings=settings,
                macro=overnight,
                hl=hl,
                generated_at=generated,
                memory_watermark=as_of if session is not None else generated,
                hl_origin=hl_origin,
            ),
            None,
        )
    if kind == "close":
        return (
            generate_close(
                as_of=as_of,
                settings=settings,
                overnight=overnight,
                session=session_snap,
                hl=hl,
                theses=theses,
                generated_at=generated_at,
            ),
            None,
        )
    if kind == "alert":
        return generate_alerts(
            as_of=as_of,
            settings=settings,
            hl=hl,
            generated_at=generated_at,
            alert_settings=alert_settings,
        )
    raise ValueError(f"unknown brief kind {kind!r}")


def default_macro_fetcher(settings: BriefingSettings, fixture: dict[str, Any] | None = None) -> MacroFetcher:
    mode = str(settings.macro.get("mode") or "off")
    if fixture is not None:
        mode = "fixture"
        payload = fixture
    else:
        payload = fixture or {}
        fixture_path = settings.macro.get("fixture_path")
        if mode == "fixture" and fixture_path:
            payload = load_fixture_file(settings.root / str(fixture_path))
    return fetcher_for_mode(mode, fixture_payload=payload, macro_spec=settings.macro)


def _macro_from_fixture(fixture: dict[str, Any], *, key: str, as_of: datetime, prior: datetime) -> MacroSnapshot:
    body = fixture.get(key) or {}
    if not isinstance(body, dict):
        body = {}
    return snapshot_from_payload(body, as_of=as_of, prior_us_close=prior, source=str(body.get("source") or "fixture"))
