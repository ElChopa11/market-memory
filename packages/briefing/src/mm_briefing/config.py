"""Load Market Pulse YAML. Never read secrets from files — only env names."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from pathlib import Path
from typing import Any

import yaml

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "packages").is_dir():
            return candidate
    return here


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def parse_hhmm(value: str) -> time:
    parts = str(value).strip().split(":")
    if len(parts) < 2:
        raise ValueError(f"invalid local_time {value!r}; expected HH:MM")
    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2]) if len(parts) > 2 else 0
    return time(hour, minute, second)


@dataclass(frozen=True)
class JobSpec:
    kind: str
    enabled: bool
    local_time: time
    weekdays: tuple[str, ...]


@dataclass(frozen=True)
class AlertTypeThresholds:
    alert_type: str
    enabled: bool
    params: dict[str, float | int | str]


@dataclass(frozen=True)
class AlertSettings:
    enabled: bool
    require_threshold_config: bool
    interval_minutes: int
    types: tuple[AlertTypeThresholds, ...]

    def has_thresholds(self) -> bool:
        if not self.types:
            return False
        for row in self.types:
            if not row.enabled:
                continue
            numeric = [v for v in row.params.values() if isinstance(v, (int, float)) and not isinstance(v, bool)]
            if numeric:
                return True
        return False

    def type_map(self) -> dict[str, AlertTypeThresholds]:
        return {row.alert_type: row for row in self.types}


@dataclass(frozen=True)
class WatchlistSpec:
    instrument: str
    why_now: str
    invalidation: str
    no_trade: str
    levels: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class PulseSchedule:
    lab_timezone: str
    session_timezone: str
    jobs: tuple[JobSpec, ...]
    alerts_enabled: bool
    alert_interval_minutes: int


@dataclass(frozen=True)
class BriefingSettings:
    root: Path
    schedule: PulseSchedule
    alerts: AlertSettings
    macro: dict[str, Any]
    calendar_events: tuple[dict[str, Any], ...]
    watchlist: tuple[WatchlistSpec, ...]
    divergence_rules: dict[str, Any]
    briefs_dir: Path = field(default_factory=lambda: Path("briefs"))


def load_schedule(path: Path | None = None) -> PulseSchedule:
    settings_path = path or (repo_root() / "config" / "schedules" / "market-pulse.yaml")
    data = load_yaml(settings_path)
    briefs = data.get("briefs") or {}
    alerts = data.get("alerts") or {}
    jobs: list[JobSpec] = []
    for kind, key in (("preopen", "pre_open"), ("close", "close")):
        spec = briefs.get(key) or {}
        weekdays = tuple(spec.get("weekdays") or ["Mon", "Tue", "Wed", "Thu", "Fri"])
        jobs.append(
            JobSpec(
                kind=kind,
                enabled=bool(spec.get("enabled", False)),
                local_time=parse_hhmm(str(spec.get("local_time") or ("08:00" if kind == "preopen" else "16:15"))),
                weekdays=weekdays,
            )
        )
    return PulseSchedule(
        lab_timezone=str(data.get("lab_timezone") or "Australia/Sydney"),
        session_timezone=str(data.get("session_timezone") or "America/New_York"),
        jobs=tuple(jobs),
        alerts_enabled=bool(alerts.get("enabled", False)),
        alert_interval_minutes=int(alerts.get("interval_minutes") or 15),
    )


def load_alert_settings(path: Path | None = None) -> AlertSettings:
    settings_path = path or (repo_root() / "config" / "briefing" / "alerts.yaml")
    data = load_yaml(settings_path)
    types: list[AlertTypeThresholds] = []
    raw_types = data.get("types") or {}
    if isinstance(raw_types, dict):
        for name, spec in raw_types.items():
            if not isinstance(spec, dict):
                continue
            params: dict[str, float | int | str] = {}
            for key, value in spec.items():
                if key == "enabled":
                    continue
                if isinstance(value, bool):
                    continue
                if isinstance(value, (int, float, str)):
                    params[str(key)] = value
            types.append(
                AlertTypeThresholds(
                    alert_type=str(name),
                    enabled=bool(spec.get("enabled", True)),
                    params=params,
                )
            )
    require = data.get("require_threshold_config")
    if require is None:
        require = True
    return AlertSettings(
        enabled=bool(data.get("enabled", True)),
        require_threshold_config=bool(require),
        interval_minutes=int(data.get("interval_minutes") or 15),
        types=tuple(types),
    )


def load_watchlist(path: Path | None = None) -> tuple[WatchlistSpec, ...]:
    settings_path = path or (repo_root() / "config" / "briefing" / "watchlist.yaml")
    data = load_yaml(settings_path)
    items: list[WatchlistSpec] = []
    for row in data.get("items") or []:
        if not isinstance(row, dict):
            continue
        levels = row.get("levels") or {}
        level_pairs = tuple(sorted((str(k), str(v)) for k, v in levels.items())) if isinstance(levels, dict) else ()
        items.append(
            WatchlistSpec(
                instrument=str(row.get("instrument") or "").upper(),
                why_now=str(row.get("why_now") or ""),
                invalidation=str(row.get("invalidation") or ""),
                no_trade=str(row.get("no_trade") or ""),
                levels=level_pairs,
            )
        )
    return tuple(items)


def load_briefing_settings(root: Path | None = None) -> BriefingSettings:
    base = root or repo_root()
    calendar = load_yaml(base / "config" / "briefing" / "calendar.yaml")
    events = tuple(row for row in (calendar.get("events") or []) if isinstance(row, dict))
    return BriefingSettings(
        root=base,
        schedule=load_schedule(base / "config" / "schedules" / "market-pulse.yaml"),
        alerts=load_alert_settings(base / "config" / "briefing" / "alerts.yaml"),
        macro=load_yaml(base / "config" / "briefing" / "macro.yaml"),
        calendar_events=events,
        watchlist=load_watchlist(base / "config" / "briefing" / "watchlist.yaml"),
        divergence_rules=load_yaml(base / "config" / "briefing" / "divergences.yaml"),
        briefs_dir=base / "briefs",
    )
