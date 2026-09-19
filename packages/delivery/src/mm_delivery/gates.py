"""Threshold, quiet-hours, and completeness gates. Never alert without a threshold."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

from mm_common.time import as_utc
from mm_delivery.config import TelegramSettings, ThresholdSettings

REASON_OK = "ok"
REASON_NO_SEND = "no_send"
REASON_THRESHOLD_CONFIG_REQUIRED = "threshold_config_required"
REASON_THRESHOLD_NOT_MET = "threshold_not_met"
REASON_QUIET_HOURS = "quiet_hours"
REASON_DEDUPE = "dedupe_hit"
REASON_RATE_LIMITED = "rate_limited"
REASON_MISSING_TOKEN = "missing_env"
REASON_MISSING_CHAT = "missing_chat_id"
REASON_MISSING_PRINCIPAL_DM = "missing_principal_dm"
REASON_DM_IS_GROUP = "principal_dm_is_group"
REASON_DESK_DISABLED = "desk_disabled"
REASON_KIND_DISABLED = "kind_disabled"


@dataclass(frozen=True)
class GateDecision:
    allow: bool
    reason: str
    notes: tuple[str, ...] = ()

    def canonical(self) -> dict[str, str | bool | list[str]]:
        return {"allow": self.allow, "reason": self.reason, "notes": list(self.notes)}


def in_quiet_hours(now: datetime, *, start: time, end: time, tz: ZoneInfo) -> bool:
    local = as_utc(now).astimezone(tz).time()
    if start == end:
        return False
    if start < end:
        return start <= local < end
    return local >= start or local < end


def evaluate_threshold(
    settings: ThresholdSettings,
    *,
    kind: str,
    completeness_pct: float | None = None,
) -> GateDecision:
    """Refuse when thresholds are missing or the numeric gate is not met."""
    if settings.require_threshold_config and not settings.has_numeric():
        return GateDecision(
            allow=False,
            reason=REASON_THRESHOLD_CONFIG_REQUIRED,
            notes=("never alert without a numeric threshold in config/delivery/telegram.yaml",),
        )
    spec = settings.spec(kind)
    if spec is None:
        if settings.require_threshold_config:
            return GateDecision(
                allow=False,
                reason=REASON_THRESHOLD_CONFIG_REQUIRED,
                notes=(f"no threshold spec for kind={kind}",),
            )
        return GateDecision(allow=True, reason=REASON_OK)
    if not spec.enabled:
        return GateDecision(allow=False, reason=REASON_KIND_DISABLED, notes=(f"{kind} disabled in thresholds",))
    if not spec.params:
        return GateDecision(
            allow=False,
            reason=REASON_THRESHOLD_CONFIG_REQUIRED,
            notes=(f"{kind} has no numeric threshold",),
        )
    min_pct = spec.params.get("min_completeness_pct")
    if min_pct is not None and completeness_pct is not None:
        if float(completeness_pct) < float(min_pct):
            return GateDecision(
                allow=False,
                reason=REASON_THRESHOLD_NOT_MET,
                notes=(f"completeness_pct {completeness_pct} < min_completeness_pct {min_pct}",),
            )
    min_events = spec.params.get("min_events")
    if min_events is not None and kind == "alert":
        # Caller must pass completeness_pct as the event count for alerts when used.
        count = 0.0 if completeness_pct is None else float(completeness_pct)
        if count < float(min_events):
            return GateDecision(
                allow=False,
                reason=REASON_THRESHOLD_NOT_MET,
                notes=(f"alert events {count} < min_events {min_events}",),
            )
    return GateDecision(allow=True, reason=REASON_OK)


def evaluate_quiet_hours(settings: TelegramSettings, now: datetime, *, respect: bool = True) -> GateDecision:
    if not respect or not settings.quiet_hours.enabled:
        return GateDecision(allow=True, reason=REASON_OK)
    qh = settings.quiet_hours
    if in_quiet_hours(now, start=qh.start, end=qh.end, tz=qh.timezone):
        return GateDecision(
            allow=False,
            reason=REASON_QUIET_HOURS,
            notes=(f"quiet hours {qh.start.isoformat(timespec='minutes')}-{qh.end.isoformat(timespec='minutes')} {qh.timezone.key}",),
        )
    return GateDecision(allow=True, reason=REASON_OK)


def evaluate_send_gates(
    settings: TelegramSettings,
    *,
    kind: str,
    now: datetime,
    completeness_pct: float | None = None,
    desk_enabled: bool = True,
    respect_quiet_hours: bool = True,
) -> GateDecision:
    if not desk_enabled:
        return GateDecision(allow=False, reason=REASON_DESK_DISABLED)
    th = evaluate_threshold(settings.thresholds, kind=kind, completeness_pct=completeness_pct)
    if not th.allow:
        return th
    return evaluate_quiet_hours(settings, now, respect=respect_quiet_hours)
