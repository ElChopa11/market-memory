"""Instrument + ingest settings from repo config (no secrets)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mm_ingest.hl_info import DEFAULT_INFO_URL


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "packages").is_dir():
            return candidate
    return here


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_instruments(path: Path | None = None) -> list[str]:
    instruments_path = path or (repo_root() / "config" / "instruments" / "perps.yaml")
    data = load_yaml(instruments_path)
    rows = data.get("instruments") or []
    symbols = []
    for row in rows:
        if row.get("enabled", True):
            symbols.append(str(row["symbol"]).upper())
    return symbols


def load_equity_instruments(path: Path | None = None) -> list[str]:
    """Locked universe equities — ticker set unchanged unless Principal expands membership."""
    universe_path = path or (repo_root() / "config" / "universe.yaml")
    data = load_yaml(universe_path)
    return [str(symbol).upper() for symbol in (data.get("equities") or [])]


def load_ingest_settings(path: Path | None = None) -> dict[str, Any]:
    settings_path = path or (repo_root() / "config" / "ingest.yaml")
    defaults: dict[str, Any] = {
        "info_url": DEFAULT_INFO_URL,
        "candle_interval": "1h",
        "stale_after_seconds": 120,
        "store_raw_objects": True,
        "source_trust_tier": 4,
        "equities": {"vendor": "polygon", "api_key_env": "POLYGON_API_KEY"},
    }
    if settings_path.is_file():
        loaded = load_yaml(settings_path)
        defaults.update({k: v for k, v in loaded.items() if v is not None})
    return defaults
