"""Delivery-only env-file load and env preflight (Hybrid Step 2).

CLI process only. Prefer ``/home/box/agent-data/delivery/telegram.env`` (or
``MM_DELIVERY_ENV_FILE``) when that file exists; otherwise keep process env
(CI). Never print secret values. Never copy ``TELEGRAM_CHAT_ID_PRINCIPAL_DM``
onto ``TELEGRAM_CHAT_ID``.

Must not hold secrets in git, place orders, or talk to Hyperliquid.
"""

from __future__ import annotations

import os
import re
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

from mm_common.naming import OPS, ROUTE_SLUGS

DEFAULT_DELIVERY_ENV_FILE = Path("/home/box/agent-data/delivery/telegram.env")
DELIVERY_ENV_FILE_VAR = "MM_DELIVERY_ENV_FILE"

BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ID_ENV = "TELEGRAM_CHAT_ID"
PRINCIPAL_DM_CHAT_ID_ENV = "TELEGRAM_CHAT_ID_PRINCIPAL_DM"
FRED_API_KEY_ENV = "FRED_API_KEY"
POLYGON_API_KEY_ENV = "POLYGON_API_KEY"
POSTGRES_DSN_ENV = "POSTGRES_DSN"
MINIO_ENDPOINT_ENV = "MINIO_ENDPOINT"
MINIO_ACCESS_KEY_ENV = "MINIO_ACCESS_KEY"
MINIO_SECRET_KEY_ENV = "MINIO_SECRET_KEY"
MINIO_BUCKET_ENV = "MINIO_BUCKET"
OBJECT_STORE_BACKEND_ENV = "MM_OBJECT_STORE"
OBJECT_STORE_PATH_ENV = "MM_OBJECT_STORE_PATH"

OBJECT_STORE_ITEM = "object_store"
DOWN_SERVICE = "DOWN SERVICE"

STATE_FOUND = "FOUND"
STATE_MISSING = "MISSING"
STATE_ABSENT = "ABSENT"
STATE_DOWN = DOWN_SERVICE
STATE_NOT_CONFIGURED = "NOT CONFIGURED"
STATE_SKIPPED = "SKIPPED"

GET_CHAT_ITEM = "telegram_group_getChat"

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_OPTIONAL = "optional"
SEVERITY_OK = "ok"

PURPOSE_CHECKLIST = "checklist"
PURPOSE_DELIVER = "deliver"
PURPOSE_BRIEF = "brief"

OBJECT_STORE_PROBE_TIMEOUT_S = 0.4

_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ASSIGN_RE = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")

_SECRET_SUBSTRINGS = (
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "API_KEY",
    "DSN",
    "ACCESS_KEY",
)


def desk_chat_id_env_names() -> tuple[str, ...]:
    """``TELEGRAM_CHAT_ID_<DESK>`` for routes other than ops (ops uses the group id)."""
    names: list[str] = []
    for slug in ROUTE_SLUGS:
        if slug == OPS:
            continue
        names.append(f"TELEGRAM_CHAT_ID_{slug.upper().replace('-', '_')}")
    return tuple(names)


def declared_scalar_names() -> tuple[str, ...]:
    return (
        BOT_TOKEN_ENV,
        PRINCIPAL_DM_CHAT_ID_ENV,
        CHAT_ID_ENV,
        *desk_chat_id_env_names(),
        FRED_API_KEY_ENV,
        POLYGON_API_KEY_ENV,
        POSTGRES_DSN_ENV,
    )


def delivery_env_file_path(environ: Mapping[str, str] | None = None) -> Path:
    env = environ if environ is not None else os.environ
    override = (env.get(DELIVERY_ENV_FILE_VAR) or "").strip()
    if override:
        return Path(override).expanduser()
    return DEFAULT_DELIVERY_ENV_FILE


def parse_env_file(text: str) -> dict[str, str]:
    """Dotenv-style KEY=VALUE. Empty values are omitted (treated as missing)."""
    parsed: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _ASSIGN_RE.match(line)
        if match is None:
            continue
        key, value = match.group(1), match.group(2).strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        if not value:
            continue
        parsed[key] = value
    return parsed


def parse_example_declared_names(text: str) -> tuple[str, ...]:
    """Collect KEY names from ``.env.example``, including commented placeholders."""
    names: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            line = line.lstrip("#").strip()
        match = _ASSIGN_RE.match(line)
        if match is None:
            continue
        key = match.group(1)
        if key in seen or not _KEY_RE.match(key):
            continue
        seen.add(key)
        names.append(key)
    return tuple(names)


@dataclass(frozen=True)
class DeliveryEnvLoad:
    path: str | None
    loaded: bool
    keys_loaded: tuple[str, ...]
    mode: str | None
    notes: tuple[str, ...]


def load_delivery_env_file(
    *,
    environ: dict[str, str] | None = None,
    path: Path | None = None,
    apply: bool = True,
) -> tuple[dict[str, str], DeliveryEnvLoad]:
    """Load the delivery env file into a mapping.

    File values win for keys present in the file. Keys already in process env
    and absent from the file are kept (CI). Never aliases PRINCIPAL_DM onto
    TELEGRAM_CHAT_ID.
    """
    source = dict(environ if environ is not None else os.environ)
    notes: list[str] = []
    file_path = path if path is not None else delivery_env_file_path(source)
    if not file_path.is_file():
        result = DeliveryEnvLoad(
            path=str(file_path),
            loaded=False,
            keys_loaded=(),
            mode=None,
            notes=(f"delivery env file not present: {file_path} (using process env)",),
        )
        return source, result
    mode = None
    try:
        mode = oct(file_path.stat().st_mode & 0o777)
        if file_path.stat().st_mode & 0o077:
            notes.append(f"delivery env file mode {mode} is not 0600 (shared-box file-path is a soft boundary)")
    except OSError as exc:
        notes.append(f"delivery env file stat failed: {type(exc).__name__}")
    try:
        parsed = parse_env_file(file_path.read_text(encoding="utf-8"))
    except OSError as exc:
        result = DeliveryEnvLoad(
            path=str(file_path),
            loaded=False,
            keys_loaded=(),
            mode=mode,
            notes=(f"delivery env file unreadable: {type(exc).__name__}",),
        )
        return source, result
    if CHAT_ID_ENV not in parsed and PRINCIPAL_DM_CHAT_ID_ENV in parsed:
        notes.append(
            f"{CHAT_ID_ENV} absent from delivery file; not defaulting to {PRINCIPAL_DM_CHAT_ID_ENV}"
        )
    merged = dict(source)
    for key, value in parsed.items():
        merged[key] = value
    if apply and environ is None:
        for key, value in parsed.items():
            os.environ[key] = value
    keys = tuple(sorted(parsed))
    notes.append(f"loaded {len(keys)} keys from {file_path} (names only; values not printed)")
    result = DeliveryEnvLoad(
        path=str(file_path),
        loaded=True,
        keys_loaded=keys,
        mode=mode,
        notes=tuple(notes),
    )
    return merged, result


def _present(environ: Mapping[str, str], name: str) -> bool:
    return bool((environ.get(name) or "").strip())


def _minio_present(environ: Mapping[str, str], *names: str) -> bool:
    return any(_present(environ, name) for name in names)


def object_store_missing_names(environ: Mapping[str, str]) -> tuple[str, ...]:
    """Return missing object-store env *names*. Empty tuple means env is complete."""
    backend = (environ.get(OBJECT_STORE_BACKEND_ENV) or "s3").strip().lower()
    if backend in {"none", "null", "disabled", "off"}:
        return ()
    if backend in {"memory", "inmemory", "in-memory"}:
        return ()
    if backend in {"filesystem", "fs", "file"}:
        return () if _present(environ, OBJECT_STORE_PATH_ENV) else (OBJECT_STORE_PATH_ENV,)
    missing: list[str] = []
    if not _minio_present(environ, MINIO_ENDPOINT_ENV, "S3_ENDPOINT"):
        missing.append(MINIO_ENDPOINT_ENV)
    if not _minio_present(environ, MINIO_ACCESS_KEY_ENV, "MINIO_ROOT_USER", "AWS_ACCESS_KEY_ID"):
        missing.append(MINIO_ACCESS_KEY_ENV)
    if not _minio_present(environ, MINIO_SECRET_KEY_ENV, "MINIO_ROOT_PASSWORD", "AWS_SECRET_ACCESS_KEY"):
        missing.append(MINIO_SECRET_KEY_ENV)
    return tuple(missing)


def _endpoint_host_port(endpoint: str) -> tuple[str, int]:
    raw = endpoint.strip()
    parsed = urlparse(raw if "://" in raw else f"http://{raw}")
    host = parsed.hostname or "127.0.0.1"
    if parsed.port is not None:
        port = parsed.port
    elif parsed.scheme == "https":
        port = 443
    else:
        port = 80
    return host, port


def probe_object_store(
    environ: Mapping[str, str],
    *,
    connect=None,
    timeout_s: float = OBJECT_STORE_PROBE_TIMEOUT_S,
) -> tuple[str, str, tuple[str, ...]]:
    """Return (state, note, missing_env_names). Never includes secrets."""
    if connect is None:
        connect = socket.create_connection
    backend = (environ.get(OBJECT_STORE_BACKEND_ENV) or "s3").strip().lower()
    missing = object_store_missing_names(environ)
    if missing:
        return STATE_MISSING, f"named failure; {DOWN_SERVICE}; missing {', '.join(missing)}", missing
    if backend in {"none", "null", "disabled", "off"}:
        return STATE_FOUND, "backend=none (raw objects disabled; honest)", ()
    if backend in {"memory", "inmemory", "in-memory"}:
        return STATE_FOUND, "backend=memory (development only; not durable)", ()
    if backend in {"filesystem", "fs", "file"}:
        return STATE_FOUND, "backend=filesystem (path not printed)", ()
    endpoint = (environ.get(MINIO_ENDPOINT_ENV) or environ.get("S3_ENDPOINT") or "").strip()
    _host, port = _endpoint_host_port(endpoint)
    try:
        sock = connect((_host, port), timeout=timeout_s)
    except OSError as exc:
        reason = "refused" if isinstance(exc, ConnectionRefusedError) or "refused" in str(exc).lower() else type(exc).__name__
        return STATE_DOWN, f"named failure; {DOWN_SERVICE} (:{port} {reason})", ()
    else:
        try:
            sock.close()
        except OSError:
            pass
        return STATE_FOUND, f"object store reachable on :{port} (host/values not printed)", ()


@dataclass(frozen=True)
class EnvVarStatus:
    name: str
    state: str
    severity: str
    note: str
    also_missing: tuple[str, ...] = ()

    @property
    def present(self) -> bool:
        return self.state == STATE_FOUND


@dataclass(frozen=True)
class PreflightReport:
    load: DeliveryEnvLoad
    items: tuple[EnvVarStatus, ...]
    purpose: str
    send: bool

    @property
    def missing_names(self) -> tuple[str, ...]:
        """Required-absent names only. NOT CONFIGURED is not missing."""
        names: list[str] = []
        fail_states = {STATE_MISSING, STATE_ABSENT, STATE_DOWN}
        for item in self.items:
            if item.state not in fail_states:
                continue
            names.append(item.name)
            names.extend(item.also_missing)
        return tuple(dict.fromkeys(names))

    @property
    def error_names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.items if not item.present and item.severity == SEVERITY_ERROR)

    @property
    def warning_names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.items if not item.present and item.severity == SEVERITY_WARNING)

    @property
    def ok(self) -> bool:
        return not self.error_names


def _severity(*, purpose: str, send: bool, name: str) -> str:
    if name == PRINCIPAL_DM_CHAT_ID_ENV or name in desk_chat_id_env_names():
        return SEVERITY_OPTIONAL
    if name == GET_CHAT_ITEM:
        return SEVERITY_ERROR
    if purpose == PURPOSE_CHECKLIST:
        return SEVERITY_ERROR
    if purpose == PURPOSE_DELIVER:
        if name == CHAT_ID_ENV:
            return SEVERITY_ERROR
        if name == BOT_TOKEN_ENV:
            return SEVERITY_ERROR if send else SEVERITY_WARNING
        if name in {OBJECT_STORE_ITEM, POLYGON_API_KEY_ENV}:
            return SEVERITY_ERROR if send else SEVERITY_WARNING
        return SEVERITY_WARNING
    return SEVERITY_WARNING


def _note_for(name: str, *, present: bool) -> str:
    if name == CHAT_ID_ENV:
        if present:
            return (
                "Hive group route (plain group; not a fallback to PRINCIPAL_DM); "
                "getChat verify each run; fail loud if id dead; value not printed"
            )
        return (
            "group route required for desk publish; MUST NOT silently default to "
            f"{PRINCIPAL_DM_CHAT_ID_ENV}"
        )
    if name == PRINCIPAL_DM_CHAT_ID_ENV:
        return "private Principal DM (step 5); value not printed; not a fallback for group route"
    if name == BOT_TOKEN_ENV:
        return "delivery file only; never Grok Secrets card; value not printed"
    if name == FRED_API_KEY_ENV:
        return (
            "no rates invent when missing (error_class=missing_env)"
            if not present
            else "present; value not printed"
        )
    if name == POLYGON_API_KEY_ENV:
        return (
            "named failure; no OHLCV invent (error_class=missing_env)"
            if not present
            else "Polygon key present (value not printed)"
        )
    if name == POSTGRES_DSN_ENV:
        return "Market Memory DSN; --no-db is ELIGIBLE only; value not printed"
    if name in desk_chat_id_env_names():
        return (
            "expected; Hive is a plain group (not a supergroup); forum topics not enabled; "
            "no message_thread_id; leave unset until Principal chooses topics or separate groups"
            if not present
            else "per-desk route present"
        )
    return "missing" if not present else "present"


def _scalar_state(name: str, present: bool) -> str:
    if present:
        return STATE_FOUND
    if name in desk_chat_id_env_names() or name == PRINCIPAL_DM_CHAT_ID_ENV:
        return STATE_NOT_CONFIGURED
    if name == POLYGON_API_KEY_ENV:
        return STATE_ABSENT
    return STATE_MISSING


def probe_group_get_chat(
    environ: Mapping[str, str],
    *,
    get_chat=None,
) -> tuple[str, str]:
    """Verify TELEGRAM_CHAT_ID still resolves. Never a sendMessage. Never prints ids."""
    token_present = _present(environ, BOT_TOKEN_ENV)
    chat_present = _present(environ, CHAT_ID_ENV)
    if not chat_present:
        return (
            STATE_SKIPPED,
            f"getChat skipped; {CHAT_ID_ENV} missing; not defaulting to {PRINCIPAL_DM_CHAT_ID_ENV}",
        )
    if not token_present:
        return STATE_SKIPPED, f"getChat skipped; {BOT_TOKEN_ENV} missing (cannot verify group id)"
    if get_chat is None:
        return STATE_SKIPPED, "getChat skipped (no probe wired)"
    raw = get_chat(environ)
    if not isinstance(raw, tuple) or len(raw) != 2:
        return STATE_MISSING, "getChat probe returned an unexpected result (id not printed)"
    state, note = raw
    return str(state), redact_env_values(str(note))


def preflight_env(
    environ: Mapping[str, str] | None = None,
    *,
    purpose: str = PURPOSE_CHECKLIST,
    send: bool = False,
    load: DeliveryEnvLoad | None = None,
    connect=None,
    get_chat=None,
) -> PreflightReport:
    """Full FOUND / MISSING / NOT CONFIGURED state. Never includes values."""
    env = dict(environ if environ is not None else os.environ)
    load_result = load or DeliveryEnvLoad(path=None, loaded=False, keys_loaded=(), mode=None, notes=())
    items: list[EnvVarStatus] = []
    for name in declared_scalar_names():
        present = _present(env, name)
        state = _scalar_state(name, present)
        sev = _severity(purpose=purpose, send=send, name=name)
        if present:
            sev = SEVERITY_OK if sev != SEVERITY_OPTIONAL else SEVERITY_OPTIONAL
        elif state == STATE_NOT_CONFIGURED:
            sev = SEVERITY_OPTIONAL
        items.append(
            EnvVarStatus(
                name=name,
                state=state,
                severity=sev,
                note=_note_for(name, present=present),
            )
        )
    obj_state, obj_note, obj_missing = probe_object_store(env, connect=connect)
    obj_sev = _severity(purpose=purpose, send=send, name=OBJECT_STORE_ITEM)
    if obj_state == STATE_FOUND:
        obj_sev = SEVERITY_OK
    items.append(
        EnvVarStatus(
            name=OBJECT_STORE_ITEM,
            state=obj_state,
            severity=obj_sev,
            note=obj_note,
            also_missing=obj_missing,
        )
    )
    gc_state, gc_note = probe_group_get_chat(env, get_chat=get_chat)
    gc_sev = SEVERITY_WARNING if gc_state == STATE_SKIPPED else _severity(purpose=purpose, send=send, name=GET_CHAT_ITEM)
    if gc_state == STATE_FOUND:
        gc_sev = SEVERITY_OK
    items.append(
        EnvVarStatus(
            name=GET_CHAT_ITEM,
            state=gc_state,
            severity=gc_sev,
            note=gc_note,
        )
    )
    return PreflightReport(load=load_result, items=tuple(items), purpose=purpose, send=send)


def format_preflight_lines(report: PreflightReport) -> tuple[str, ...]:
    """Human lines for stderr. Full state (found and missing). Values never interpolated."""
    lines: list[str] = []
    for note in report.load.notes:
        lines.append(f"env preflight: {redact_env_values(note)}")
    for item in report.items:
        lines.append(f"env preflight: {item.name} {item.state} — {item.note}")
    if CHAT_ID_ENV in report.error_names:
        lines.append(
            "env preflight: desk deliver will not use "
            f"{PRINCIPAL_DM_CHAT_ID_ENV} as a silent fallback for {CHAT_ID_ENV}"
        )
    missing = ", ".join(report.missing_names) if report.missing_names else "(none)"
    lines.append(f"env preflight: missing names: {missing}")
    if report.error_names:
        lines.append(f"env preflight: FAIL {', '.join(report.error_names)}")
    else:
        lines.append("env preflight: required values present (values not printed)")
    return tuple(redact_env_values(line) for line in lines)


def redact_env_values(text: str) -> str:
    """Strip KEY=value assignments and obvious token shapes from copy."""
    cleaned = text
    for name in (
        BOT_TOKEN_ENV,
        PRINCIPAL_DM_CHAT_ID_ENV,
        CHAT_ID_ENV,
        FRED_API_KEY_ENV,
        POLYGON_API_KEY_ENV,
        POSTGRES_DSN_ENV,
        MINIO_SECRET_KEY_ENV,
        MINIO_ACCESS_KEY_ENV,
        "AWS_SECRET_ACCESS_KEY",
        "AWS_ACCESS_KEY_ID",
    ):
        cleaned = re.sub(rf"{re.escape(name)}\s*=\s*\S+", f"{name}=***", cleaned)
    cleaned = re.sub(r"\b\d+:[A-Za-z0-9_-]{20,}\b", "***", cleaned)
    return cleaned


def looks_like_secret_name(name: str) -> bool:
    upper = name.upper()
    return any(token in upper for token in _SECRET_SUBSTRINGS)


def prepare_cli_env(
    *,
    purpose: str,
    send: bool = False,
    environ: dict[str, str] | None = None,
    path: Path | None = None,
    apply: bool = True,
    connect=None,
    get_chat=None,
) -> tuple[dict[str, str], PreflightReport]:
    merged, load = load_delivery_env_file(environ=environ, path=path, apply=apply)
    report = preflight_env(
        merged,
        purpose=purpose,
        send=send,
        load=load,
        connect=connect,
        get_chat=get_chat,
    )
    return merged, report
