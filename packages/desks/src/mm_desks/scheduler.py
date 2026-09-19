"""Scheduler miss sweep (IMP-042). This is the control, not a log.

For each configured routine: if the window is closed and no completion
row exists → missed. Heartbeat-on-fire is secondary.

Ops-owned. Must not depend on the execution package, sign, or talk to Telegram live.
Canaries are out of scope and are never loaded from this catalog.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

import yaml

from mm_common.time import as_utc, parse_utc

UTC = timezone.utc
WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
STATUSES = ("ok", "late", "missed", "skipped")
FAMILIES = ("lab", "grok_bot")
CANARY_MARKERS = ("canary",)
DEFAULT_LATE_AFTER = 300
DEFAULT_MISS_AFTER = 900
DEFAULT_LOOKBACK_DAYS = 14
ROUTINES_REL = Path("config") / "schedules" / "routines.yaml"
PULSE_REL = Path("config") / "schedules" / "market-pulse.yaml"
TELEGRAM_REL = Path("config") / "delivery" / "telegram.yaml"


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

    def canonical(self) -> dict[str, Any]:
        return {
            "routine_id": self.routine_id,
            "run_id": self.run_id,
            "scheduled_anchor_ts": as_utc(self.scheduled_anchor_ts).isoformat(),
            "fired_at_ts": None if self.fired_at_ts is None else as_utc(self.fired_at_ts).isoformat(),
            "delta_seconds": self.delta_seconds,
            "status": self.status,
            "as_of_knowledge": as_utc(self.as_of_knowledge).isoformat(),
            "source": self.source,
        }


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

    def canonical(self) -> dict[str, Any]:
        return {
            "routine_id": self.routine_id,
            "family": self.family,
            "scheduled_anchor_ts": as_utc(self.scheduled_anchor_ts).isoformat(),
            "window_closed_at": as_utc(self.window_closed_at).isoformat(),
            "incident": self.incident,
            "reason": self.reason,
            "status": "missed",
        }


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
            "n_ok": len(self.ok),
            "n_late": len(self.late),
            "n_pending": len(self.pending),
            "n_skipped": len(self.skipped),
            "routines_checked": list(self.routines_checked),
            "misses": [row.canonical() for row in self.misses],
            "ok": list(self.ok),
            "late": list(self.late),
            "pending": list(self.pending),
            "skipped": list(self.skipped),
            "artifact_path": self.artifact_path,
            "heartbeat_is_not_the_check": True,
        }


def delta_seconds(anchor: datetime, fired: datetime) -> int:
    """Signed seconds: fired - anchor. Negative = early vs anchor."""
    return int((as_utc(fired) - as_utc(anchor)).total_seconds())


def classify_delta(delta: int, late_after_seconds: int) -> str:
    """ok if |delta| within grace; late if a fire exists but off-anchor."""
    if abs(int(delta)) <= int(late_after_seconds):
        return "ok"
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
    anchor = parse_utc(str(row["scheduled_anchor_ts"]))
    fired_raw = row.get("fired_at_ts")
    fired = None if fired_raw in (None, "") else parse_utc(str(fired_raw))
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
    as_of = parse_utc(str(row.get("as_of_knowledge") or row.get("fired_at_ts") or row["scheduled_anchor_ts"]))
    return Completion(
        routine_id=routine_id,
        run_id=str(row.get("run_id") or f"{routine_id}-{as_utc(anchor).strftime('%Y%m%dT%H%M%SZ')}"),
        scheduled_anchor_ts=anchor,
        fired_at_ts=fired,
        delta_seconds=None if delta is None else int(delta),
        status=status,
        as_of_knowledge=as_of,
        source=str(row.get("source") or "fixture"),
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
    rank = {"ok": 3, "late": 2, "skipped": 1, "missed": 0}
    out: dict[tuple[str, datetime], Completion] = {}
    for row in rows:
        key = (row.routine_id, as_utc(row.scheduled_anchor_ts))
        prev = out.get(key)
        if prev is None or rank.get(row.status, 0) >= rank.get(prev.status, 0):
            out[key] = row
    return out


def miss_sweep(
    catalog: Catalog,
    completions: Iterable[Completion],
    now: datetime,
    *,
    lookback_days: int | None = None,
) -> SweepResult:
    """MERGE-BLOCKING control. Closed window + no completion → miss.

    Does not auto-close SCHED-001. Does not treat 'no window yet' as a close.
    created_at is not used to suppress a closed window (Hive timestamps unverified).
    """
    now_u = as_utc(now)
    lookback = int(lookback_days if lookback_days is not None else catalog.lookback_days)
    indexed = _index_completions(completions)
    misses: list[Miss] = []
    pending: list[dict[str, Any]] = []
    ok: list[dict[str, Any]] = []
    late: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
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
            if hit is None or hit.status == "missed":
                closed_at = as_utc(anchor) + timedelta(seconds=routine.miss_after_seconds)
                misses.append(
                    Miss(
                        routine_id=routine.routine_id,
                        family=routine.family,
                        scheduled_anchor_ts=anchor,
                        window_closed_at=closed_at,
                        incident=routine.incident,
                        reason="closed_window_no_completion",
                    )
                )
                continue
            payload = {
                "routine_id": routine.routine_id,
                "scheduled_anchor_ts": as_utc(anchor).isoformat(),
                "status": hit.status,
                "delta_seconds": hit.delta_seconds,
                "run_id": hit.run_id,
            }
            if hit.status == "ok":
                ok.append(payload)
            elif hit.status == "late":
                late.append(payload)
            elif hit.status == "skipped":
                skipped.append(payload)
    return SweepResult(
        now=now_u,
        as_of_knowledge=now_u,
        misses=tuple(misses),
        pending=tuple(pending),
        ok=tuple(ok),
        late=tuple(late),
        skipped=tuple(skipped),
        routines_checked=tuple(checked),
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
        "",
        "SCHED-001 stays OPEN until a verified on-anchor fire. This file does not close it.",
        "Do not interpret pending/'no window yet' as a close.",
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
) -> Completion:
    """Secondary log. Not the scheduler check."""
    fired = as_utc(fired_at)
    day = fired.astimezone(routine.tz()).date()
    weekday = WEEKDAY_NAMES[day.weekday()]
    if weekday in routine.weekdays:
        anchor = local_anchor(routine, day)
    else:
        # Fall back to most recent weekday anchor at or before fired.
        cursor = day
        while WEEKDAY_NAMES[cursor.weekday()] not in routine.weekdays:
            cursor = cursor - timedelta(days=1)
        anchor = local_anchor(routine, cursor)
    delta, status = classify_fire(anchor, fired, routine.late_after_seconds)
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
    )
