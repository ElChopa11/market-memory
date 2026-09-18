"""Load delivery YAML. Chat ids and bot token come from env names only — never from git."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

from mm_common.http import DEFAULT_BACKOFF_S, DEFAULT_MAX_ATTEMPTS, DEFAULT_TIMEOUT
from mm_common.naming import OPS

BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ID_ENV = "TELEGRAM_CHAT_ID"
CHAT_ID_DESK_PREFIX = "TELEGRAM_CHAT_ID_"


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
        raise ValueError(f"invalid HH:MM {value!r}")
    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2]) if len(parts) > 2 else 0
    return time(hour, minute, second)


def _int(value: Any, default: int) -> int:
    if value is None:
        return default
    return int(value)


def _float(value: Any, default: float) -> float:
    if value is None:
        return default
    return float(value)


def _bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    return bool(value)


@dataclass(frozen=True)
class DeskRoute:
    slug: str
    enabled: bool
    chat_id_env: str
    thread_id: int | None


@dataclass(frozen=True)
class DeliveryProduct:
    """Ops-owned delivery of an existing desk artifact. Does not invent content."""

    slug: str
    desk: str
    kind: str
    sleeve: str | None
    enabled: bool
    inherit_content_hash: bool


@dataclass(frozen=True)
class QuietHours:
    enabled: bool
    timezone: ZoneInfo
    start: time
    end: time


@dataclass(frozen=True)
class ThresholdSpec:
    name: str
    enabled: bool
    params: dict[str, float | int]


@dataclass(frozen=True)
class ThresholdSettings:
    require_threshold_config: bool
    specs: tuple[ThresholdSpec, ...]

    def spec(self, name: str) -> ThresholdSpec | None:
        for row in self.specs:
            if row.name == name:
                return row
        return None

    def has_numeric(self, name: str | None = None) -> bool:
        rows = self.specs if name is None else tuple(s for s in self.specs if s.name == name)
        for row in rows:
            if not row.enabled:
                continue
            if any(isinstance(v, (int, float)) and not isinstance(v, bool) for v in row.params.values()):
                return True
        return False


@dataclass(frozen=True)
class ScheduleJob:
    name: str
    enabled: bool
    local_time: time
    weekdays: tuple[str, ...]
    timezone: ZoneInfo


@dataclass(frozen=True)
class RateLimitSettings:
    max_requests_per_minute: int
    timeout_seconds: float
    max_attempts: int
    backoff_s: float


@dataclass(frozen=True)
class InboundSettings:
    enabled: bool
    allowlist: tuple[str, ...]


@dataclass(frozen=True)
class TelegramSettings:
    channel: str
    parse_mode: str
    max_message_chars: int
    disable_web_page_preview: bool
    api_base_url: str
    rate_limit: RateLimitSettings
    quiet_hours: QuietHours
    dedupe_ttl_seconds: int
    thresholds: ThresholdSettings
    desks: dict[str, DeskRoute]
    schedule: tuple[ScheduleJob, ...]
    inbound: InboundSettings
    products: dict[str, DeliveryProduct]
    owner: str = OPS
    publisher: str = OPS
    coordinator: str = "orchestration_only"
    bot_token_env: str = BOT_TOKEN_ENV
    default_chat_id_env: str = CHAT_ID_ENV

    def route(self, slug: str) -> DeskRoute | None:
        return self.desks.get(slug)

    def product(self, slug: str) -> DeliveryProduct | None:
        return self.products.get(slug)


def default_config_path(root: Path | None = None) -> Path:
    return repo_root(root) / "config" / "delivery" / "telegram.yaml"


def load_telegram_settings(root: Path | None = None, *, path: Path | None = None) -> TelegramSettings:
    cfg_path = path or default_config_path(root)
    data = load_yaml(cfg_path)
    parse_mode = str(data.get("parse_mode") or "MarkdownV2")
    max_chars = _int(data.get("max_message_chars"), 4096)
    api = data.get("api") if isinstance(data.get("api"), dict) else {}
    rl_block = data.get("rate_limit") if isinstance(data.get("rate_limit"), dict) else {}
    rate_limit = RateLimitSettings(
        max_requests_per_minute=_int(rl_block.get("max_requests_per_minute"), 20),
        timeout_seconds=_float(api.get("timeout_seconds"), DEFAULT_TIMEOUT),
        max_attempts=_int(api.get("max_attempts"), DEFAULT_MAX_ATTEMPTS),
        backoff_s=_float(api.get("backoff_s"), DEFAULT_BACKOFF_S),
    )
    qh = data.get("quiet_hours") if isinstance(data.get("quiet_hours"), dict) else {}
    tz_name = str(qh.get("timezone") or "Australia/Sydney")
    quiet = QuietHours(
        enabled=_bool(qh.get("enabled"), True),
        timezone=ZoneInfo(tz_name),
        start=parse_hhmm(str(qh.get("start") or "22:00")),
        end=parse_hhmm(str(qh.get("end") or "07:00")),
    )
    dedupe = data.get("dedupe") if isinstance(data.get("dedupe"), dict) else {}
    raw_th = data.get("thresholds") if isinstance(data.get("thresholds"), dict) else {}
    specs: list[ThresholdSpec] = []
    for name, spec in raw_th.items():
        if name == "require_threshold_config" or not isinstance(spec, dict):
            continue
        params: dict[str, float | int] = {}
        for key, value in spec.items():
            if key == "enabled":
                continue
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                params[key] = value
        specs.append(
            ThresholdSpec(name=str(name), enabled=_bool(spec.get("enabled"), True), params=params)
        )
    thresholds = ThresholdSettings(
        require_threshold_config=_bool(raw_th.get("require_threshold_config"), True),
        specs=tuple(specs),
    )
    desks: dict[str, DeskRoute] = {}
    raw_desks = data.get("desks") if isinstance(data.get("desks"), dict) else {}
    for slug, spec in raw_desks.items():
        if not isinstance(spec, dict):
            continue
        thread_raw = spec.get("thread_id")
        thread_id = int(thread_raw) if thread_raw is not None and str(thread_raw).strip() != "" else None
        env_name = str(spec.get("chat_id_env") or f"{CHAT_ID_DESK_PREFIX}{str(slug).upper()}")
        desks[str(slug)] = DeskRoute(
            slug=str(slug),
            enabled=_bool(spec.get("enabled"), True),
            chat_id_env=env_name,
            thread_id=thread_id,
        )
    if "ops" not in desks:
        desks["ops"] = DeskRoute(
            slug="ops",
            enabled=True,
            chat_id_env=CHAT_ID_ENV,
            thread_id=None,
        )
    sched_block = data.get("schedule") if isinstance(data.get("schedule"), dict) else {}
    sched_tz = ZoneInfo(str(sched_block.get("timezone") or tz_name))
    jobs: list[ScheduleJob] = []
    for name, spec in sched_block.items():
        if name == "timezone" or not isinstance(spec, dict):
            continue
        weekdays = spec.get("weekdays") or ["Mon", "Tue", "Wed", "Thu", "Fri"]
        jobs.append(
            ScheduleJob(
                name=str(name),
                enabled=_bool(spec.get("enabled"), True),
                local_time=parse_hhmm(str(spec.get("local_time") or "07:30")),
                weekdays=tuple(str(d) for d in weekdays),
                timezone=sched_tz,
            )
        )
    inbound_block = data.get("inbound") if isinstance(data.get("inbound"), dict) else {}
    allow = inbound_block.get("allowlist") or ["/status", "/brief", "/desk", "/idea", "/gaps", "/halt"]
    inbound = InboundSettings(
        enabled=_bool(inbound_block.get("enabled"), False),
        allowlist=tuple(str(x) for x in allow),
    )
    products: dict[str, DeliveryProduct] = {}
    raw_products = data.get("products") if isinstance(data.get("products"), dict) else {}
    for slug, spec in raw_products.items():
        if not isinstance(spec, dict):
            continue
        sleeve_raw = spec.get("sleeve")
        products[str(slug)] = DeliveryProduct(
            slug=str(slug),
            desk=str(spec.get("desk") or ""),
            kind=str(spec.get("kind") or slug),
            sleeve=None if sleeve_raw in (None, "") else str(sleeve_raw),
            enabled=_bool(spec.get("enabled"), True),
            inherit_content_hash=_bool(spec.get("inherit_content_hash"), True),
        )
    settings = TelegramSettings(
        channel=str(data.get("channel") or "telegram"),
        parse_mode=parse_mode,
        max_message_chars=max_chars,
        disable_web_page_preview=_bool(data.get("disable_web_page_preview"), True),
        api_base_url=str(api.get("base_url") or "https://api.telegram.org").rstrip("/"),
        rate_limit=rate_limit,
        quiet_hours=quiet,
        dedupe_ttl_seconds=_int(dedupe.get("ttl_seconds"), 86400),
        thresholds=thresholds,
        desks=desks,
        schedule=tuple(jobs),
        inbound=inbound,
        products=products,
        owner=str(data.get("owner") or OPS),
        publisher=str(data.get("publisher") or OPS),
        coordinator=str(data.get("coordinator") or "orchestration_only"),
    )
    from mm_delivery.matrix import assert_channel_matrix

    assert_channel_matrix(settings)
    return settings


def bot_token_from_env(environ: dict[str, str] | None = None) -> str | None:
    env = environ if environ is not None else os.environ
    value = (env.get(BOT_TOKEN_ENV) or "").strip()
    return value or None


def resolve_chat_id_env(slug: str, settings: TelegramSettings, environ: dict[str, str] | None = None) -> str:
    """Return the env *name* used for this desk (for dry-run payloads)."""
    env = environ if environ is not None else os.environ
    upper = slug.upper().replace("-", "_")
    desk_override = f"{CHAT_ID_DESK_PREFIX}{upper}"
    if (env.get(desk_override) or "").strip():
        return desk_override
    route = settings.route(slug)
    configured = route.chat_id_env if route else CHAT_ID_ENV
    if configured != CHAT_ID_ENV and (env.get(configured) or "").strip():
        return configured
    if (env.get(CHAT_ID_ENV) or "").strip():
        return CHAT_ID_ENV
    if configured:
        return configured
    return CHAT_ID_ENV


def chat_id_from_env(slug: str, settings: TelegramSettings, environ: dict[str, str] | None = None) -> str | None:
    env = environ if environ is not None else os.environ
    name = resolve_chat_id_env(slug, settings, env)
    value = (env.get(name) or "").strip()
    if value:
        return value
    fallback = (env.get(CHAT_ID_ENV) or "").strip()
    return fallback or None
