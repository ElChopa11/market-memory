"""Sydney morning / US close brief under the standing rule.

A line that says the same thing every morning is not information.
The send path is one Telegram message. Card split stays deferred.
"""

from __future__ import annotations

from datetime import date, datetime

from mm_common.time import as_utc
from mm_briefing.divergences import fmt_pct, fmt_px
from mm_briefing.freshness import format_quality_with_age
from mm_briefing.health import load_presentation_config, score_data_health
from mm_briefing.hl import basis_mark_oracle, funding_value, liquidation_size_sum, oi_change_pct
from mm_briefing.models import (
    ASSET_ORDER,
    AssetPrint,
    BriefDocument,
    CalendarEvent,
    HLInstrumentState,
    HLMetric,
    MacroSnapshot,
    ThesisHook,
    display_symbol,
    pulse_quality,
)
from mm_briefing.prior import PriorCaptureReader, PriorCaptureValue, read_prior
from mm_briefing.render import brief_hash, iso
from mm_briefing.schedule import NY_TZ, SYDNEY_TZ, session_date_for

# Fixed sentences the morning brief must never render.
FORBIDDEN_RENDER_FRAGMENTS = (
    "KEY TAKEAWAY",
    "INSUFFICIENT DATA",
    "Nothing crossed the unexpected-move rules",
    "No indexed theses to score against this session",
    "No named macro assumption flipped vs the overnight tape",
    "Monitor into Asia",
    "Monitor into Europe",
    "Overnight reference:",
    "Asia: BTC/ETH funding",
    "Europe: whether the USD/yields",
    "No dated catalysts remaining",
    "MACRO TRANSMISSION",
    "TRANSMISSION CHAIN",
    "CRYPTO TAPE",
    "CLUSTER LEADERSHIP",
    "BTC vs NDX",
)

_STATIC_ASSUMPTION = "No named macro assumption flipped vs the overnight tape"

# Price-row Δ is decided by the observation date, not by whether the number moved.
_CRYPTO_SLOTS = frozenset({"BTC", "ETH"})
_SESSION_SLOTS = frozenset({"ES", "NQ", "DXY", "CL"})
_CLOSE_METRIC = "close"
NO_NEW_SESSION_PREFIX = "no new session since"
NO_NEW_PRINT_PREFIX = "no new print since"

# (reader metric, label, value getter name)
_POSITION_METRICS = (
    ("funding", "Funding"),
    ("open_interest", "Open interest"),
    ("mid_px", "Mid"),
    ("liquidations", "Liquidations (window sum)"),
)


def render_morning_close(
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
    prior_reader: PriorCaptureReader | None = None,
) -> BriefDocument:
    """Render the morning brief. ``overnight`` is not reprinted (no reference block)."""
    del overnight  # the price table is the session print; the reference block is gone
    session_date = session_date_for(as_of)
    ny = generated_at.astimezone(NY_TZ)
    syd = generated_at.astimezone(SYDNEY_TZ)
    presentation = load_presentation_config()
    health = score_data_health(session.assets, hl, config=presentation)
    lines: list[str] = [
        f"# US Close Brief — {session_date.isoformat()}",
        "",
        (
            f"UTC {iso(generated_at)} | New York {iso(ny)} ({ny.tzname() or session_tz}) | "
            f"Sydney {iso(syd)} ({syd.tzname() or lab_tz})"
        ),
        f"As-of knowledge: {iso(as_of)}",
    ]
    health_line = health.morning_line(icons=presentation.icons)
    if health_line:
        lines.append(health_line)
    if not _has_observation(session, hl):
        lines.append("obs none")
    lines.append("")
    lines.extend(_price_rows(session.assets, knowledge_as_of=as_of, prior_reader=prior_reader))
    positioning = _positioning(hl, prior_reader=prior_reader, knowledge_as_of=as_of)
    if positioning:
        lines.extend(["", "## Positioning", ""])
        lines.extend(positioning)
    unexpected_lines = _live_notes(unexpected)
    if unexpected_lines:
        lines.extend(["", "## Unexpected", ""])
        lines.extend(f"- {note}" for note in unexpected_lines)
    thesis_lines = _thesis_lines(theses)
    if thesis_lines:
        lines.extend(["", "## Lab hooks", ""])
        lines.extend(thesis_lines)
    assumption_lines = _live_notes(assumptions, drop=_STATIC_ASSUMPTION)
    if assumption_lines:
        lines.extend(["", "## Assumptions", ""])
        lines.extend(f"- {note}" for note in assumption_lines)
    catalyst_lines = _catalyst_lines(calendar)
    if catalyst_lines:
        lines.extend(["", "## Catalysts", ""])
        lines.extend(catalyst_lines)
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
        payload={"kind": "close", "data_quality": data_quality, "template": "brief-v2-morning"},
    )


def _price_rows(
    assets: tuple[AssetPrint, ...],
    *,
    knowledge_as_of: datetime,
    prior_reader: PriorCaptureReader | None,
) -> list[str]:
    by_symbol = {row.symbol.upper(): row for row in assets}
    lines = [
        "| Symbol | Last | Δ | Source | Quality | Label |",
        "|---|---:|---:|---|---|---|",
    ]
    for symbol in ASSET_ORDER:
        row = by_symbol.get(symbol)
        if row is None:
            row = AssetPrint(
                symbol=symbol,
                name=symbol,
                last=None,
                prior_close=None,
                data_quality="unavailable",
                source="none",
                as_of=knowledge_as_of,
            )
        delta = _change_cell(row, prior_reader)
        quality = format_quality_with_age(
            row.data_quality,
            observation_as_of=row.as_of,
            reference_as_of=knowledge_as_of,
        )
        lines.append(
            f"| {display_symbol(row)} | {fmt_px(row.last)} | {delta} | {row.source} | {quality} | {_label(row)} |"
        )
    return lines


def _observation_date(value: datetime | date | None) -> date | None:
    """UTC calendar date of a vendor bar or FRED observation. Same rule as freshness age."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return as_utc(value).date()
    return value


def _numeric_delta(row: AssetPrint) -> str:
    if row.unit == "%":
        return f"{row.change_bp:+.1f}bp" if row.change_bp is not None else "n/a"
    return fmt_pct(row.change_pct)


def _change_cell(row: AssetPrint, prior_reader: PriorCaptureReader | None) -> str:
    """Δ cell. Same observation date as the prior capture is not a 0.00% move.

    Equities use the vendor bar date (``market_time``). FRED uses the
    observation date. A later as-of with an unchanged value is a real zero.
    Crypto always prints the computed change. No prior keeps that change.
    """
    numeric = _numeric_delta(row)
    symbol = row.symbol.upper()
    if symbol in _CRYPTO_SLOTS or row.last is None:
        return numeric
    prior = read_prior(prior_reader, symbol, _CLOSE_METRIC)
    if prior is None or prior.observation_as_of is None or row.as_of is None:
        return numeric
    current_day = _observation_date(row.as_of)
    prior_day = _observation_date(prior.observation_as_of)
    if current_day is None or prior_day is None or current_day != prior_day:
        return numeric
    if symbol == "US10Y" or (row.source or "").lower() == "fred":
        return f"{NO_NEW_PRINT_PREFIX} {current_day.isoformat()}"
    if symbol in _SESSION_SLOTS:
        return f"{NO_NEW_SESSION_PREFIX} {current_day.isoformat()}"
    return numeric


def _label(row: AssetPrint) -> str:
    name = row.name.strip() or row.symbol
    shown = display_symbol(row)
    if shown.upper() != row.symbol.upper() and "proxy" not in name.lower():
        return f"{name} (proxy for {row.symbol})"
    return name


def _positioning(
    hl: tuple[HLInstrumentState, ...],
    *,
    prior_reader: PriorCaptureReader | None,
    knowledge_as_of: datetime,
) -> list[str]:
    del knowledge_as_of
    if not hl:
        return []
    lines: list[str] = []
    gaps: list[str] = []
    for state in hl:
        flag = _quality_flag(state.data_quality)
        if flag:
            lines.append(f"{state.instrument} {flag}")
        for metric_name, label in _POSITION_METRICS:
            current = _metric_value(state, metric_name)
            prior = read_prior(prior_reader, state.instrument, metric_name)
            if _show_metric(current, prior):
                lines.append(_metric_line(state, metric_name, label, current))
            else:
                gaps.append(f"{state.instrument} {label}")
        basis_prior = read_prior(prior_reader, state.instrument, "basis")
        if basis_prior is not None:
            current_basis = basis_mark_oracle(state)
            lines.append(
                f"{state.instrument} Basis mark−oracle: {_fmt_num(current_basis)} "
                f"(prior {_fmt_num(basis_prior.value)})"
            )
        level_txt = _level_text(state)
        if level_txt:
            lines.append(f"{state.instrument} Levels: {level_txt}")
    if gaps:
        lines.append("gaps: " + ", ".join(gaps))
    return lines


def _show_metric(current: float | None, prior: PriorCaptureValue | None) -> bool:
    """Non-zero, or changed versus the prior capture. No prior → non-zero only."""
    if _nonzero(current):
        return True
    if prior is None:
        return False
    return not _same_number(current, prior.value)


def _nonzero(value: float | None) -> bool:
    return value is not None and value != 0


def _same_number(left: float | None, right: float | None) -> bool:
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    scale = max(1.0, abs(left), abs(right))
    return abs(left - right) <= 1e-9 * scale


def _metric_value(state: HLInstrumentState, metric_name: str) -> float | None:
    if metric_name == "funding":
        return funding_value(state)
    if metric_name == "liquidations":
        if not state.liquidations:
            return 0.0
        return liquidation_size_sum(state)
    metric = state.metric(metric_name)
    if metric is None or metric.value is None:
        return None
    try:
        return float(metric.value)
    except ValueError:
        return None


def _metric_line(state: HLInstrumentState, metric_name: str, label: str, current: float | None) -> str:
    text = f"{state.instrument} {label}: {_fmt_metric(metric_name, current)}"
    if metric_name == "open_interest":
        delta = oi_change_pct(state)
        if delta is not None:
            text += f" Δ {delta:+.2f}%"
    obs = _metric_obs(state, metric_name)
    if obs:
        text += f" obs {obs}"
    return text


def _fmt_metric(metric_name: str, value: float | None) -> str:
    if value is None:
        return "n/a"
    if metric_name == "funding":
        return f"{value:.6f}"
    return _fmt_num(value)


def _fmt_num(value: float | None) -> str:
    if value is None:
        return "n/a"
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text if text not in {"", "-"} else "0"


def _metric_obs(state: HLInstrumentState, metric_name: str) -> str:
    if metric_name == "liquidations":
        ids = [row.observation_id for row in state.liquidations if row.observation_id]
        return ",".join(ids)
    metric: HLMetric | None = state.metric(metric_name)
    if metric is None or not metric.observation_id:
        return ""
    return metric.observation_id


def _level_text(state: HLInstrumentState) -> str:
    kept = [(name, value) for name, value in state.levels if "basis" not in name.lower()]
    if not kept:
        return ""
    return ", ".join(f"{name}={value}" for name, value in kept)


def _quality_flag(quality: str) -> str:
    """Staleness / degraded / unavailable only. Fresh is the quiet default."""
    label = pulse_quality(quality)
    if label == "fresh":
        return ""
    if label == "partial":
        return "degraded"
    return label


def _has_observation(session: MacroSnapshot, hl: tuple[HLInstrumentState, ...]) -> bool:
    for row in session.assets:
        if row.observation_id:
            return True
    for state in hl:
        if state.observation_ids():
            return True
    return False


def _live_notes(notes: tuple[str, ...], *, drop: str | None = None) -> tuple[str, ...]:
    kept: list[str] = []
    for note in notes:
        text = note.strip()
        if not text:
            continue
        if drop is not None and text == drop:
            continue
        if any(fragment in text for fragment in FORBIDDEN_RENDER_FRAGMENTS):
            continue
        kept.append(text)
    return tuple(kept)


def _thesis_lines(theses: tuple[ThesisHook, ...]) -> list[str]:
    lines: list[str] = []
    for thesis in theses:
        inst = thesis.instrument or "n/a"
        lines.append(
            f"- `{thesis.slug}` status={thesis.status} instrument={inst}: {thesis.verdict_hook}"
        )
        if thesis.invalidation_summary:
            lines.append(f"  - Invalidation: {thesis.invalidation_summary}")
        if thesis.hypothesis:
            lines.append(f"  - Hypothesis: {thesis.hypothesis}")
    return lines


def _catalyst_lines(calendar: tuple[CalendarEvent, ...]) -> list[str]:
    lines: list[str] = []
    for event in calendar:
        extra = f" — {event.notes}" if event.notes else ""
        lines.append(f"- {iso(event.when)} [{event.importance}] {event.name}{extra}")
    return lines
