"""Pluggable macro/cross-asset fetchers. Fixtures are the deterministic default."""

from __future__ import annotations

import csv
import io
import os
from datetime import datetime
from typing import Any, Protocol
from urllib.parse import urlencode

import httpx

from mm_common.time import as_utc, parse_utc
from mm_briefing.models import ASSET_ORDER, AssetPrint, MacroSnapshot, worst_quality

ASSET_NAMES = {
    "ES": "S&P 500 futures",
    "NQ": "Nasdaq 100 futures",
    "US10Y": "US 10Y yield",
    "DXY": "US Dollar Index",
    "CL": "WTI crude",
    "VIX": "CBOE Volatility Index",
    "BTC": "Bitcoin",
    "ETH": "Ether",
}


class MacroFetcher(Protocol):
    name: str

    def fetch(self, as_of: datetime, *, prior_us_close: datetime) -> MacroSnapshot: ...


def parse_asset_row(row: dict[str, Any], *, source: str, default_quality: str = "ok") -> AssetPrint:
    last = _maybe_float(row.get("last") if "last" in row else row.get("close"))
    prior = _maybe_float(row.get("prior_close") if "prior_close" in row else row.get("priorClose"))
    opened = _maybe_float(row.get("open"))
    quality = str(row.get("data_quality") or default_quality)
    if last is None and prior is None:
        quality = worst_quality(quality, "partial")
    return AssetPrint(
        symbol=str(row.get("symbol") or "").upper(),
        name=str(row.get("name") or ASSET_NAMES.get(str(row.get("symbol") or "").upper(), str(row.get("symbol") or ""))),
        last=last,
        prior_close=prior,
        unit=str(row.get("unit") or "px"),
        data_quality=quality,
        source=source,
        open=opened,
    )


def snapshot_from_payload(
    payload: dict[str, Any],
    *,
    as_of: datetime,
    prior_us_close: datetime,
    source: str = "fixture",
) -> MacroSnapshot:
    raw_assets = payload.get("assets") or []
    assets = tuple(
        parse_asset_row(row, source=source, default_quality=str(payload.get("data_quality") or "ok"))
        for row in raw_assets
        if isinstance(row, dict) and row.get("symbol")
    )
    ordered = tuple(sorted(assets, key=lambda row: _order_key(row.symbol)))
    quality = str(payload.get("data_quality") or "ok")
    for row in ordered:
        quality = worst_quality(quality, row.data_quality)
    notes = payload.get("notes") or []
    if isinstance(notes, str):
        note_tuple = (notes,)
    else:
        note_tuple = tuple(str(item) for item in notes)
    as_of_value = payload.get("as_of")
    prior_value = payload.get("prior_us_close")
    return MacroSnapshot(
        as_of=parse_utc(str(as_of_value)) if as_of_value else as_utc(as_of),
        prior_us_close=parse_utc(str(prior_value)) if prior_value else as_utc(prior_us_close),
        assets=ordered,
        data_quality=quality,
        source=str(payload.get("source") or source),
        notes=note_tuple,
    )


def empty_snapshot(
    as_of: datetime,
    prior_us_close: datetime,
    *,
    reason: str,
    source: str = "none",
) -> MacroSnapshot:
    return MacroSnapshot(
        as_of=as_utc(as_of),
        prior_us_close=as_utc(prior_us_close),
        assets=(),
        data_quality="partial",
        source=source,
        notes=(reason,),
    )


class FixtureMacroFetcher:
    name = "fixture"

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def fetch(self, as_of: datetime, *, prior_us_close: datetime) -> MacroSnapshot:
        body = self.payload.get("macro") if "macro" in self.payload else self.payload
        if not isinstance(body, dict):
            return empty_snapshot(as_of, prior_us_close, reason="fixture missing macro object", source="fixture")
        return snapshot_from_payload(body, as_of=as_of, prior_us_close=prior_us_close, source="fixture")


class OffMacroFetcher:
    name = "off"

    def fetch(self, as_of: datetime, *, prior_us_close: datetime) -> MacroSnapshot:
        return empty_snapshot(
            as_of,
            prior_us_close,
            reason="macro mode is off; pass --fixture or enable a live fetcher",
            source="off",
        )


class LiveMacroFetcher:
    """Optional public fetchers. Missing keys / HTTP errors → data_quality=partial."""

    name = "live"

    def __init__(
        self,
        spec: dict[str, Any],
        *,
        client: httpx.Client | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.spec = spec
        self._client = client
        self._env = env

    def fetch(self, as_of: datetime, *, prior_us_close: datetime) -> MacroSnapshot:
        notes: list[str] = []
        assets: list[AssetPrint] = []
        live = self.spec.get("live") or {}
        if not live or not live.get("enabled", True):
            return empty_snapshot(as_of, prior_us_close, reason="live macro disabled", source="live")

        owns = self._client is None
        client = self._client or httpx.Client(timeout=20.0)
        try:
            stooq = live.get("stooq") or {}
            if stooq.get("enabled"):
                rows, note = self._fetch_stooq(client, stooq)
                assets.extend(rows)
                if note:
                    notes.append(note)
            fred = live.get("fred") or {}
            if fred.get("enabled"):
                rows, note = self._fetch_fred(client, fred)
                assets.extend(rows)
                if note:
                    notes.append(note)
            gecko = live.get("coingecko") or {}
            if gecko.get("enabled"):
                rows, note = self._fetch_coingecko(client, gecko)
                assets.extend(rows)
                if note:
                    notes.append(note)
        except httpx.HTTPError as exc:
            notes.append(f"live macro HTTP error: {exc.__class__.__name__}")
        finally:
            if owns:
                client.close()

        if not assets:
            return MacroSnapshot(
                as_of=as_utc(as_of),
                prior_us_close=as_utc(prior_us_close),
                assets=(),
                data_quality="partial",
                source="live",
                notes=tuple(notes) or ("live macro returned no assets",),
            )
        by_symbol: dict[str, AssetPrint] = {}
        for row in assets:
            by_symbol[row.symbol] = row
        ordered = tuple(by_symbol[sym] for sym in ASSET_ORDER if sym in by_symbol)
        extra = tuple(row for row in assets if row.symbol not in ASSET_ORDER)
        merged = ordered + extra
        quality = "ok"
        for row in merged:
            quality = worst_quality(quality, row.data_quality)
        if notes:
            quality = worst_quality(quality, "partial")
        return MacroSnapshot(
            as_of=as_utc(as_of),
            prior_us_close=as_utc(prior_us_close),
            assets=merged,
            data_quality=quality,
            source="live",
            notes=tuple(notes),
        )

    def _getenv(self, name: str) -> str | None:
        if self._env is not None:
            value = self._env.get(name)
        else:
            value = os.environ.get(name)
        if value is None or value.strip() == "":
            return None
        return value

    def _fetch_stooq(self, client: httpx.Client, spec: dict[str, Any]) -> tuple[list[AssetPrint], str | None]:
        symbols = spec.get("symbols") or {}
        base = str(spec.get("base_url") or "https://stooq.com/q/l/").rstrip("/") + "/"
        out: list[AssetPrint] = []
        errors = 0
        for symbol, ticker in symbols.items():
            query = urlencode({"s": ticker, "f": "sd2t2ohlcv", "h": "", "e": "csv"})
            url = f"{base}?{query}"
            try:
                response = client.get(url)
                response.raise_for_status()
                parsed = _parse_stooq_csv(response.text, symbol=str(symbol).upper())
                if parsed is None:
                    errors += 1
                    continue
                out.append(parsed)
            except httpx.HTTPError:
                errors += 1
        note = f"stooq failed for {errors} symbol(s)" if errors else None
        return out, note

    def _fetch_fred(self, client: httpx.Client, spec: dict[str, Any]) -> tuple[list[AssetPrint], str | None]:
        env_name = str(spec.get("api_key_env") or "FRED_API_KEY")
        key = self._getenv(env_name)
        if not key:
            return [], f"missing env {env_name}; FRED degraded"
        series = spec.get("series") or {}
        base = str(spec.get("base_url") or "https://api.stlouisfed.org/fred/series/observations")
        out: list[AssetPrint] = []
        errors = 0
        for symbol, series_id in series.items():
            params = {
                "series_id": series_id,
                "api_key": key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 2,
            }
            try:
                response = client.get(base, params=params)
                response.raise_for_status()
                payload = response.json()
                observations = payload.get("observations") or []
                values = [obs for obs in observations if str(obs.get("value")) not in {"", "."}]
                if not values:
                    errors += 1
                    continue
                last = _maybe_float(values[0].get("value"))
                prior = _maybe_float(values[1].get("value")) if len(values) > 1 else None
                out.append(
                    AssetPrint(
                        symbol=str(symbol).upper(),
                        name=ASSET_NAMES.get(str(symbol).upper(), str(symbol).upper()),
                        last=last,
                        prior_close=prior,
                        unit="%" if str(symbol).upper() == "US10Y" else "idx",
                        data_quality="ok" if last is not None else "partial",
                        source="fred",
                    )
                )
            except httpx.HTTPError:
                errors += 1
        note = f"fred failed for {errors} series" if errors else None
        return out, note

    def _fetch_coingecko(self, client: httpx.Client, spec: dict[str, Any]) -> tuple[list[AssetPrint], str | None]:
        ids = spec.get("ids") or {}
        if not ids:
            return [], None
        base = str(spec.get("base_url") or "https://api.coingecko.com/api/v3/simple/price")
        params = {
            "ids": ",".join(str(v) for v in ids.values()),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        }
        try:
            response = client.get(base, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError:
            return [], "coingecko HTTP error"
        out: list[AssetPrint] = []
        for symbol, gecko_id in ids.items():
            body = payload.get(gecko_id) or {}
            last = _maybe_float(body.get("usd"))
            change_pct = _maybe_float(body.get("usd_24h_change"))
            prior = None
            if last is not None and change_pct is not None:
                prior = last / (1.0 + change_pct / 100.0)
            out.append(
                AssetPrint(
                    symbol=str(symbol).upper(),
                    name=ASSET_NAMES.get(str(symbol).upper(), str(symbol).upper()),
                    last=last,
                    prior_close=prior,
                    unit="usd",
                    data_quality="ok" if last is not None else "partial",
                    source="coingecko",
                )
            )
        return out, None


def _parse_stooq_csv(text: str, *, symbol: str) -> AssetPrint | None:
    reader = csv.DictReader(io.StringIO(text.strip()))
    rows = list(reader)
    if not rows:
        return None
    row = rows[0]
    last = _maybe_float(row.get("Close") or row.get("close"))
    opened = _maybe_float(row.get("Open") or row.get("open"))
    if last is None:
        return None
    return AssetPrint(
        symbol=symbol,
        name=ASSET_NAMES.get(symbol, symbol),
        last=last,
        prior_close=opened,
        unit="idx" if symbol in {"DXY", "VIX"} else "pts" if symbol in {"ES", "NQ"} else "usd",
        data_quality="ok",
        source="stooq",
        open=opened,
    )


def _maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _order_key(symbol: str) -> tuple[int, str]:
    try:
        return (ASSET_ORDER.index(symbol), symbol)
    except ValueError:
        return (len(ASSET_ORDER), symbol)


def fetcher_for_mode(
    mode: str,
    *,
    fixture_payload: dict[str, Any] | None = None,
    macro_spec: dict[str, Any] | None = None,
    client: httpx.Client | None = None,
    env: dict[str, str] | None = None,
) -> MacroFetcher:
    normalized = (mode or "off").strip().lower()
    if normalized == "fixture":
        return FixtureMacroFetcher(fixture_payload or {})
    if normalized == "live":
        return LiveMacroFetcher(macro_spec or {}, client=client, env=env)
    return OffMacroFetcher()
