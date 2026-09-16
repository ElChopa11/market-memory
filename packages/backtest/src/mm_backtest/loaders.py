"""Load JSON or parquet candle fixtures. Raw dicts are scanned for look-ahead first."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mm_backtest.bars import Bar, KnowledgeFact, parse_as_of
from mm_backtest.errors import BacktestError
from mm_backtest.leakage import scan_fixture_for_lookahead


def load_fixture_file(path: Path, *, strict: bool = True) -> tuple[list[Bar], list[KnowledgeFact], dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix in {".json", ".jsonl"}:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return load_fixture_payload(raw, strict=strict)
    if suffix in {".parquet", ".pq"}:
        return load_parquet(path, strict=strict)
    raise BacktestError(f"unsupported fixture type: {path.suffix} (use .json or .parquet)")


def load_fixture_payload(
    raw: Any,
    *,
    strict: bool = True,
    default_instrument: str | None = None,
) -> tuple[list[Bar], list[KnowledgeFact], dict[str, Any]]:
    if isinstance(raw, list):
        payload: dict[str, Any] = {"bars": raw}
    elif isinstance(raw, dict):
        payload = raw
    else:
        raise BacktestError("fixture must be an object or a list of bars")

    findings = scan_fixture_for_lookahead(payload)
    if findings and strict:
        from mm_backtest.errors import FixtureLookAheadError

        detail = "; ".join(item.message for item in findings)
        raise FixtureLookAheadError(f"look-ahead in fixture: {detail}")

    instrument = (
        default_instrument
        or payload.get("instrument")
        or payload.get("symbol")
        or "BTC"
    )
    interval = str(payload.get("interval") or payload.get("candle_interval") or "1h")
    bars = [_parse_bar(item, default_instrument=str(instrument), default_interval=interval) for item in _bar_items(payload)]
    bars.sort(key=lambda bar: (bar.available_at, bar.market_time, bar.instrument))
    facts = [_parse_fact(item) for item in payload.get("observations") or payload.get("facts") or []]
    facts.sort(key=lambda fact: (fact.ingested_at, fact.id))
    meta = {
        "instrument": str(instrument),
        "interval": interval,
        "strict": strict,
        "lookahead_findings": [item.message for item in findings],
    }
    return bars, facts, meta


def load_parquet(path: Path, *, strict: bool = True, default_instrument: str = "BTC") -> tuple[list[Bar], list[KnowledgeFact], dict[str, Any]]:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover
        raise BacktestError("pyarrow is required to read parquet fixtures") from exc
    table = pq.read_table(path)
    rows = table.to_pylist()
    payload: dict[str, Any] = {"bars": rows, "instrument": default_instrument}
    if "instrument" in table.column_names and rows:
        payload["instrument"] = rows[0].get("instrument") or default_instrument
    return load_fixture_payload(payload, strict=strict, default_instrument=default_instrument)


def write_parquet(path: Path, bars: list[Bar]) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover
        raise BacktestError("pyarrow is required to write parquet fixtures") from exc
    rows = [bar.canonical() for bar in bars]
    table = pa.Table.from_pylist(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def _bar_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "bars" in payload:
        items = payload["bars"]
    elif "candles" in payload:
        candles = payload["candles"]
        if isinstance(candles, dict):
            items = []
            for symbol, rows in candles.items():
                for row in rows:
                    item = dict(row)
                    item.setdefault("instrument", symbol)
                    items.append(item)
        else:
            items = list(candles)
    else:
        raise BacktestError("fixture has no bars/candles")
    return [item if isinstance(item, dict) else dict(item) for item in items]


def _parse_bar(raw: dict[str, Any], *, default_instrument: str, default_interval: str) -> Bar:
    instrument = str(raw.get("instrument") or raw.get("s") or raw.get("symbol") or default_instrument)
    interval = str(raw.get("interval") or raw.get("i") or default_interval)
    market_time = _first(raw, "market_time", "T", "t", "time", "close_time")
    if market_time is None:
        raise BacktestError(f"bar missing market_time: {raw!r}")
    available_at = _first(raw, "available_at", "as_of", "ingested_at", "knowledge_time")
    if available_at is None:
        available_at = market_time
    return Bar(
        instrument=instrument,
        market_time=parse_as_of(market_time),
        available_at=parse_as_of(available_at),
        open=raw.get("open", raw.get("o")),
        high=raw.get("high", raw.get("h")),
        low=raw.get("low", raw.get("l")),
        close=raw.get("close", raw.get("c")),
        volume=raw.get("volume", raw.get("v", 0)),
        interval=interval,
    )


def _parse_fact(raw: dict[str, Any]) -> KnowledgeFact:
    ingested = raw.get("ingested_at") or raw.get("as_of") or raw.get("available_at")
    if ingested is None:
        raise BacktestError(f"observation missing ingested_at: {raw!r}")
    return KnowledgeFact(
        id=str(raw.get("id") or raw.get("observation_id") or ""),
        ingested_at=parse_as_of(ingested),
        instrument=raw.get("instrument"),
        claim_text=str(raw.get("claim_text") or raw.get("claim") or ""),
        payload=dict(raw.get("payload") or {}),
    )


def _first(raw: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return None
