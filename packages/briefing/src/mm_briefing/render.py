"""Deterministic markdown rendering for pre-open, close, and alert briefs."""

from __future__ import annotations

from datetime import datetime

from mm_common.hashing import sha256_hex
from mm_briefing.divergences import fmt_pct, fmt_px
from mm_briefing.freshness import FreshnessConfig, format_quality_with_age
from mm_briefing.health import load_presentation_config, pulse_to_health_state, score_data_health
from mm_briefing.hl import basis_mark_oracle, funding_value, liquidation_size_sum, oi_change_pct
from mm_briefing.models import (
    AlertEvent,
    AssetPrint,
    BriefDocument,
    CalendarEvent,
    Divergence,
    HLInstrumentState,
    MacroSnapshot,
    SessionStatus,
    SourceStatus,
    ThesisHook,
    WatchItem,
    display_symbol,
    pulse_quality,
    slot_label,
)
from mm_briefing.schedule import NY_TZ, SYDNEY_TZ, session_date_for, us_session_status

NO_DECISION_FOOTER = (
    "---",
    "**Informational only — no decision, no recommendation, no order intent.**",
    "This brief does not change universe membership, size a trade, submit an order, or approve risk.",
)

SOURCE_HEALTH_POINTER = (
    "Standing source-health (Data desk, not this brief): `lab data source-health` → "
    "`ops/reports/source-health/` (latest dated file). Pointer only — this brief does not embed a health report."
)


def _no_decision_footer(*, live_macro: bool = False) -> tuple[str, ...]:
    if live_macro:
        return (*NO_DECISION_FOOTER, SOURCE_HEALTH_POINTER)
    return NO_DECISION_FOOTER


def brief_hash(markdown: str) -> str:
    return sha256_hex(markdown.replace("\r\n", "\n"))


def iso(ts: datetime) -> str:
    return ts.isoformat(timespec="seconds")


def render_preopen(
    *,
    generated_at: datetime,
    as_of: datetime,
    macro: MacroSnapshot,
    calendar: tuple[CalendarEvent, ...],
    divergences: tuple[Divergence, ...],
    hl: tuple[HLInstrumentState, ...],
    watchlist: tuple[WatchItem, ...],
    data_quality: str,
    session_tz: str = "America/New_York",
    lab_tz: str = "Australia/Sydney",
    session_status: SessionStatus | None = None,
    source_statuses: tuple[SourceStatus, ...] = (),
    memory_watermark: datetime | None = None,
    hl_origin: str = "market_memory",
    calendar_source: str = "config/briefing/calendar.yaml",
    freshness: FreshnessConfig | None = None,
) -> BriefDocument:
    session_date = session_date_for(as_of)
    status = session_status or us_session_status(generated_at, session_tz=session_tz)
    ny_gen = generated_at.astimezone(NY_TZ)
    syd_gen = generated_at.astimezone(SYDNEY_TZ)
    watermark = memory_watermark if memory_watermark is not None else as_of
    presentation = load_presentation_config()
    health = score_data_health(macro.assets, hl, config=presentation)
    lines = [
        f"# US Pre-Market Brief — {session_date.isoformat()}",
        "",
        f"Generated (UTC): {iso(generated_at)}",
        f"Generated (America/New_York): {iso(ny_gen)} ({ny_gen.tzname() or session_tz})",
        f"Generated (Australia/Sydney): {iso(syd_gen)} ({syd_gen.tzname() or lab_tz})",
        (
            f"US session status: {status.code} — {status.label} "
            f"(DST={status.tzname}, offset {status.utc_offset}; "
            f"cash open {status.cash_open}, cash close {status.cash_close} {status.timezone})"
        ),
        f"Memory watermark (as_of_knowledge): {iso(watermark)}",
        f"As-of knowledge: {iso(as_of)} (ingested_at lockstep; never published_at / market_time)",
        *health.header_lines(icons=presentation.icons),
        f"Macro source: {macro.source}",
        f"HL origin: {hl_origin}",
        "",
        *health.section_lines(icons=presentation.icons),
        "",
        "## Data quality by source",
        "",
    ]
    lines.extend(_source_table(source_statuses, macro=macro, hl=hl, calendar_source=calendar_source, as_of=as_of))
    lines.extend(
        [
            "",
            "## Cross-asset snapshot",
            "",
            f"Section as-of: {iso(macro.as_of)} (capture/quote time — not an exchange-event clock unless the source says so)",
            "Required slots (always listed): crypto, equity-index proxy, rates, USD, oil, vol. Unavailable is shown, never invented.",
            "",
        ]
    )
    lines.extend(
        _asset_table(macro.assets, vs="Name", knowledge_as_of=as_of, freshness=freshness)
    )
    if macro.notes:
        lines.append("")
        lines.append("Notes:")
        for note in macro.notes:
            lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## What changed since prior US close",
            "",
            f"Prior US close watermark: {iso(macro.prior_us_close)}",
            "Figures below are recorded prints vs that close; missing slots stay unavailable (not invented).",
            "",
        ]
    )
    lines.extend(_since_close_bullets(macro.assets, knowledge_as_of=as_of, freshness=freshness))
    lines.extend(_hl_since_close(hl, prior_close=macro.prior_us_close))
    lines.extend(
        [
            "",
            "## Today's market-event calendar",
            "",
            f"Source: {calendar_source} (approved attributable file; empty window is shown, not invented)",
            f"Section as-of: {iso(as_of)}",
            "",
        ]
    )
    if calendar:
        for event in calendar:
            extra = f" — {event.notes}" if event.notes else ""
            lines.append(
                f"- {iso(event.when)} [{event.importance}] {event.region} {event.name} "
                f"(source: {event.source}){extra}"
            )
    else:
        lines.append("- None in the look-ahead window.")
    lines.extend(["", "## Cross-asset divergences", ""])
    if divergences:
        for row in divergences:
            lines.append(f"- `{row.rule_id}` **{row.title}**: {row.detail} (evidence: {', '.join(row.evidence)})")
    else:
        lines.append("- No configured rule fired.")
    lines.extend(
        [
            "",
            "## Hyperliquid market structure",
            "",
            f"Section as-of / memory watermark: {iso(watermark)}",
            f"Source: {hl_origin} — public `/info` allowlist only (no wallet, user, account, or trading endpoints).",
            "Snapshot fields have no exchange event time; capture is ingested_at / as_of_knowledge.",
            "",
        ]
    )
    lines.extend(_hl_section(hl))
    lines.extend(["", "## Watchlist", ""])
    if watchlist:
        for item in watchlist:
            lines.append(f"### {item.instrument}")
            lines.append("")
            lines.append(f"- Why now: {item.why_now}")
            evidence = ", ".join(item.evidence) if item.evidence else "none"
            lines.append(f"- Evidence (observation ids): {evidence}")
            if item.levels:
                level_txt = ", ".join(f"{name}={value}" for name, value in item.levels)
                lines.append(f"- Levels: {level_txt}")
            lines.append(f"- Invalidation: {item.invalidation}")
            lines.append(f"- No-trade: {item.no_trade}")
            lines.append("")
    else:
        lines.append("- Watchlist empty.")
        lines.append("")
    lines.extend(["", *_no_decision_footer(live_macro=macro.source == "live")])
    markdown = "\n".join(lines).rstrip() + "\n"
    return BriefDocument(
        kind="preopen",
        session_date=session_date,
        generated_at=generated_at,
        as_of_knowledge=as_of,
        session_tz=session_tz,
        lab_tz=lab_tz,
        data_quality=data_quality,
        markdown=markdown,
        content_hash=brief_hash(markdown),
        payload={"kind": "preopen", "data_quality": data_quality, "session_status": status.code},
    )


def render_close(
    *,
    generated_at: datetime,
    as_of: datetime,
    overnight: MacroSnapshot,
    session: MacroSnapshot,
    calendar: tuple[CalendarEvent, ...],
    unexpected: tuple[str, ...],
    theses: tuple[ThesisHook, ...],
    assumptions: tuple[str, ...],
    hl: tuple[HLInstrumentState, ...],
    data_quality: str,
    session_tz: str = "America/New_York",
    lab_tz: str = "Australia/Sydney",
    freshness: FreshnessConfig | None = None,
) -> BriefDocument:
    session_date = session_date_for(as_of)
    ny = generated_at.astimezone(NY_TZ)
    syd = generated_at.astimezone(SYDNEY_TZ)
    status = us_session_status(generated_at, session_tz=session_tz)
    presentation = load_presentation_config()
    health = score_data_health(session.assets, hl, config=presentation)
    lines = [
        f"# US Close Brief — {session_date.isoformat()}",
        "",
        f"Generated (UTC): {iso(generated_at)}",
        f"Generated (America/New_York): {iso(ny)} ({ny.tzname() or session_tz})",
        f"Generated (Australia/Sydney): {iso(syd)} ({syd.tzname() or lab_tz})",
        f"US session status: {status.code} — {status.label} (DST={status.tzname})",
        f"As-of knowledge: {iso(as_of)} (ingested_at watermark; never published_at alone)",
        *health.header_lines(icons=presentation.icons),
        "",
        *health.section_lines(icons=presentation.icons),
        "",
        "## What moved",
        "",
    ]
    lines.extend(
        _asset_table(
            session.assets,
            vs="prior US close (session)",
            knowledge_as_of=as_of,
            freshness=freshness,
        )
    )
    lines.extend(["", "Overnight reference:", ""])
    lines.extend(_since_close_bullets(overnight.assets, knowledge_as_of=as_of, freshness=freshness))
    lines.extend(["", "## What was unexpected", ""])
    if unexpected:
        for note in unexpected:
            lines.append(f"- {note}")
    else:
        lines.append("- Nothing crossed the unexpected-move rules.")
    lines.extend(["", "## Lab right/wrong hooks", ""])
    if theses:
        for thesis in theses:
            inst = thesis.instrument or "n/a"
            lines.append(
                f"- `{thesis.slug}` status={thesis.status} instrument={inst}: {thesis.verdict_hook}"
            )
            if thesis.invalidation_summary:
                lines.append(f"  - Invalidation: {thesis.invalidation_summary}")
            if thesis.hypothesis:
                lines.append(f"  - Hypothesis: {thesis.hypothesis}")
    else:
        lines.append("- No indexed theses to score against this session.")
    lines.extend(["", "## Assumption changes", ""])
    for note in assumptions:
        lines.append(f"- {note}")
    lines.extend(["", "## Monitor into Asia / Europe / next US", ""])
    lines.append("- Asia: BTC/ETH funding, OI, and liquidation prints vs US cash close levels.")
    lines.append("- Europe: whether the USD/yields overnight path re-asserts before next US pre-open.")
    if calendar:
        lines.append("- Dated catalysts still live:")
        for event in calendar:
            extra = f" — {event.notes}" if event.notes else ""
            lines.append(f"  - {iso(event.when)} [{event.importance}] {event.name}{extra}")
    else:
        lines.append("- No dated catalysts remaining in the look-ahead window.")
    lines.extend(["", "## Hyperliquid into the next session", ""])
    lines.extend(_hl_section(hl))
    lines.extend(["", *NO_DECISION_FOOTER])
    markdown = "\n".join(lines).rstrip() + "\n"
    return BriefDocument(
        kind="close",
        session_date=session_date,
        generated_at=generated_at,
        as_of_knowledge=as_of,
        session_tz=session_tz,
        lab_tz=lab_tz,
        data_quality=data_quality,
        markdown=markdown,
        content_hash=brief_hash(markdown),
        payload={"kind": "close", "data_quality": data_quality},
    )


def render_alerts(
    *,
    generated_at: datetime,
    as_of: datetime,
    events: tuple[AlertEvent, ...],
    data_quality: str,
    session_tz: str = "America/New_York",
    lab_tz: str = "Australia/Sydney",
) -> BriefDocument:
    session_date = session_date_for(as_of)
    lines = [
        f"# Intraday alerts — {session_date.isoformat()}",
        "",
        f"Generated: {iso(generated_at)}",
        f"As-of knowledge: {iso(as_of)}",
        f"Data quality: {data_quality}",
        "",
        "Threshold-gated only. No commentary beyond the crossed rule.",
        "",
    ]
    for event in events:
        evidence = ", ".join(event.evidence) if event.evidence else "none"
        lines.append(f"- `{event.alert_type}` {event.instrument}: {event.detail}")
        lines.append(f"  - evidence: {evidence}")
        thresh = ", ".join(f"{k}={v}" for k, v in sorted(event.threshold.items()))
        lines.append(f"  - threshold: {thresh}")
    lines.extend(["", *NO_DECISION_FOOTER])
    markdown = "\n".join(lines).rstrip() + "\n"
    return BriefDocument(
        kind="alert",
        session_date=session_date,
        generated_at=generated_at,
        as_of_knowledge=as_of,
        session_tz=session_tz,
        lab_tz=lab_tz,
        data_quality=data_quality,
        markdown=markdown,
        content_hash=brief_hash(markdown),
        payload={"kind": "alert", "count": len(events)},
    )


def _asset_table(
    assets: tuple[AssetPrint, ...],
    *,
    vs: str,
    knowledge_as_of: datetime | None = None,
    freshness: FreshnessConfig | None = None,
) -> list[str]:
    if not assets:
        return ["- No prints (macro snapshot empty or degraded)."]
    lines = [
        f"| Slot | Symbol | Last | Prior close | Change | {vs} | Source | As-of | State |",
        "|---|---|---:|---:|---:|---|---|---|---|",
    ]
    for row in assets:
        if row.unit == "%":
            change = f"{row.change_bp:+.1f}bp" if row.change_bp is not None else "n/a"
        else:
            change = fmt_pct(row.change_pct)
        as_of = iso(row.as_of) if row.as_of is not None else "n/a"
        state = _row_state_label(
            row,
            knowledge_as_of=knowledge_as_of,
            freshness=freshness,
        )
        lines.append(
            f"| {slot_label(row.symbol)} | {display_symbol(row)} | {fmt_px(row.last)} | {fmt_px(row.prior_close)} | {change} "
            f"| {row.name} | {row.source} | {as_of} | {state} |"
        )
    return lines


def _since_close_bullets(
    assets: tuple[AssetPrint, ...],
    *,
    knowledge_as_of: datetime | None = None,
    freshness: FreshnessConfig | None = None,
) -> list[str]:
    if not assets:
        return ["- No overnight prints available."]
    lines: list[str] = []
    for row in assets:
        if row.unit == "%":
            delta = f"{row.change_bp:+.1f}bp" if row.change_bp is not None else "n/a"
        else:
            delta = fmt_pct(row.change_pct)
        as_of = iso(row.as_of) if row.as_of is not None else "n/a"
        obs = row.observation_id or "none"
        state = _row_state_label(row, knowledge_as_of=knowledge_as_of, freshness=freshness)
        shown = display_symbol(row)
        slot_note = f" slot={row.symbol}" if shown.upper() != row.symbol.upper() else ""
        lines.append(
            f"- {shown} [{slot_label(row.symbol)}]{slot_note} ({row.name}): last {fmt_px(row.last)} / {delta} "
            f"[state={state}; source={row.source}; as-of={as_of}; obs {obs}]"
        )
    return lines


def _row_state_label(
    row: AssetPrint,
    *,
    knowledge_as_of: datetime | None,
    freshness: FreshnessConfig | None,
) -> str:
    """Icon + data-state label. Not a direction."""
    presentation = load_presentation_config()
    state = pulse_to_health_state(row.data_quality)
    icon = presentation.icons.get(state, "")
    if state == "stale" and knowledge_as_of is not None:
        basis = "calendar"
        if freshness is not None:
            resolved = freshness.lag_for(source=row.source, symbol=row.symbol)
            if resolved is not None:
                basis = resolved.age_basis
        aged = format_quality_with_age(
            row.data_quality,
            observation_as_of=row.as_of,
            reference_as_of=knowledge_as_of,
            age_basis=basis,
        )
        return f"{icon} {aged}".strip()
    return f"{icon} {state}".strip()


def _hl_since_close(hl: tuple[HLInstrumentState, ...], *, prior_close: datetime) -> list[str]:
    if not hl:
        return ["- Hyperliquid prior-close comparison unavailable (no retained observations)."]
    lines = [
        f"- HL vs prior US close {iso(prior_close)} "
        "(close-to-close change only when a prior observation exists; current snapshot is labeled, not invented as a move):"
    ]
    any_change = False
    for state in hl:
        oi_chg = oi_change_pct(state)
        funding = funding_value(state)
        mid = state.metric("mid_px")
        bits: list[str] = []
        if oi_chg is not None:
            bits.append(f"OI {oi_chg:+.2f}% vs prior print")
            any_change = True
        else:
            bits.append("OI change unavailable (no retained observation at/before prior US close)")
        if funding is not None:
            bits.append(f"current funding {funding:.6f} (snapshot, not a close-to-close delta)")
        if mid and mid.value:
            bits.append(f"current mid {mid.value} (snapshot, not a close-to-close delta)")
        if not bits:
            lines.append(
                f"  - {state.instrument}: unavailable "
                f"[quality={pulse_quality(state.data_quality)}; source={state.source}]"
            )
        else:
            lines.append(
                f"  - {state.instrument}: {'; '.join(bits)} "
                f"[quality={pulse_quality(state.data_quality)}; source={state.source}]"
            )
    if not any_change and not any(state.metrics for state in hl):
        lines.append("- HL prior-close comparison unavailable (no retained observation before prior US close).")
    return lines


def _source_table(
    explicit: tuple[SourceStatus, ...],
    *,
    macro: MacroSnapshot,
    hl: tuple[HLInstrumentState, ...],
    calendar_source: str,
    as_of: datetime,
) -> list[str]:
    rows = list(explicit) if explicit else list(_infer_source_statuses(macro, hl, calendar_source, as_of))
    if not rows:
        return ["- No sources reported."]
    lines = [
        "| Source | Status | As-of | Evidence | Notes |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        as_of_txt = iso(row.as_of) if row.as_of is not None else "n/a"
        lines.append(
            f"| {row.name} | {pulse_quality(row.quality)} | {as_of_txt} | {row.evidence or 'n/a'} | {row.notes or ''} |"
        )
    return lines


def _infer_source_statuses(
    macro: MacroSnapshot,
    hl: tuple[HLInstrumentState, ...],
    calendar_source: str,
    as_of: datetime,
) -> tuple[SourceStatus, ...]:
    by_source: dict[str, list[AssetPrint]] = {}
    for asset in macro.assets:
        by_source.setdefault(asset.source, []).append(asset)
    rows: list[SourceStatus] = []
    for name, assets in sorted(by_source.items()):
        quality = "ok"
        as_times = [row.as_of for row in assets if row.as_of is not None]
        for asset in assets:
            quality = worst_quality_local(quality, asset.data_quality)
        evidence = ", ".join(sorted({asset.symbol for asset in assets}))
        attached = ""
        for item in macro.notes:
            lowered = item.lower()
            if name == "fred" and "fred" in lowered:
                attached = item
            elif name == "stooq" and "stooq" in lowered:
                attached = item
            elif name == "polygon" and "polygon" in lowered:
                attached = item
            elif name == "coingecko" and "coingecko" in lowered:
                attached = item
            elif "hyperliquid" in name and ("hyperliquid" in lowered or "crypto pulse" in lowered):
                attached = item
            elif name in {"off", "none", "live"} and not attached:
                attached = item
        rows.append(
            SourceStatus(
                name=name,
                quality=quality,
                as_of=max(as_times) if as_times else macro.as_of,
                evidence=evidence,
                notes=attached,
            )
        )
    hl_quality = "unavailable"
    hl_ids: list[str] = []
    hl_source = "hyperliquid.info"
    hl_as_of = as_of
    if hl:
        hl_quality = "ok"
        for state in hl:
            hl_quality = worst_quality_local(hl_quality, state.data_quality)
            hl_ids.extend(state.observation_ids())
            hl_source = state.source
            if state.as_of_knowledge is not None:
                hl_as_of = state.as_of_knowledge
    rows.append(
        SourceStatus(
            name=hl_source,
            quality=hl_quality,
            as_of=hl_as_of,
            evidence=(", ".join(hl_ids) if hl_ids else ("none (not indexed)" if hl else "none")),
            notes="public /info allowlist only",
        )
    )
    rows.append(
        SourceStatus(
            name=calendar_source,
            quality="ok",
            as_of=as_of,
            evidence="yaml events",
            notes="fixture; no live calendar API configured",
        )
    )
    return tuple(rows)


def worst_quality_local(left: str, right: str) -> str:
    from mm_briefing.models import worst_quality

    return worst_quality(left, right)


def _hl_section(hl: tuple[HLInstrumentState, ...]) -> list[str]:
    if not hl:
        return ["- No Hyperliquid observations in the as-of window (unavailable)."]
    lines: list[str] = []
    for state in hl:
        hl_state = pulse_to_health_state(state.data_quality)
        hl_icon = load_presentation_config().icons.get(hl_state, "")
        icon_prefix = f"{hl_icon} " if hl_icon else ""
        lines.append(f"### {state.instrument} ({icon_prefix}{hl_state}; source={state.source})")
        lines.append("")
        as_of = iso(state.as_of_knowledge) if state.as_of_knowledge is not None else "n/a"
        lines.append(f"- Instrument as-of knowledge: {as_of}")
        funding = funding_value(state)
        oi = state.metric("open_interest")
        oi_chg = oi_change_pct(state)
        basis = basis_mark_oracle(state)
        mid = state.metric("mid_px")
        liq = liquidation_size_sum(state)
        funding_m = state.metric("funding")
        lines.append(
            f"- Funding: {_fmt_rate(funding)} (obs {_oid(funding_m)}; "
            f"as-of {_metric_as_of(funding_m)}; market_time {_metric_market_time(funding_m)})"
        )
        oi_txt = _fmt_metric_value(oi.value if oi else None)
        oi_chg_txt = f"{oi_chg:+.2f}%" if oi_chg is not None else "n/a"
        lines.append(
            f"- Open interest: {oi_txt} (Δ {oi_chg_txt}; obs {_oid(oi)}; "
            f"as-of {_metric_as_of(oi)}; market_time {_metric_market_time(oi)})"
        )
        lines.append(
            f"- Mid: {_fmt_metric_value(mid.value if mid else None)} (obs {_oid(mid)}; "
            f"as-of {_metric_as_of(mid)}; market_time {_metric_market_time(mid)})"
        )
        mark = state.metric("mark_px")
        oracle = state.metric("oracle_px")
        lines.append(
            f"- Basis mark−oracle: {_fmt_num(basis)} "
            f"(mark obs {_oid(mark)}; oracle obs {_oid(oracle)})"
        )
        liq_ids = ", ".join(row.observation_id for row in state.liquidations if row.observation_id) or "none"
        lines.append(f"- Liquidations (window sum): {_fmt_num(liq)} (obs {liq_ids})")
        if state.levels:
            level_txt = ", ".join(f"{name}={value}" for name, value in state.levels)
            lines.append(f"- Levels: {level_txt}")
        lines.append("")
    return lines


def _oid(metric) -> str:
    if metric is None or not metric.observation_id:
        if metric is not None and metric.source_url:
            return f"none ({metric.source_url})"
        return "none"
    return metric.observation_id


def _metric_as_of(metric) -> str:
    if metric is None or metric.as_of_knowledge is None:
        return "n/a"
    return iso(metric.as_of_knowledge)


def _metric_market_time(metric) -> str:
    if metric is None:
        return "n/a"
    if metric.market_time is None:
        return "null (snapshot; capture is as_of_knowledge / ingested_at)"
    return iso(metric.market_time)


def _fmt_rate(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.6f}"


def _fmt_num(value: float | None) -> str:
    if value is None:
        return "n/a"
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text if text else "0"


def _fmt_metric_value(value: str | None) -> str:
    if value is None:
        return "missing"
    try:
        return _fmt_num(float(value))
    except ValueError:
        return value
