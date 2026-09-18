"""EVENT_RISK: high-impact calendar proximity. Config-driven. No LLM."""

from __future__ import annotations

from datetime import datetime

from mm_common.time import as_utc
from mm_macro.config import MacroConfig
from mm_macro.models import CalendarEvent, EventRiskTag
from mm_macro.series import visible_events

EVENT_RISK_RULE = "event_risk"


def event_risk_at(
    events: tuple[CalendarEvent, ...] | list[CalendarEvent],
    *,
    watermark: datetime,
    config: MacroConfig,
) -> EventRiskTag:
    spec = config.event_risk
    cut = as_utc(watermark)
    visible = visible_events(events, cut)
    high = {item.lower() for item in spec.high_importance}
    tokens = tuple(token.lower() for token in spec.cb_name_tokens)
    closest: tuple[float, CalendarEvent] | None = None
    for row in visible:
        if row.importance.lower() not in high:
            continue
        name_l = row.name.lower()
        if tokens and not any(token.lower() in name_l for token in tokens):
            # High-importance is enough; tokens are extra CB/econ hints, not a filter that drops CPI.
            pass
        minutes = abs((row.when - cut).total_seconds()) / 60.0
        if closest is None or minutes < closest[0]:
            closest = (minutes, row)
    if closest is None:
        return EventRiskTag(
            tagged=False,
            rule_id=spec.rule_id or EVENT_RISK_RULE,
            window_minutes=spec.window_minutes,
            as_of_knowledge=cut,
            size_haircut_pct=spec.size_haircut_pct,
            reason="no high-impact calendar event visible at watermark",
        )
    minutes, row = closest
    tagged = minutes <= spec.window_minutes
    return EventRiskTag(
        tagged=tagged,
        rule_id=spec.rule_id or EVENT_RISK_RULE,
        window_minutes=spec.window_minutes,
        as_of_knowledge=cut,
        event_name=row.name,
        event_when=row.when.isoformat(),
        minutes_to_event=minutes,
        size_haircut_pct=spec.size_haircut_pct if tagged else None,
        reason=(
            f"within {spec.window_minutes}m of high-impact {row.name}"
            if tagged
            else f"nearest high-impact {row.name} is {minutes:.1f}m away (outside window)"
        ),
    )
