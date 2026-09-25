"""Scheduler miss sweep (IMP-042). This is the control, not a log.

For each configured routine: if the window is closed and no completion
row exists → missed. Heartbeat-on-fire is secondary.

Ops-owned. Must not depend on the execution package, sign, or talk to Telegram live.
Canaries are out of scope and are never loaded from this catalog.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

import yaml

from mm_common.time import OPS_TZ, as_utc, in_ops_tz, parse_utc

UTC = timezone.utc
WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
STATUSES = ("ok", "early", "late", "missed", "skipped", "wrong_anchor")
FAMILIES = ("lab", "grok_bot")
CANARY_MARKERS = ("canary",)
DEFAULT_LATE_AFTER = 300
DEFAULT_MISS_AFTER = 900
DEFAULT_LOOKBACK_DAYS = 14
ROUTINES_REL = Path("config") / "schedules" / "routines.yaml"
PULSE_REL = Path("config") / "schedules" / "market-pulse.yaml"
TELEGRAM_REL = Path("config") / "delivery" / "telegram.yaml"
BASELINE_REL = Path("ops") / "reports" / "scheduler" / "known-missed-baseline.yaml"
BASELINE_ENV = "MM_SCHEDULE_BASELINE_FILE"
KNOWN_MISSED_LABEL = "known-missed"
WRONG_ANCHOR_REASON = "fired_on_unscheduled_weekday"
STATUS_RANK = {"ok": 5, "late": 4, "early": 3, "skipped": 2, "wrong_anchor": 1, "missed": 0}
FIRE_STATUSES = frozenset({"ok", "early", "late", "skipped"})


class WrongAnchorError(ValueError):
    """Anchor cannot be derived for this fire. Must not write a completion row.

    Distinguishes stamp-refused from silence (no CLI) and from a failed CLI that
    still wrote a fire (exit_status != 0 on a scheduled day).
    """

    def __init__(self, payload: Mapping[str, Any]) -> None:
        self.payload = dict(payload)
        super().__init__(str(self.payload.get("reason") or WRONG_ANCHOR_REASON))

    def as_public_dict(self) -> dict[str, Any]:
        return dict(self.payload)


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "packages").is_dir():
            return candidate
    return here


def parse_hhmm(value: str) -> time:
    parts = str(value).strip().split(":")
    if len(parts) < 2:
        raise ValueError(f"invalid local_time {value!r}; expected HH:MM")
    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2]) if len(parts) > 2 else 0
    return time(hour, minute, second)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _is_canary(routine_id: str, display: str = "") -> bool:
    blob = f"{routine_id} {display}".lower()
    return any(marker in blob for marker in CANARY_MARKERS)


@dataclass(frozen=True)
class Routine:
    routine_id: str
    family: str
    timezone: str
    local_time: time
    weekdays: tuple[str, ...]
    enabled: bool
    display: str = ""
    incident: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    late_after_seconds: int = DEFAULT_LATE_AFTER
    miss_after_seconds: int = DEFAULT_MISS_AFTER
    notes: str = ""
    source: str = ""

    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


@dataclass(frozen=True)
class Completion:
    routine_id: str
    run_id: str
    scheduled_anchor_ts: datetime
    fired_at_ts: datetime | None
    delta_seconds: int | None
    status: str
    as_of_knowledge: datetime
    source: str = "fixture"
    exit_status: int | None = None
    payload_path: str | None = None
    cli: str | None = None
    reason: str | None = None

    def canonical(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "routine_id": self.routine_id,
            "run_id": self.run_id,
            "scheduled_anchor_ts": as_utc(self.scheduled_anchor_ts).isoformat(),
            "fired_at_ts": None if self.fired_at_ts is None else as_utc(self.fired_at_ts).isoformat(),
            "delta_seconds": self.delta_seconds,
            "status": self.status,
            "as_of_knowledge": as_utc(self.as_of_knowledge).isoformat(),
            "source": self.source,
        }
        extra: dict[str, Any] = {}
        if self.exit_status is not None:
            payload["exit_status"] = int(self.exit_status)
            extra["exit_status"] = int(self.exit_status)
        if self.payload_path:
            payload["payload_path"] = self.payload_path
            extra["payload_path"] = self.payload_path
        if self.cli:
            payload["cli"] = self.cli
            extra["cli"] = self.cli
        if self.reason:
            payload["reason"] = self.reason
            extra["reason"] = self.reason
        if extra:
            payload["payload_json"] = extra
        return payload


@dataclass(frozen=True)
class Catalog:
    routines: tuple[Routine, ...]
    late_after_seconds: int = DEFAULT_LATE_AFTER
    miss_after_seconds: int = DEFAULT_MISS_AFTER
    lookback_days: int = DEFAULT_LOOKBACK_DAYS
    lab_timezone: str = "Australia/Sydney"

    def by_id(self) -> dict[str, Routine]:
        return {row.routine_id: row for row in self.routines}

    def enabled(self) -> tuple[Routine, ...]:
        return tuple(row for row in self.routines if row.enabled)


@dataclass(frozen=True)
class Miss:
    routine_id: str
    family: str
    scheduled_anchor_ts: datetime
    window_closed_at: datetime
    incident: str | None
    reason: str
    label: str | None = None

    def canonical(self) -> dict[str, Any]:
        payload = {
            "routine_id": self.routine_id,
            "family": self.family,
            "scheduled_anchor_ts": as_utc(self.scheduled_anchor_ts).isoformat(),
            "window_closed_at": as_utc(self.window_closed_at).isoformat(),
            "incident": self.incident,
            "reason": self.reason,
            "status": "missed",
        }
        if self.label:
            payload["label"] = self.label
        return payload


@dataclass(frozen=True)
class SweepResult:
    now: datetime
    as_of_knowledge: datetime
    misses: tuple[Miss, ...]
    pending: tuple[dict[str, Any], ...]
    ok: tuple[dict[str, Any], ...]
    late: tuple[dict[str, Any], ...]
    skipped: tuple[dict[str, Any], ...]
    routines_checked: tuple[str, ...]
    artifact_path: str | None = None
    control: str = "miss_sweep"
    known_missed: tuple[Miss, ...] = ()
    wrong_anchor: tuple[dict[str, Any], ...] = ()
    baseline_path: str | None = None
    baseline_before: str | None = None
    early: tuple[dict[str, Any], ...] = ()

    def with_artifact(self, path: str) -> SweepResult:
        return SweepResult(
            now=self.now,
            as_of_knowledge=self.as_of_knowledge,
            misses=self.misses,
            pending=self.pending,
            ok=self.ok,
            late=self.late,
            skipped=self.skipped,
            routines_checked=self.routines_checked,
            artifact_path=path,
            control=self.control,
            known_missed=self.known_missed,
            wrong_anchor=self.wrong_anchor,
            baseline_path=self.baseline_path,
            baseline_before=self.baseline_before,
            early=self.early,
        )

    @property
    def escalated(self) -> bool:
        return bool(self.misses)

    def canonical(self) -> dict[str, Any]:
        return {
            "control": self.control,
            "now": as_utc(self.now).isoformat(),
            "as_of_knowledge": as_utc(self.as_of_knowledge).isoformat(),
            "escalated": self.escalated,
            "n_missed": len(self.misses),
            "n_known_missed": len(self.known_missed),
            "n_ok": len(self.ok),
            "n_early": len(self.early),
            "n_late": len(self.late),
            "n_pending": len(self.pending),
            "n_skipped": len(self.skipped),
            "n_wrong_anchor": len(self.wrong_anchor),
            "routines_checked": list(self.routines_checked),
            "misses": [row.canonical() for row in self.misses],
            "known_missed": [row.canonical() for row in self.known_missed],
            "ok": list(self.ok),
            "early": list(self.early),
            "late": list(self.late),
            "pending": list(self.pending),
            "skipped": list(self.skipped),
            "wrong_anchor": list(self.wrong_anchor),
            "artifact_path": self.artifact_path,
            "baseline_path": self.baseline_path,
            "baseline_before": self.baseline_before,
            "heartbeat_is_not_the_check": True,
        }


def delta_seconds(anchor: datetime, fired: datetime) -> int:
    """Signed seconds: fired - anchor. Negative = early vs anchor."""
    return int((as_utc(fired) - as_utc(anchor)).total_seconds())


def classify_delta(delta: int, late_after_seconds: int) -> str:
    """ok inside grace; early if the fire is before the anchor; late if after.

    Grace is symmetric: ``|delta| <= late_after_seconds`` is ``ok``. Outside
    grace, a negative delta (fired before the anchor) is ``early`` and a
    positive delta is ``late``. Wrong-day / unscheduled weekday is neither —
    use scheduled_slot + stamp_fire (no completion row).
    """
    grace = int(late_after_seconds)
    signed = int(delta)
    if abs(signed) <= grace:
        return "ok"
    if signed < 0:
        return "early"
    return "late"


def classify_fire(anchor: datetime, fired: datetime, late_after_seconds: int) -> tuple[int, str]:
    delta = delta_seconds(anchor, fired)
    return delta, classify_delta(delta, late_after_seconds)


def window_closed(anchor: datetime, now: datetime, miss_after_seconds: int) -> bool:
    return as_utc(now) >= as_utc(anchor) + timedelta(seconds=int(miss_after_seconds))


def local_anchor(routine: Routine, day: date) -> datetime:
    local = datetime(
        day.year,
        day.month,
        day.day,
        routine.local_time.hour,
        routine.local_time.minute,
        routine.local_time.second,
        tzinfo=routine.tz(),
    )
    return local.astimezone(UTC)


def sydney_calendar_date(value: datetime) -> date:
    """Australia/Sydney calendar date of a timestamptz (ops timezone)."""
    return in_ops_tz(value).date()


def scheduled_slot(routine: Routine, fired_at: datetime) -> tuple[datetime, bool, str]:
    """Catalog local_time on the fire's local calendar date in the routine timezone.

    Returns (anchor_utc, weekday_ok, local_weekday). Does *not* walk back to the
    previous scheduled weekday — that mis-keyed Sunday 06:30 AEST onto Friday
    and classified a ~2d offset as mere ``late``.
    """
    fired = as_utc(fired_at)
    local = fired.astimezone(routine.tz())
    day = local.date()
    weekday = WEEKDAY_NAMES[day.weekday()]
    return local_anchor(routine, day), weekday in routine.weekdays, weekday


def anchors_between(routine: Routine, start: datetime, end: datetime) -> tuple[datetime, ...]:
    """Inclusive start, exclusive end. DST via zoneinfo."""
    start_u = as_utc(start)
    end_u = as_utc(end)
    tz = routine.tz()
    start_local = start_u.astimezone(tz).date() - timedelta(days=1)
    end_local = end_u.astimezone(tz).date() + timedelta(days=1)
    out: list[datetime] = []
    day = start_local
    while day <= end_local:
        weekday = WEEKDAY_NAMES[day.weekday()]
        if weekday in routine.weekdays:
            when = local_anchor(routine, day)
            if start_u <= when < end_u:
                out.append(when)
        day += timedelta(days=1)
    return tuple(out)


def closed_anchors(routine: Routine, now: datetime, *, lookback_days: int) -> tuple[datetime, ...]:
    now_u = as_utc(now)
    start = now_u - timedelta(days=int(lookback_days))
    rows = anchors_between(routine, start, now_u + timedelta(seconds=1))
    return tuple(ts for ts in rows if window_closed(ts, now_u, routine.miss_after_seconds))


def _optional_ts(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    return parse_utc(str(value))


def _weekdays(raw: Any) -> tuple[str, ...]:
    if not raw:
        return ("Mon", "Tue", "Wed", "Thu", "Fri")
    return tuple(str(item) for item in raw)


def routine_from_mapping(
    row: Mapping[str, Any],
    *,
    late_after_seconds: int,
    miss_after_seconds: int,
    source: str,
) -> Routine | None:
    routine_id = str(row.get("id") or row.get("routine_id") or "").strip()
    display = str(row.get("display") or "")
    if not routine_id or _is_canary(routine_id, display):
        return None
    family = str(row.get("family") or "lab").strip()
    if family not in FAMILIES:
        raise ValueError(f"{routine_id}: unknown family {family!r}")
    incident = row.get("incident")
    return Routine(
        routine_id=routine_id,
        family=family,
        timezone=str(row.get("timezone") or "Australia/Sydney"),
        local_time=parse_hhmm(str(row.get("local_time") or "00:00")),
        weekdays=_weekdays(row.get("weekdays")),
        enabled=bool(row.get("enabled", True)),
        display=display or routine_id,
        incident=None if not incident else str(incident),
        created_at=_optional_ts(row.get("created_at")),
        updated_at=_optional_ts(row.get("updated_at")),
        late_after_seconds=int(row.get("late_after_seconds") or late_after_seconds),
        miss_after_seconds=int(row.get("miss_after_seconds") or miss_after_seconds),
        notes=str(row.get("notes") or "").strip(),
        source=str(row.get("source") or source),
    )


def _pulse_routines(root: Path, late_after: int, miss_after: int) -> list[Routine]:
    data = _load_yaml(root / PULSE_REL)
    briefs = data.get("briefs") or {}
    session_tz = str(data.get("session_timezone") or "America/New_York")
    out: list[Routine] = []
    for kind, key, default_time in (
        ("lab.pulse.preopen", "pre_open", "08:00"),
        ("lab.pulse.close", "close", "16:15"),
    ):
        spec = briefs.get(key) or {}
        if not isinstance(spec, dict):
            continue
        mapped = {
            "id": kind,
            "family": "lab",
            "display": f"Market Pulse {key}",
            "timezone": session_tz,
            "local_time": str(spec.get("local_time") or default_time),
            "weekdays": spec.get("weekdays") or ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "enabled": bool(spec.get("enabled", False)),
            "source": str(PULSE_REL),
        }
        row = routine_from_mapping(mapped, late_after_seconds=late_after, miss_after_seconds=miss_after, source=str(PULSE_REL))
        if row is not None:
            out.append(row)
    return out


def _telegram_routines(root: Path, late_after: int, miss_after: int) -> list[Routine]:
    data = _load_yaml(root / TELEGRAM_REL)
    schedule = data.get("schedule") or {}
    if not isinstance(schedule, dict):
        return []
    tz = str(schedule.get("timezone") or "Australia/Sydney")
    out: list[Routine] = []
    for name, spec in schedule.items():
        if name in {"timezone", "enabled"} or not isinstance(spec, dict):
            continue
        mapped = {
            "id": f"lab.delivery.{name}",
            "family": "lab",
            "display": f"Telegram {name}",
            "timezone": tz,
            "local_time": str(spec.get("local_time") or "00:00"),
            "weekdays": spec.get("weekdays") or ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "enabled": bool(spec.get("enabled", False)),
            "source": str(TELEGRAM_REL),
        }
        row = routine_from_mapping(mapped, late_after_seconds=late_after, miss_after_seconds=miss_after, source=str(TELEGRAM_REL))
        if row is not None:
            out.append(row)
    return out


def _grok_routines(root: Path, late_after: int, miss_after: int) -> tuple[list[Routine], dict[str, int], str]:
    data = _load_yaml(root / ROUTINES_REL)
    late = int(data.get("late_after_seconds") or late_after)
    miss = int(data.get("miss_after_seconds") or miss_after)
    lookback = int(data.get("lookback_days") or DEFAULT_LOOKBACK_DAYS)
    lab_tz = str(data.get("lab_timezone") or "Australia/Sydney")
    out: list[Routine] = []
    for raw in data.get("routines") or []:
        if not isinstance(raw, dict):
            continue
        row = routine_from_mapping(raw, late_after_seconds=late, miss_after_seconds=miss, source=str(ROUTINES_REL))
        if row is not None:
            out.append(row)
    return out, {"late_after_seconds": late, "miss_after_seconds": miss, "lookback_days": lookback}, lab_tz


def load_catalog(root: Path | None = None) -> Catalog:
    base = repo_root(root)
    grok, defaults, lab_tz = _grok_routines(base, DEFAULT_LATE_AFTER, DEFAULT_MISS_AFTER)
    late = int(defaults["late_after_seconds"])
    miss = int(defaults["miss_after_seconds"])
    lookback = int(defaults["lookback_days"])
    lab = _pulse_routines(base, late, miss) + _telegram_routines(base, late, miss)
    merged: dict[str, Routine] = {}
    for row in [*lab, *grok]:
        if _is_canary(row.routine_id, row.display):
            continue
        merged[row.routine_id] = row
    return Catalog(
        routines=tuple(merged.values()),
        late_after_seconds=late,
        miss_after_seconds=miss,
        lookback_days=lookback,
        lab_timezone=lab_tz,
    )


def completion_from_mapping(row: Mapping[str, Any], *, catalog: Catalog | None = None) -> Completion:
    routine_id = str(row["routine_id"])
    fired_raw = row.get("fired_at_ts")
    fired = None if fired_raw in (None, "") else parse_utc(str(fired_raw))
    nested = row.get("payload_json") if isinstance(row.get("payload_json"), dict) else {}
    exit_raw = row.get("exit_status", nested.get("exit_status") if nested else None)
    payload_path = row.get("payload_path") or (nested.get("payload_path") if nested else None)
    cli = row.get("cli") or (nested.get("cli") if nested else None)
    reason_raw = row.get("reason") or (nested.get("reason") if nested else None)
    run_id = str(row.get("run_id") or "")
    source = str(row.get("source") or "fixture")
    as_of_raw = row.get("as_of_knowledge") or row.get("fired_at_ts") or row.get("scheduled_anchor_ts")
    if catalog is not None and fired is not None:
        routine = catalog.by_id().get(routine_id)
        if routine is not None:
            return stamp_fire(
                routine,
                fired_at=fired,
                run_id=run_id or f"{routine_id}-{fired.strftime('%Y%m%dT%H%M%SZ')}",
                as_of_knowledge=parse_utc(str(as_of_raw)) if as_of_raw else fired,
                source=source,
                exit_status=None if exit_raw in (None, "") else int(exit_raw),
                payload_path=None if not payload_path else str(payload_path),
                cli=None if not cli else str(cli),
            )
    if str(row.get("status") or "") == "wrong_anchor":
        raise WrongAnchorError(
            {
                "error": "wrong_anchor",
                "reason": reason_raw or WRONG_ANCHOR_REASON,
                "wrote": False,
                "routine_id": routine_id,
            }
        )
    anchor = parse_utc(str(row["scheduled_anchor_ts"]))
    status = str(row.get("status") or "")
    delta = row.get("delta_seconds")
    late_after = DEFAULT_LATE_AFTER
    if catalog is not None:
        routine = catalog.by_id().get(routine_id)
        if routine is not None:
            late_after = routine.late_after_seconds
    if fired is not None:
        computed, classified = classify_fire(anchor, fired, late_after)
        if delta is None:
            delta = computed
        if not status:
            status = classified
    elif not status:
        status = "missed"
    if status not in STATUSES:
        raise ValueError(f"unknown heartbeat status {status!r}")
    as_of = parse_utc(str(as_of_raw or row["scheduled_anchor_ts"]))
    return Completion(
        routine_id=routine_id,
        run_id=run_id or f"{routine_id}-{as_utc(anchor).strftime('%Y%m%dT%H%M%SZ')}",
        scheduled_anchor_ts=anchor,
        fired_at_ts=fired,
        delta_seconds=None if delta is None else int(delta),
        status=status,
        as_of_knowledge=as_of,
        source=source,
        exit_status=None if exit_raw in (None, "") else int(exit_raw),
        payload_path=None if not payload_path else str(payload_path),
        cli=None if not cli else str(cli),
        reason=None if not reason_raw else str(reason_raw),
    )


def load_fixture(path: Path, *, root: Path | None = None) -> tuple[Catalog, tuple[Completion, ...], datetime | None]:
    data = _load_yaml(path)
    base = repo_root(root)
    catalog = load_catalog(base)
    if data.get("routines"):
        late = int(data.get("late_after_seconds") or catalog.late_after_seconds)
        miss = int(data.get("miss_after_seconds") or catalog.miss_after_seconds)
        lookback = int(data.get("lookback_days") or catalog.lookback_days)
        rows: list[Routine] = []
        for raw in data.get("routines") or []:
            if not isinstance(raw, dict):
                continue
            row = routine_from_mapping(raw, late_after_seconds=late, miss_after_seconds=miss, source=str(path))
            if row is not None:
                rows.append(row)
        catalog = Catalog(
            routines=tuple(rows),
            late_after_seconds=late,
            miss_after_seconds=miss,
            lookback_days=lookback,
            lab_timezone=str(data.get("lab_timezone") or catalog.lab_timezone),
        )
    completions = tuple(
        completion_from_mapping(raw, catalog=catalog)
        for raw in (data.get("completions") or [])
        if isinstance(raw, dict)
    )
    now = None if not data.get("now") else parse_utc(str(data["now"]))
    return catalog, completions, now


def _index_completions(rows: Iterable[Completion]) -> dict[tuple[str, datetime], Completion]:
    """Best status wins: ok/late/skipped beat missed for the same anchor."""
    out: dict[tuple[str, datetime], Completion] = {}
    for row in rows:
        key = (row.routine_id, as_utc(row.scheduled_anchor_ts))
        prev = out.get(key)
        if prev is None or STATUS_RANK.get(row.status, 0) >= STATUS_RANK.get(prev.status, 0):
            out[key] = row
    return out


def parse_baseline_before(raw: str, now: datetime) -> date:
    """`--baseline-before today` is the Australia/Sydney calendar date of *now*."""
    text = str(raw).strip()
    if not text:
        raise ValueError("baseline-before is empty")
    if text.lower() == "today":
        return sydney_calendar_date(now)
    return date.fromisoformat(text)


def resolve_baseline_path(
    root: Path,
    override: Path | str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> Path:
    if override:
        return Path(override)
    env = environ if environ is not None else os.environ
    raw = str(env.get(BASELINE_ENV) or "").strip()
    if raw:
        return Path(raw)
    return Path(root) / BASELINE_REL


def load_known_missed_baseline(path: Path) -> dict[tuple[str, datetime], dict[str, Any]]:
    """History is labeled, never deleted. Missing file → empty."""
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    out: dict[tuple[str, datetime], dict[str, Any]] = {}
    for raw in data.get("windows") or []:
        if not isinstance(raw, dict) or not raw.get("routine_id") or not raw.get("scheduled_anchor_ts"):
            continue
        routine_id = str(raw["routine_id"])
        anchor = as_utc(parse_utc(str(raw["scheduled_anchor_ts"])))
        out[(routine_id, anchor)] = {
            "routine_id": routine_id,
            "scheduled_anchor_ts": as_utc(anchor).isoformat(),
            "window_closed_at": raw.get("window_closed_at"),
            "incident": raw.get("incident"),
            "reason": raw.get("reason") or "closed_window_no_completion",
            "label": raw.get("label") or KNOWN_MISSED_LABEL,
        }
    return out


def write_known_missed_baseline(
    path: Path,
    *,
    now: datetime,
    cutoff: date,
    windows: Iterable[Miss],
    existing: Mapping[tuple[str, datetime], Mapping[str, Any]] | None = None,
) -> Path:
    """Union write. Does not delete prior labeled windows."""
    merged: dict[tuple[str, datetime], dict[str, Any]] = dict(existing or {})
    for miss in windows:
        key = (miss.routine_id, as_utc(miss.scheduled_anchor_ts))
        merged[key] = {
            "routine_id": miss.routine_id,
            "scheduled_anchor_ts": as_utc(miss.scheduled_anchor_ts).isoformat(),
            "window_closed_at": as_utc(miss.window_closed_at).isoformat(),
            "incident": miss.incident,
            "reason": miss.reason,
            "label": KNOWN_MISSED_LABEL,
        }
    rows = [merged[key] for key in sorted(merged, key=lambda item: (item[0], item[1].isoformat()))]
    payload = {
        "schema": "mm.scheduler.known_missed_baseline.v1",
        "as_of_knowledge": as_utc(now).isoformat(),
        "timezone": str(OPS_TZ),
        "sydney_date_cutoff": cutoff.isoformat(),
        "label": KNOWN_MISSED_LABEL,
        "n_windows": len(rows),
        "notes": (
            "Pre-cutoff closed windows labeled known-missed so Monday's miss-check "
            "is visible. History is labeled, not deleted. SCHED-001 stays OPEN."
        ),
        "windows": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def miss_sweep(
    catalog: Catalog,
    completions: Iterable[Completion],
    now: datetime,
    *,
    lookback_days: int | None = None,
    known_missed: Mapping[tuple[str, datetime], Any] | Iterable[tuple[str, datetime]] | None = None,
    baseline_before: date | None = None,
    baseline_path: str | Path | None = None,
) -> SweepResult:
    """MERGE-BLOCKING control. Closed window + no completion → miss.

    Does not auto-close SCHED-001. Does not treat 'no window yet' as a close.
    created_at is not used to suppress a closed window (Hive timestamps unverified).
    A refused stamp (wrong weekday) writes no row — silence to the sweep.
    known-missed / baselined windows are labeled, not deleted, and do not escalate.
    """
    now_u = as_utc(now)
    lookback = int(lookback_days if lookback_days is not None else catalog.lookback_days)
    completion_rows = tuple(completions)
    indexed = _index_completions(completion_rows)
    known_keys: set[tuple[str, datetime]] = set()
    if isinstance(known_missed, Mapping):
        known_keys = {(rid, as_utc(ts)) for rid, ts in known_missed.keys()}
    elif known_missed is not None:
        known_keys = {(rid, as_utc(ts)) for rid, ts in known_missed}
    misses: list[Miss] = []
    labeled: list[Miss] = []
    pending: list[dict[str, Any]] = []
    ok: list[dict[str, Any]] = []
    early: list[dict[str, Any]] = []
    late: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    wrong: list[dict[str, Any]] = []
    checked: list[str] = []
    for routine in catalog.enabled():
        checked.append(routine.routine_id)
        closed = closed_anchors(routine, now_u, lookback_days=lookback)
        next_open = [ts for ts in anchors_between(routine, now_u, now_u + timedelta(days=lookback)) if not window_closed(ts, now_u, routine.miss_after_seconds)]
        if next_open and now_u < next_open[0] + timedelta(seconds=routine.miss_after_seconds) and now_u >= next_open[0]:
            pending.append(
                {
                    "routine_id": routine.routine_id,
                    "scheduled_anchor_ts": as_utc(next_open[0]).isoformat(),
                    "status": "pending",
                    "reason": "window_open",
                }
            )
        elif not closed and next_open:
            pending.append(
                {
                    "routine_id": routine.routine_id,
                    "scheduled_anchor_ts": as_utc(next_open[0]).isoformat(),
                    "status": "pending",
                    "reason": "no_closed_window_in_lookback",
                }
            )
        for anchor in closed:
            hit = indexed.get((routine.routine_id, as_utc(anchor)))
            if hit is not None and hit.status in FIRE_STATUSES:
                payload = {
                    "routine_id": routine.routine_id,
                    "scheduled_anchor_ts": as_utc(anchor).isoformat(),
                    "status": hit.status,
                    "delta_seconds": hit.delta_seconds,
                    "run_id": hit.run_id,
                }
                if hit.status == "ok":
                    ok.append(payload)
                elif hit.status == "early":
                    early.append(payload)
                elif hit.status == "late":
                    late.append(payload)
                elif hit.status == "skipped":
                    skipped.append(payload)
                continue
            closed_at = as_utc(anchor) + timedelta(seconds=routine.miss_after_seconds)
            key = (routine.routine_id, as_utc(anchor))
            sydney_day = sydney_calendar_date(anchor)
            is_known = key in known_keys or (baseline_before is not None and sydney_day < baseline_before)
            row = Miss(
                routine_id=routine.routine_id,
                family=routine.family,
                scheduled_anchor_ts=anchor,
                window_closed_at=closed_at,
                incident=routine.incident,
                reason="closed_window_no_completion",
                label=KNOWN_MISSED_LABEL if is_known else None,
            )
            if is_known:
                labeled.append(row)
            else:
                misses.append(row)
    seen_wrong: set[tuple[str, datetime]] = set()
    for hit in completion_rows:
        if hit.status != "wrong_anchor":
            continue
        key = (hit.routine_id, as_utc(hit.scheduled_anchor_ts))
        if key in seen_wrong:
            continue
        seen_wrong.add(key)
        wrong.append(
            {
                "routine_id": hit.routine_id,
                "scheduled_anchor_ts": as_utc(hit.scheduled_anchor_ts).isoformat(),
                "fired_at_ts": None if hit.fired_at_ts is None else as_utc(hit.fired_at_ts).isoformat(),
                "delta_seconds": hit.delta_seconds,
                "status": hit.status,
                "reason": hit.reason or WRONG_ANCHOR_REASON,
                "run_id": hit.run_id,
            }
        )
    return SweepResult(
        now=now_u,
        as_of_knowledge=now_u,
        misses=tuple(misses),
        pending=tuple(pending),
        ok=tuple(ok),
        late=tuple(late),
        skipped=tuple(skipped),
        routines_checked=tuple(checked),
        known_missed=tuple(labeled),
        wrong_anchor=tuple(wrong),
        baseline_path=None if baseline_path is None else str(baseline_path),
        baseline_before=None if baseline_before is None else baseline_before.isoformat(),
        early=tuple(early),
    )


def render_incident_markdown(result: SweepResult) -> str:
    lines = [
        "# Scheduler miss sweep — OPEN ops artifact",
        "",
        f"as_of_knowledge: {as_utc(result.as_of_knowledge).isoformat()}",
        f"control: {result.control}",
        "heartbeat_on_fire: secondary log; this artifact is the check",
        f"escalated: {str(result.escalated).lower()}",
        f"n_missed: {len(result.misses)}",
        f"n_known_missed: {len(result.known_missed)}",
        f"n_wrong_anchor: {len(result.wrong_anchor)}",
        "",
        "SCHED-001 stays OPEN until a verified on-anchor fire. This file does not close it.",
        "Do not interpret pending/'no window yet' as a close.",
        "known-missed windows are labeled (not deleted) and do not occupy n_missed.",
        "",
        "| routine_id | family | scheduled_anchor_ts | window_closed_at | incident | reason |",
        "|---|---|---|---|---|---|",
    ]
    for miss in result.misses:
        inc = miss.incident or "—"
        lines.append(
            f"| `{miss.routine_id}` | {miss.family} | {as_utc(miss.scheduled_anchor_ts).isoformat()} | "
            f"{as_utc(miss.window_closed_at).isoformat()} | {inc} | {miss.reason} |"
        )
    if not result.misses:
        lines.append("| — | — | — | — | — | none |")
    if result.known_missed:
        lines.extend(
            [
                "",
                "## known-missed (baselined; not escalated)",
                "",
                "| routine_id | family | scheduled_anchor_ts | window_closed_at | label |",
                "|---|---|---|---|---|",
            ]
        )
        for miss in result.known_missed:
            lines.append(
                f"| `{miss.routine_id}` | {miss.family} | {as_utc(miss.scheduled_anchor_ts).isoformat()} | "
                f"{as_utc(miss.window_closed_at).isoformat()} | {miss.label or KNOWN_MISSED_LABEL} |"
            )
    if result.wrong_anchor:
        lines.extend(
            [
                "",
                "## wrong_anchor (not classified as late)",
                "",
                "| routine_id | scheduled_anchor_ts | fired_at_ts | delta_seconds | reason |",
                "|---|---|---|---|---|",
            ]
        )
        for row in result.wrong_anchor:
            lines.append(
                f"| `{row['routine_id']}` | {row['scheduled_anchor_ts']} | "
                f"{row.get('fired_at_ts') or '—'} | {row.get('delta_seconds')} | {row.get('reason')} |"
            )
    lines.append("")
    return "\n".join(lines) + "\n"


def write_incident_artifact(result: SweepResult, *, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    day = as_utc(result.as_of_knowledge).date().isoformat()
    path = out_dir / f"{day}-miss.md"
    path.write_text(render_incident_markdown(result), encoding="utf-8")
    return path


def render_backfill_markdown(
    catalog: Catalog,
    completions: Iterable[Completion],
    *,
    as_of: datetime,
    lookback_days: int | None = None,
) -> str:
    now = as_utc(as_of)
    lookback = int(lookback_days if lookback_days is not None else catalog.lookback_days)
    indexed = _index_completions(completions)
    lines = [
        f"# Scheduler backfill — {now.date().isoformat()}",
        "",
        f"as_of_knowledge: {now.isoformat()}",
        f"lookback_days: {lookback}",
        "control: miss_sweep (heartbeat-on-fire is a log)",
        "created_at / updated_at / ROUTINE_CHANGE: **not in repo** (unverified; pending Hive timestamps).",
        "",
        "| routine_id | family | scheduled_anchor_ts | fired_at_ts | delta_seconds | status |",
        "|---|---|---|---|---|---|",
    ]
    for routine in catalog.routines:
        closed = closed_anchors(routine, now, lookback_days=lookback)
        if not closed:
            lines.append(f"| `{routine.routine_id}` | {routine.family} | — | — | — | no_closed_window |")
            continue
        for anchor in closed:
            hit = indexed.get((routine.routine_id, as_utc(anchor)))
            if hit is None:
                lines.append(
                    f"| `{routine.routine_id}` | {routine.family} | {as_utc(anchor).isoformat()} | — | — | missed |"
                )
                continue
            fired = "—" if hit.fired_at_ts is None else as_utc(hit.fired_at_ts).isoformat()
            delta = "—" if hit.delta_seconds is None else str(hit.delta_seconds)
            lines.append(
                f"| `{routine.routine_id}` | {routine.family} | {as_utc(anchor).isoformat()} | {fired} | {delta} | {hit.status} |"
            )
    lines.append("")
    return "\n".join(lines) + "\n"


def stamp_fire(
    routine: Routine,
    *,
    fired_at: datetime,
    run_id: str,
    as_of_knowledge: datetime | None = None,
    source: str = "lab",
    exit_status: int | None = None,
    payload_path: str | None = None,
    cli: str | None = None,
) -> Completion:
    """Secondary log. Not the scheduler check. A failed CLI run is still a fire.

    Anchor is catalog ``local_time`` on the fire's local calendar date in the
    routine timezone (Australia/Sydney for Hive clocks). If that weekday is not
    in the catalog, raise ``WrongAnchorError`` and write **no** completion row —
    never mere ``late`` from walking back to the previous scheduled day.
    """
    fired = as_utc(fired_at)
    anchor, weekday_ok, weekday = scheduled_slot(routine, fired)
    if not weekday_ok:
        raise WrongAnchorError(
            {
                "error": "wrong_anchor",
                "reason": WRONG_ANCHOR_REASON,
                "wrote": False,
                "routine_id": routine.routine_id,
                "fired_at_ts": fired.isoformat(),
                "local_weekday": weekday,
                "scheduled_weekdays": list(routine.weekdays),
                "would_be_anchor_ts": as_utc(anchor).isoformat(),
                "note": "no completion row; stamp refused. Silence (no CLI) and failed-CLI fires stay distinct from a successful fire with a bad stamp.",
            }
        )
    delta = delta_seconds(anchor, fired)
    status = classify_delta(delta, routine.late_after_seconds)
    as_of = as_utc(as_of_knowledge or fired)
    return Completion(
        routine_id=routine.routine_id,
        run_id=run_id,
        scheduled_anchor_ts=anchor,
        fired_at_ts=fired,
        delta_seconds=delta,
        status=status,
        as_of_knowledge=as_of,
        source=source,
        exit_status=exit_status,
        payload_path=payload_path,
        cli=cli,
        reason=None,
    )
