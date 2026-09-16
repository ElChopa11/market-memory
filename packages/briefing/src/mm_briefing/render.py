"""Deterministic markdown rendering for pre-open, close, and alert briefs."""

from __future__ import annotations

from datetime import datetime

from mm_common.hashing import sha256_hex
from mm_briefing.divergences import fmt_pct, fmt_px
from mm_briefing.hl import basis_mark_oracle, funding_value, liquidation_size_sum, oi_change_pct
from mm_briefing.models import (
    AlertEvent,
    AssetPrint,
    BriefDocument,
    CalendarEvent,
    Divergence,
    HLInstrumentState,
    MacroSnapshot,
    ThesisHook,
    WatchItem,
)
from mm_briefing.schedule import NY_TZ, SYDNEY_TZ, session_date_for


def brief_hash(markdown: str) -> str:
    return sha256_hex(markdown.replace("\r\n", "\n"))


def iso(ts: datetime) -> str:
    return ts.isoformat()


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
) -> BriefDocument:
    session_date = session_date_for(as_of)
    ny = as_of.astimezone(NY_TZ)
    syd = as_of.astimezone(SYDNEY_TZ)
    lines = [
        f"# US Pre-Open Brief — {session_date.isoformat()}",
        "",
        f"Generated: {iso(generated_at)}",
        f"As-of knowledge: {iso(as_of)} (ingested_at watermark; never published_at alone)",
        f"Session clock: {iso(ny)} ({session_tz})",
        f"Lab clock: {iso(syd)} ({lab_tz})",
        f"Data quality: {data_quality}",
        f"Macro source: {macro.source}",
        "",
        "## Overnight tape",
        "",
    ]
    lines.extend(_asset_table(macro.assets, vs="prior US close"))
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
            "",
        ]
    )
    lines.extend(_since_close_bullets(macro.assets))
    lines.extend(["", "## Macro / catalysts", ""])
    if calendar:
        for event in calendar:
            extra = f" — {event.notes}" if event.notes else ""
            lines.append(
                f"- {iso(event.when)} [{event.importance}] {event.region} {event.name}{extra}"
            )
    else:
        lines.append("- None in the look-ahead window.")
    lines.extend(["", "## Cross-asset divergences", ""])
    if divergences:
        for row in divergences:
            lines.append(f"- `{row.rule_id}` **{row.title}**: {row.detail} (evidence: {', '.join(row.evidence)})")
    else:
        lines.append("- No configured rule fired.")
    lines.extend(["", "## Hyperliquid (Market Memory)", ""])
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
        payload={"kind": "preopen", "data_quality": data_quality},
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
) -> BriefDocument:
    session_date = session_date_for(as_of)
    ny = as_of.astimezone(NY_TZ)
    syd = as_of.astimezone(SYDNEY_TZ)
    lines = [
        f"# US Close Brief — {session_date.isoformat()}",
        "",
        f"Generated: {iso(generated_at)}",
        f"As-of knowledge: {iso(as_of)} (ingested_at watermark; never published_at alone)",
        f"Session clock: {iso(ny)} ({session_tz})",
        f"Lab clock: {iso(syd)} ({lab_tz})",
        f"Data quality: {data_quality}",
        "",
        "## What moved",
        "",
    ]
    lines.extend(_asset_table(session.assets, vs="prior US close (session)"))
    lines.extend(["", "Overnight reference:", ""])
    lines.extend(_since_close_bullets(overnight.assets))
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


def _asset_table(assets: tuple[AssetPrint, ...], *, vs: str) -> list[str]:
    if not assets:
        return ["- No prints (macro snapshot empty or degraded)."]
    lines = [
        f"| Symbol | Last | Prior close | Change | {vs} | Quality |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in assets:
        if row.unit == "%":
            change = f"{row.change_bp:+.1f}bp" if row.change_bp is not None else "n/a"
        else:
            change = fmt_pct(row.change_pct)
        lines.append(
            f"| {row.symbol} | {fmt_px(row.last)} | {fmt_px(row.prior_close)} | {change} "
            f"| {row.name} | {row.data_quality} |"
        )
    return lines


def _since_close_bullets(assets: tuple[AssetPrint, ...]) -> list[str]:
    if not assets:
        return ["- No overnight prints available."]
    lines: list[str] = []
    for row in assets:
        if row.unit == "%":
            delta = f"{row.change_bp:+.1f}bp" if row.change_bp is not None else "n/a"
        else:
            delta = fmt_pct(row.change_pct)
        lines.append(f"- {row.symbol} ({row.name}): last {fmt_px(row.last)} / {delta} [{row.data_quality}]")
    return lines


def _hl_section(hl: tuple[HLInstrumentState, ...]) -> list[str]:
    if not hl:
        return ["- No Hyperliquid observations in the as-of window."]
    lines: list[str] = []
    for state in hl:
        lines.append(f"### {state.instrument} (quality={state.data_quality})")
        lines.append("")
        funding = funding_value(state)
        oi = state.metric("open_interest")
        oi_chg = oi_change_pct(state)
        basis = basis_mark_oracle(state)
        mid = state.metric("mid_px")
        liq = liquidation_size_sum(state)
        funding_id = _oid(state.metric("funding"))
        oi_id = _oid(oi)
        lines.append(f"- Funding: {_fmt_rate(funding)} (obs {funding_id})")
        oi_txt = oi.value if oi and oi.value is not None else "missing"
        oi_chg_txt = f"{oi_chg:+.2f}%" if oi_chg is not None else "n/a"
        lines.append(f"- Open interest: {oi_txt} (Δ {oi_chg_txt}; obs {oi_id})")
        lines.append(f"- Mid: {mid.value if mid and mid.value else 'n/a'} (obs {_oid(mid)})")
        lines.append(f"- Basis mark−oracle: {basis if basis is not None else 'n/a'}")
        liq_ids = ", ".join(row.observation_id for row in state.liquidations if row.observation_id) or "none"
        lines.append(f"- Liquidations (window sum): {liq:.4f} (obs {liq_ids})")
        if state.levels:
            level_txt = ", ".join(f"{name}={value}" for name, value in state.levels)
            lines.append(f"- Levels: {level_txt}")
        lines.append("")
    return lines


def _oid(metric) -> str:
    if metric is None or not metric.observation_id:
        return "none"
    return metric.observation_id


def _fmt_rate(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.6f}"
