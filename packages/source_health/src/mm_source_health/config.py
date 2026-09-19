"""Load inventory config (YAML only). Never read secret values from files."""

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
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_inventory_config(root: Path) -> dict[str, Any]:
    ingest = load_yaml(root / "config" / "ingest.yaml")
    macro = load_yaml(root / "config" / "briefing" / "macro.yaml")
    live = macro.get("live") if isinstance(macro.get("live"), dict) else {}
    calendar_path = root / "config" / "briefing" / "calendar.yaml"
    adapters = ingest.get("adapters") if isinstance(ingest.get("adapters"), dict) else {}
    edgar = adapters.get("edgar") if isinstance(adapters.get("edgar"), dict) else {}
    return {
        "hl_info_url": str(ingest.get("info_url") or DEFAULT_INFO_URL),
        "stooq": live.get("stooq") if isinstance(live.get("stooq"), dict) else {},
        "fred": live.get("fred") if isinstance(live.get("fred"), dict) else {},
        "edgar": edgar,
        "coingecko": live.get("coingecko") if isinstance(live.get("coingecko"), dict) else {},
        "calendar_path": calendar_path,
        "polygon": ingest.get("equities") if isinstance(ingest.get("equities"), dict) else {},
        "binance": ((ingest.get("crypto") or {}).get("spot_cross_check") or {}).get("binance")
        if isinstance(ingest.get("crypto"), dict)
        else {},
        "hl_structure": ((ingest.get("crypto") or {}).get("structure") or {})
        if isinstance(ingest.get("crypto"), dict)
        else {},
    }
