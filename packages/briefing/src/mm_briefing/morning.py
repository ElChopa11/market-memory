"""Sydney morning / US close brief under the standing rule.

A line that says the same thing every morning is not information.
The send path is one Telegram message. Card split stays deferred.
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal

from mm_common.time import as_utc
from mm_briefing.divergences import fmt_pct, fmt_px
from mm_briefing.freshness import format_quality_with_age
from mm_briefing.health import load_presentation_config, score_data_health
from mm_briefing.hl import basis_mark_oracle, funding_value, liquidation_size_sum
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

# (reader metric, label). Mid is the headline last, so it is not repeated here.
# Funding and open interest need a prior capture; otherwise they are gaps.
_POSITION_METRICS = (
    ("funding", "Funding"),
    ("open_interest", "Open interest"),
    ("liquidations", "Liquidations (window sum)"),
)
_PRIOR_REQUIRED_METRICS = frozenset({"open_interest"})
# Hyperliquid funding docs: the interest component is 0.01% per 8 hours
# (0.0001). The formula is an 8h rate, paid each hour at one eighth.
# https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding
# Baseline hourly rate = 0.0001 / 8 = 0.0000125 (0.00125% per hour).
# Recorded asset-ctx prints use 6 decimal places. A print is on baseline when
# it is within half of 1e-6 of 0.0000125. Compared in Decimal: float subtraction
# treats 0.000012 as just outside that window. 0.000012 and 0.000013 are on
# baseline. 0.000014 is the first 6-decimal print off baseline.
HL_FUNDING_INTEREST_8H = 0.0001
HL_FUNDING_PAYMENTS_PER_8H = 8
HL_FUNDING_BASELINE_HOURLY = HL_FUNDING_INTEREST_8H / HL_FUNDING_PAYMENTS_PER_8H
HL_FUNDING_PRINT_QUANTUM = 1e-6
_HL_FUNDING_BASELINE = Decimal("0.0001") / Decimal(HL_FUNDING_PAYMENTS_PER_8H)
_HL_FUNDING_HALF_QUANTUM = Decimal(str(HL_FUNDING_PRINT_QUANTUM)) / Decimal(2)
_FUNDING_HOURS_PER_YEAR = 24 * 365
# Monospace block. A phone wraps past this. Asserted on the gate render.
PHONE_LINE_MAX = 42
# Health names only non-fresh domains. Unavailable is written n/a.
_HEALTH_EXCEPTION_ORDER = ("stale", "degraded", "unavailable")
_HEALTH_EXCEPTION_WORD = {"stale": "stale", "degraded": "degraded", "unavailable": "n/a"}
_STAMP_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})?"
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
    lead_lines: tuple[str, ...] = (),
    closing_lines: tuple[str, ...] = (),
) -> BriefDocument:
    """Render the morning brief. ``overnight`` is not reprinted (no reference block)."""
    del overnight  # the price table is the session print; the reference block is gone
    session_date = session_date_for(as_of)
    ny = generated_at.astimezone(NY_TZ)
    syd = generated_at.astimezone(SYDNEY_TZ)
    presentation = load_presentation_config()
    health = score_data_health(
        _assets_for_health(session.assets, prior_reader),
        hl,
        config=presentation,
    )
    lines: list[str] = [f"US Close {session_date.isoformat()}", ""]
    kept_leads = [lead for lead in lead_lines if not _lead_restates_generated_at(lead, generated_at)]
    for lead in kept_leads:
        lines.extend(_phone_wrap(lead))
    if kept_leads:
        lines.append("")
    lines.extend(_clock_lines(generated_at, ny, syd))
    lines.extend(_health_lines(health))
    if not _has_observation(session, hl):
        lines.append("obs none")
    lines.append("")
    price_lines, price_gaps = _price_rows(
        session.assets, knowledge_as_of=as_of, prior_reader=prior_reader
    )
    lines.extend(price_lines)
    positioning, pos_gaps = _positioning(hl, prior_reader=prior_reader, knowledge_as_of=as_of)
    gaps = [*price_gaps, *pos_gaps]
    if positioning or gaps:
        lines.append("")
        if positioning:
            lines.append("Positioning")
            lines.extend(positioning)
        if gaps:
            lines.extend(_phone_wrap("gaps: " + ", ".join(gaps)))
    unexpected_lines = _live_notes(unexpected)
    if unexpected_lines:
        lines.extend(["", "Unexpected", ""])
        lines.extend(f"- {note}" for note in unexpected_lines)
    thesis_lines = _thesis_lines(theses)
    if thesis_lines:
        lines.extend(["", "Lab hooks", ""])
        lines.extend(thesis_lines)
    assumption_lines = _live_notes(assumptions, drop=_STATIC_ASSUMPTION)
    if assumption_lines:
        lines.extend(["", "Assumptions", ""])
        lines.extend(f"- {note}" for note in assumption_lines)
    catalyst_lines = _catalyst_lines(calendar)
    if catalyst_lines:
        lines.extend(["", "Catalysts", ""])
        lines.extend(catalyst_lines)
    extras = [line.rstrip() for line in closing_lines if line.strip()]
    if extras:
        lines.append("")
        for extra in extras:
            lines.extend(_phone_wrap(extra))
    fitted = [wrapped for line in lines for wrapped in (_phone_wrap(line) or [""])]
    # One pre block. MarkdownV2 does not render pipe tables or # headings.
    # Headings are plain short lines. Status lines appended later stay outside.
    markdown = "```\n" + "\n".join(fitted).rstrip() + "\n```\n"
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


def _clock_lines(generated_at: datetime, ny: datetime, syd: datetime) -> list[str]:
    ny_name = ny.tzname() or "NY"
    syd_name = syd.tzname() or "SYD"
    return [
        f"UTC {generated_at.strftime('%Y-%m-%d %H:%MZ')}",
        f"NY {ny.strftime('%Y-%m-%d %H:%M')} {ny_name}",
        f"SYD {syd.strftime('%Y-%m-%d %H:%M')} {syd_name}",
    ]


def _health_lines(health) -> list[str]:
    """One line of exceptions. Fresh domains are omitted.

    ``Health 100%`` when every scored domain is fresh. Otherwise the percentage
    plus the domains that are not fresh, grouped by state. Unavailable is
    written ``n/a``. At most two lines, each within the phone width.
    """
    if health.insufficient or health.pct is None:
        return []
    grouped: dict[str, list[str]] = {}
    for row in health.domains:
        if row.excluded or row.state == "fresh":
            continue
        grouped.setdefault(row.state, []).append(row.label)
    parts: list[str] = []
    seen: set[str] = set()
    for state in _HEALTH_EXCEPTION_ORDER:
        names = grouped.get(state) or []
        if not names:
            continue
        seen.add(state)
        word = _HEALTH_EXCEPTION_WORD.get(state, state)
        parts.append(f"{word} {' '.join(names)}")
    for state, names in grouped.items():
        if state in seen or not names:
            continue
        parts.append(f"{state} {' '.join(names)}")
    if not parts:
        return [f"Health {health.pct}%"]
    text = f"Health {health.pct}% " + "; ".join(parts)
    wrapped = _phone_wrap(text)
    if len(wrapped) <= 2:
        return wrapped
    return _pack_two(text)


def _pack_two(text: str) -> list[str]:
    """Two lines of at most PHONE_LINE_MAX. Used when a health line is long."""
    words = [word for word in text.split(" ") if word]
    first: list[str] = []
    index = 0
    while index < len(words):
        trial = words[index] if not first else f"{' '.join(first)} {words[index]}"
        if len(trial) > PHONE_LINE_MAX:
            break
        first.append(words[index])
        index += 1
    if not first:
        first = [words[0][:PHONE_LINE_MAX]]
        index = 1
    rest = " ".join(words[index:])
    if not rest:
        return [" ".join(first)]
    if len(rest) <= PHONE_LINE_MAX:
        return [" ".join(first), rest]
    return [" ".join(first), rest[:PHONE_LINE_MAX].rstrip()]


def _lead_restates_generated_at(lead: str, generated_at: datetime) -> bool:
    """A lead whose only fact is this capture's clock is the UTC line.

    ``Now 2026-09-24T23:17:25Z`` and ``UTC 2026-09-24 23:17Z`` are one instant.
    A prior stamp, or any other words, stays.
    """
    stamps = list(_STAMP_RE.finditer(lead))
    if len(stamps) != 1:
        return False
    raw = stamps[0].group(0)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00").replace(" ", "T"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=generated_at.tzinfo)
    left = as_utc(parsed).replace(second=0, microsecond=0)
    right = as_utc(generated_at).replace(second=0, microsecond=0)
    if left != right:
        return False
    residue = _STAMP_RE.sub(" ", lead)
    words = [word.strip(" :,").lower() for word in residue.split() if word.strip(" :,")]
    return words in ([], ["now"], ["utc"])


def _assets_for_health(
    assets: tuple[AssetPrint, ...],
    prior_reader: PriorCaptureReader | None,
) -> tuple[AssetPrint, ...]:
    """Health states for the morning line.

    A missing last is unavailable, including a structural slot, so it is
    listed and weighted 0. It is not omitted and not fresh. An observation
    date that did not roll since the prior capture is stale. That phrase is
    the right change cell; the health line must not call the slot fresh.
    Stale is not a failure. Crypto is never marked stale for a repeated as-of.
    """
    adjusted: list[AssetPrint] = []
    for row in assets:
        if row.last is None:
            adjusted.append(replace(row, data_quality="unavailable", structural_unavailable=False))
            continue
        if _did_not_roll(row, prior_reader):
            adjusted.append(replace(row, data_quality="stale"))
            continue
        adjusted.append(row)
    return tuple(adjusted)


def _did_not_roll(row: AssetPrint, prior_reader: PriorCaptureReader | None) -> bool:
    symbol = row.symbol.upper()
    if symbol in _CRYPTO_SLOTS or row.last is None:
        return False
    prior = read_prior(prior_reader, symbol, _CLOSE_METRIC)
    if prior is None or prior.observation_as_of is None or row.as_of is None:
        return False
    current_day = _observation_date(row.as_of)
    prior_day = _observation_date(prior.observation_as_of)
    return current_day is not None and current_day == prior_day


def funding_on_baseline(rate: float) -> bool:
    """True when the hourly print is the HL interest baseline, at 6-decimal precision.

    The inclusive window is half of 1e-6 around 0.0000125. Both neighbors that
    a 6-decimal print can take, 0.000012 and 0.000013, are on baseline.
    0.000014 is off.
    """
    return abs(Decimal(str(rate)) - _HL_FUNDING_BASELINE) <= _HL_FUNDING_HALF_QUANTUM


def _phone_wrap(text: str) -> list[str]:
    """Break a line so each piece is at most PHONE_LINE_MAX characters.

    Leading spaces stay on every piece, so a nested bullet keeps its indent.
    """
    raw = text.rstrip()
    if raw == "":
        return [""]
    if len(raw) <= PHONE_LINE_MAX:
        return [raw]
    indent = raw[: len(raw) - len(raw.lstrip(" "))]
    body = raw[len(indent) :]
    width = PHONE_LINE_MAX - len(indent)
    if width < 8:
        indent = ""
        body = raw.lstrip(" ")
        width = PHONE_LINE_MAX
    pieces = _wrap_words(body, width)
    return [f"{indent}{piece}" if piece else indent[:PHONE_LINE_MAX] for piece in pieces]


def _wrap_words(body: str, width: int) -> list[str]:
    words = [word for word in body.split(" ") if word]
    lines: list[str] = []
    current = ""
    for word in words:
        while len(word) > width:
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:width])
            word = word[width:]
        if not word:
            continue
        trial = word if not current else f"{current} {word}"
        if len(trial) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _price_rows(
    assets: tuple[AssetPrint, ...],
    *,
    knowledge_as_of: datetime,
    prior_reader: PriorCaptureReader | None,
) -> tuple[list[str], list[str]]:
    """Headline rows. A slot with no last goes to the gaps list, not a row.

    Labels live in ``docs/specs/brief-row-labels.md``. A quality marker is
    appended only when the row is not fresh and the change cell is not
    already the no-new-session / no-new-print phrase.
    """
    by_symbol = {row.symbol.upper(): row for row in assets}
    body: list[str] = []
    gaps: list[str] = []
    for symbol in ASSET_ORDER:
        row = by_symbol.get(symbol)
        if row is None or row.last is None:
            gaps.append(symbol if row is None else display_symbol(row))
            continue
        delta = _change_cell(row, prior_reader)
        marker = ""
        if not delta.startswith((NO_NEW_SESSION_PREFIX, NO_NEW_PRINT_PREFIX)):
            marker = _row_quality_marker(row, knowledge_as_of)
        head = f"{display_symbol(row)} {fmt_px(row.last)}"
        same = f"{head} {delta}" + (f" {marker}" if marker else "")
        if len(same) <= PHONE_LINE_MAX:
            body.append(same)
        else:
            body.append(head)
            rest = delta if not marker else f"{delta} {marker}"
            body.append(rest if len(rest) <= PHONE_LINE_MAX else f" {delta}")
            if marker and len(rest) > PHONE_LINE_MAX:
                body.append(marker)
    return body, gaps


def _observation_date(value: datetime | date | None) -> date | None:
    """UTC calendar date of a vendor bar or FRED observation. Same rule as freshness age."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return as_utc(value).date()
    return value


def _row_quality_marker(row: AssetPrint, knowledge_as_of: datetime) -> str:
    """Empty when fresh. Stale keeps its age. Anything else is the state name."""
    label = format_quality_with_age(
        row.data_quality,
        observation_as_of=row.as_of,
        reference_as_of=knowledge_as_of,
    )
    if label == "fresh":
        return ""
    return label


def format_funding_annualised(rate: float | None) -> str:
    """Hourly HL funding as an annualised percent."""
    if rate is None:
        return "n/a"
    pct = rate * _FUNDING_HOURS_PER_YEAR * 100.0
    return f"{pct:.2f}% ann"


def _fmt_oi(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{round(value):,}"


def _numeric_delta(row: AssetPrint, prior: PriorCaptureValue | None) -> str:
    if row.unit == "%":
        return f"{row.change_bp:+.1f}bp" if row.change_bp is not None else "n/a"
    if row.change_pct is not None:
        return fmt_pct(row.change_pct)
    if prior is not None and prior.value not in (None, 0) and row.last is not None:
        return fmt_pct((row.last - prior.value) / prior.value * 100.0)
    return "n/a"


def _change_cell(row: AssetPrint, prior_reader: PriorCaptureReader | None) -> str:
    """Δ cell. Same observation date as the prior capture is not a 0.00% move.

    Equities use the vendor bar date (``market_time``). FRED uses the
    observation date. A later as-of with an unchanged value is a real zero.
    Crypto always prints the computed change. No prior keeps that change.
    """
    symbol = row.symbol.upper()
    prior = read_prior(prior_reader, symbol, _CLOSE_METRIC)
    numeric = _numeric_delta(row, prior)
    if symbol in _CRYPTO_SLOTS or row.last is None:
        return numeric
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


def _positioning(
    hl: tuple[HLInstrumentState, ...],
    *,
    prior_reader: PriorCaptureReader | None,
    knowledge_as_of: datetime,
) -> tuple[list[str], list[str]]:
    del knowledge_as_of
    if not hl:
        return [], []
    lines: list[str] = []
    gaps: list[str] = []
    for state in hl:
        flag = _quality_flag(state.data_quality)
        if flag:
            lines.append(f"{state.instrument} {flag}")
        for metric_name, label in _POSITION_METRICS:
            current = _metric_value(state, metric_name)
            prior = read_prior(prior_reader, state.instrument, metric_name)
            if _show_metric(metric_name, current, prior):
                lines.extend(_metric_lines(state, metric_name, label, current, prior))
            else:
                gaps.append(f"{state.instrument} {label}")
        basis_prior = read_prior(prior_reader, state.instrument, "basis")
        if basis_prior is not None:
            current_basis = basis_mark_oracle(state)
            lines.append(f"{state.instrument} basis {_fmt_num(current_basis)}")
            lines.append(f" prior {_fmt_num(basis_prior.value)}")
        level_txt = _level_text(state)
        if level_txt:
            lines.extend(_phone_wrap(f"{state.instrument} levels {level_txt}"))
    return lines, gaps


def _show_metric(
    metric_name: str,
    current: float | None,
    prior: PriorCaptureValue | None,
) -> bool:
    """Non-zero, or changed versus the prior capture.

    Open interest with no prior is a gap, even when non-zero.
    Funding is shown only when the hourly print is off the HL interest
    baseline. On baseline it is the same number every quiet morning.
    A zero that matches the prior stays on the gaps line.
    """
    if metric_name == "funding":
        return current is not None and not funding_on_baseline(current)
    if metric_name in _PRIOR_REQUIRED_METRICS and prior is None:
        return False
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


def _metric_lines(
    state: HLInstrumentState,
    metric_name: str,
    label: str,
    current: float | None,
    prior: PriorCaptureValue | None,
) -> list[str]:
    obs = _metric_obs(state, metric_name)
    obs_suffix = f" obs {obs}" if obs else ""
    if metric_name == "funding":
        lines = [f"{state.instrument} fund {format_funding_annualised(current)}"]
        if prior is not None:
            lines.append(f" prior {format_funding_annualised(prior.value)}")
    elif metric_name == "open_interest":
        lines = [f"{state.instrument} OI {_fmt_oi(current)}"]
        if prior is not None and prior.value not in (None, 0) and current is not None:
            delta = (current - prior.value) / prior.value * 100.0
            lines.append(f" prior {_fmt_oi(prior.value)} {delta:+.2f}%")
    else:
        lines = [f"{state.instrument} {label} {_fmt_num(current)}"]
    if obs_suffix:
        lines[-1] += obs_suffix
    return lines


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
