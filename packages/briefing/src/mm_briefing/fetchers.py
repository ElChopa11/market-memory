"""Pluggable macro/cross-asset fetchers. Fixtures are the deterministic default."""

from __future__ import annotations

import csv
import io
import os
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any, Protocol
from urllib.parse import urlencode

import httpx

from mm_common.http import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_TIMEOUT,
    ERROR_PARSE,
    http_get,
    missing_env_notes,
)
from mm_common.time import as_utc, from_unix_ms, parse_utc
from mm_ingest.sources import POLYGON_BASE_URL
from mm_briefing.freshness import (
    DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS,
    FreshnessConfig,
    gate_snapshot_freshness,
    load_freshness_config,
    quality_from_observation_age,
)
from mm_briefing.models import ASSET_ORDER, AssetPrint, HLInstrumentState, MacroSnapshot, worst_quality

# Pulse slot → preferred live source. Stooq is not primary (SRC-STOOQ-404).
# Crypto What-moved slots use HL mid (see crypto_pulse).
SLOT_SOURCE = {
    "ES": "polygon",
    "NQ": "polygon",
    "US10Y": "fred",
    "DXY": "polygon",
    "CL": "polygon",
    "VIX": "polygon",
    "BTC": "hyperliquid",
    "ETH": "hyperliquid",
}

# Default display names. Live polygon rows override with config labels (ETF proxies).
ASSET_NAMES = {
    "ES": "SPY ETF (proxy for S&P 500; not ES futures)",
    "NQ": "QQQ ETF (proxy for Nasdaq-100; not NQ futures)",
    "US10Y": "US 10Y yield",
    "DXY": "UUP ETF (USD proxy; not DX futures / DXY)",
    "CL": "USO ETF (WTI oil proxy; not CL futures)",
    "VIX": "CBOE VIX (structurally unavailable without Cboe entitlement)",
    "BTC": "HL BTC-USDC perp mid (not CoinGecko spot)",
    "ETH": "HL ETH-USDC perp mid (not CoinGecko spot)",
}

CRYPTO_PULSE_SYMBOLS = ("BTC", "ETH")
DEFAULT_CRYPTO_PULSE_SOR = "hyperliquid"
DEFAULT_CRYPTO_DIVERGENCE_MAX_BPS = 100.0
DEFAULT_CRYPTO_DIVERGENCE_MAX_BPS_RAW_MID = 300.0
CRYPTO_PULSE_SOR_NOTE = (
    "crypto pulse SoR=hyperliquid (mid_px for BTC/ETH What-moved slots); "
    "CoinGecko always fetched on --live as secondary DQ — both values kept in notes"
)
_FIXTURE_PROTECTED_SOURCES = frozenset({"fixture"})
SOURCE_DIVERGENCE_CLASS = "source_divergence"
METRIC_CG_VS_HL_ORACLE = "cg_vs_hl_oracle"
METRIC_RAW_MID_VS_SPOT = "raw_mid_vs_spot"


class MacroFetcher(Protocol):
    name: str

    def fetch(self, as_of: datetime, *, prior_us_close: datetime) -> MacroSnapshot: ...


def parse_asset_row(
    row: dict[str, Any],
    *,
    source: str,
    default_quality: str = "ok",
    as_of: datetime | None = None,
) -> AssetPrint:
    last = _maybe_float(row.get("last") if "last" in row else row.get("close"))
    prior = _maybe_float(row.get("prior_close") if "prior_close" in row else row.get("priorClose"))
    opened = _maybe_float(row.get("open"))
    quality = str(row.get("data_quality") or default_quality)
    if last is None and prior is None:
        quality = "unavailable"
    as_of_raw = row.get("as_of")
    parsed_as_of = parse_utc(str(as_of_raw)) if as_of_raw else as_of
    row_source = str(row.get("source") or source or "none")
    return AssetPrint(
        symbol=str(row.get("symbol") or "").upper(),
        name=str(row.get("name") or ASSET_NAMES.get(str(row.get("symbol") or "").upper(), str(row.get("symbol") or ""))),
        last=last,
        prior_close=prior,
        unit=str(row.get("unit") or "px"),
        data_quality=quality,
        source=row_source,
        open=opened,
        as_of=parsed_as_of,
        observation_id=str(row["observation_id"]) if row.get("observation_id") else None,
        source_url=str(row["source_url"]) if row.get("source_url") else None,
    )


def snapshot_from_payload(
    payload: dict[str, Any],
    *,
    as_of: datetime,
    prior_us_close: datetime,
    source: str = "fixture",
) -> MacroSnapshot:
    as_of_value = payload.get("as_of")
    prior_value = payload.get("prior_us_close")
    snap_as_of = parse_utc(str(as_of_value)) if as_of_value else as_utc(as_of)
    raw_assets = payload.get("assets") or []
    assets = tuple(
        parse_asset_row(
            row,
            source=source,
            default_quality=str(payload.get("data_quality") or "ok"),
            as_of=snap_as_of,
        )
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
    return MacroSnapshot(
        as_of=snap_as_of,
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
        data_quality="unavailable",
        source=source,
        notes=(reason,),
    )


def complete_cross_asset(
    snapshot: MacroSnapshot,
    *,
    freshness: FreshnessConfig | None = None,
) -> MacroSnapshot:
    """Fill required slots with unavailable rows so missing sources are visible.

    Applies cadence freshness gates (FRED daily lag, etc.) so fetch-ok alone
    cannot label an aged observation as fresh for all Pulse consumers.
    """
    by_symbol = snapshot.by_symbol()
    filled: list[AssetPrint] = []
    for symbol in ASSET_ORDER:
        if symbol in by_symbol:
            filled.append(by_symbol[symbol])
            continue
        filled.append(
            AssetPrint(
                symbol=symbol,
                name=ASSET_NAMES.get(symbol, symbol),
                last=None,
                prior_close=None,
                data_quality="unavailable",
                source=SLOT_SOURCE.get(symbol, "none"),
                as_of=snapshot.as_of,
            )
        )
    extra = [row for row in snapshot.assets if row.symbol not in ASSET_ORDER]
    assets = tuple(filled + extra)
    quality = snapshot.data_quality
    for row in assets:
        quality = worst_quality(quality, row.data_quality)
    completed = MacroSnapshot(
        as_of=snapshot.as_of,
        prior_us_close=snapshot.prior_us_close,
        assets=assets,
        data_quality=quality,
        source=snapshot.source,
        notes=snapshot.notes,
    )
    return gate_snapshot_freshness(completed, config=freshness)


def apply_crypto_pulse_from_hl(
    snapshot: MacroSnapshot,
    hl: tuple[HLInstrumentState, ...],
    *,
    source_of_record: str = DEFAULT_CRYPTO_PULSE_SOR,
    macro_config: dict[str, Any] | None = None,
) -> MacroSnapshot:
    """Route BTC/ETH What-moved slots to HL mid when Hyperliquid is the SoR.

    Honest rules (Principal Fix 3 fold a+c):
    - Table last = mid_px when present; never invent a prior_close from mid alone
    - CoinGecko is always fetched on --live; CG values + unavailable notes are retained
    - Normal: note CG vs HL (oracle-preferred) with both source tags and as_of stamps
    - Escalation: |divergence| > path threshold → error_class=source_divergence + degrade
    - Fixture rows stay untouched so frozen hashes remain pinned
    """
    sor = (source_of_record or DEFAULT_CRYPTO_PULSE_SOR).strip().lower()
    if sor not in {"hyperliquid", "hl"}:
        return snapshot

    by_hl = {state.instrument.upper(): state for state in hl}
    by_symbol = snapshot.by_symbol()
    replaced: list[AssetPrint] = []
    extra_notes: list[str] = []
    changed = False

    for symbol in CRYPTO_PULSE_SYMBOLS:
        existing = by_symbol.get(symbol)
        if existing is not None and existing.source in _FIXTURE_PROTECTED_SOURCES:
            replaced.append(existing)
            continue

        cg_print = existing if existing is not None and existing.source == "coingecko" else None
        state = by_hl.get(symbol)
        mid = state.metric("mid_px") if state is not None else None
        oracle = state.metric("oracle_px") if state is not None else None
        mid_value = _maybe_float(mid.value) if mid is not None else None
        oracle_value = _maybe_float(oracle.value) if oracle is not None else None
        source_label = (
            state.source
            if state is not None and state.source
            else SLOT_SOURCE.get(symbol, "hyperliquid")
        )
        hl_as_of = None
        if mid is not None:
            hl_as_of = mid.as_of_knowledge or (state.as_of_knowledge if state else None)
        if hl_as_of is None and state is not None:
            hl_as_of = state.as_of_knowledge

        if mid_value is not None and mid is not None:
            quality = mid.data_quality or (state.data_quality if state else "ok")
            if quality in {"unavailable", "none"}:
                quality = "ok"
            compare_note, escalated = _crypto_compare_note(
                symbol,
                cg_print=cg_print,
                hl_mid=mid_value,
                hl_oracle=oracle_value,
                hl_source=source_label,
                hl_as_of=hl_as_of or snapshot.as_of,
                macro_config=macro_config,
            )
            if compare_note:
                extra_notes.append(compare_note)
            if escalated:
                quality = worst_quality(quality, "partial")
            replaced.append(
                AssetPrint(
                    symbol=symbol,
                    name=ASSET_NAMES.get(symbol, symbol),
                    last=mid_value,
                    prior_close=None,
                    unit="usd",
                    data_quality=quality,
                    source=source_label,
                    as_of=hl_as_of or snapshot.as_of,
                    observation_id=mid.observation_id,
                    source_url=mid.source_url,
                )
            )
            changed = True
            continue

        if cg_print is not None and cg_print.last is not None:
            extra_notes.append(
                f"{symbol}: SoR hyperliquid mid unavailable; retained CoinGecko spot="
                f"{_fmt_px(cg_print.last)} "
                f"[source=coingecko; as_of={_fmt_as_of(cg_print.as_of)}; quality={cg_print.data_quality}]"
            )
        replaced.append(
            AssetPrint(
                symbol=symbol,
                name=ASSET_NAMES.get(symbol, symbol),
                last=None,
                prior_close=None,
                unit="usd",
                data_quality="unavailable",
                source=source_label if state is not None else SLOT_SOURCE.get(symbol, "hyperliquid"),
                as_of=snapshot.as_of,
            )
        )
        if existing is None or existing.last is not None or existing.source == "coingecko":
            changed = True

    if not changed and all(
        (by_symbol.get(sym) is not None and by_symbol[sym].source in _FIXTURE_PROTECTED_SOURCES)
        for sym in CRYPTO_PULSE_SYMBOLS
        if sym in by_symbol
    ):
        return snapshot

    merged: list[AssetPrint] = []
    crypto_map = {row.symbol: row for row in replaced}
    seen_crypto: set[str] = set()
    for row in snapshot.assets:
        if row.symbol in crypto_map:
            merged.append(crypto_map[row.symbol])
            seen_crypto.add(row.symbol)
        else:
            merged.append(row)
    for symbol in CRYPTO_PULSE_SYMBOLS:
        if symbol not in seen_crypto and symbol in crypto_map:
            merged.append(crypto_map[symbol])

    ordered = tuple(sorted(merged, key=lambda row: _order_key(row.symbol)))
    quality = snapshot.data_quality
    for row in ordered:
        quality = worst_quality(quality, row.data_quality)
    notes = list(snapshot.notes)
    if CRYPTO_PULSE_SOR_NOTE not in notes:
        notes.append(CRYPTO_PULSE_SOR_NOTE)
    for note in extra_notes:
        if note not in notes:
            notes.append(note)
    return MacroSnapshot(
        as_of=snapshot.as_of,
        prior_us_close=snapshot.prior_us_close,
        assets=ordered,
        data_quality=quality,
        source=snapshot.source,
        notes=tuple(notes),
    )


def crypto_pulse_source_of_record(macro: dict[str, Any] | None) -> str:
    """Preferred source for BTC/ETH What-moved slots (default: Hyperliquid mid)."""
    body = (macro or {}).get("crypto_pulse") if isinstance(macro, dict) else None
    if not isinstance(body, dict):
        return DEFAULT_CRYPTO_PULSE_SOR
    raw = str(body.get("source_of_record") or DEFAULT_CRYPTO_PULSE_SOR).strip().lower()
    return raw or DEFAULT_CRYPTO_PULSE_SOR


def crypto_pulse_max_bps(macro: dict[str, Any] | None, symbol: str, *, path: str = "oracle") -> float:
    """Escalation threshold in bps. Oracle path uses max_bps; raw mid uses max_bps_raw_mid_vs_spot."""
    body = (macro or {}).get("crypto_pulse") if isinstance(macro, dict) else None
    if not isinstance(body, dict):
        return (
            DEFAULT_CRYPTO_DIVERGENCE_MAX_BPS_RAW_MID
            if path == "raw"
            else DEFAULT_CRYPTO_DIVERGENCE_MAX_BPS
        )
    div = body.get("divergence") if isinstance(body.get("divergence"), dict) else {}
    key = "max_bps_raw_mid_vs_spot" if path == "raw" else "max_bps"
    default_fallback = (
        DEFAULT_CRYPTO_DIVERGENCE_MAX_BPS_RAW_MID if path == "raw" else DEFAULT_CRYPTO_DIVERGENCE_MAX_BPS
    )
    default = _maybe_float(div.get(key))
    if default is None:
        default = default_fallback
    overrides = div.get("symbols") if isinstance(div.get("symbols"), dict) else {}
    raw = overrides.get(symbol) or overrides.get(symbol.upper())
    if isinstance(raw, dict):
        override = _maybe_float(raw.get(key))
        if override is not None:
            return override
    elif path != "raw":
        override = _maybe_float(raw)
        if override is not None:
            return override
    return float(default)


def _crypto_compare_note(
    symbol: str,
    *,
    cg_print: AssetPrint | None,
    hl_mid: float,
    hl_oracle: float | None,
    hl_source: str,
    hl_as_of: datetime,
    macro_config: dict[str, Any] | None,
) -> tuple[str | None, bool]:
    """Build (a) dual-source compare note; (c) escalate when |div| > path threshold."""
    if cg_print is None or cg_print.last is None:
        return None, False
    cg_spot = float(cg_print.last)
    abs_bps, mode, _ref = _crypto_divergence_bps(cg_spot, hl_mid=hl_mid, hl_oracle=hl_oracle)
    if abs_bps is None:
        return None, False
    if mode == "oracle_adjusted":
        metric = METRIC_CG_VS_HL_ORACLE
        max_bps = crypto_pulse_max_bps(macro_config, symbol, path="oracle")
        confidence = "normal"
        basis_note = ""
    else:
        metric = METRIC_RAW_MID_VS_SPOT
        max_bps = crypto_pulse_max_bps(macro_config, symbol, path="raw")
        confidence = "low"
        basis_note = "; basis not subtracted"
    oracle_txt = _fmt_px(hl_oracle) if hl_oracle is not None else "n/a"
    note = (
        f"{symbol} compare: SoR {hl_source} mid={_fmt_px(hl_mid)} "
        f"[source={hl_source}; as_of={_fmt_as_of(hl_as_of)}]; "
        f"CoinGecko spot={_fmt_px(cg_spot)} "
        f"[source=coingecko; as_of={_fmt_as_of(cg_print.as_of)}; "
        f"quality={cg_print.data_quality}]; "
        f"HL oracle={oracle_txt}; divergence={abs_bps:.1f}bps "
        f"(metric={metric}; confidence={confidence}{basis_note}); "
        f"threshold={max_bps:.0f}bps"
    )
    escalated = abs_bps > max_bps
    if escalated:
        note = (
            f"{symbol} DQ event error_class={SOURCE_DIVERGENCE_CLASS}: "
            f"|divergence|={abs_bps:.1f}bps > max_bps={max_bps:.0f}; "
            f"metric={metric}; confidence={confidence}"
            f"{basis_note}; "
            f"CoinGecko spot={_fmt_px(cg_spot)} [source=coingecko; as_of={_fmt_as_of(cg_print.as_of)}]; "
            f"hyperliquid mid={_fmt_px(hl_mid)} [source={hl_source}; as_of={_fmt_as_of(hl_as_of)}]; "
            f"hyperliquid oracle={oracle_txt} — SoR mid still printed; slot quality degraded"
        )
    return note, escalated


def _crypto_divergence_bps(
    cg_spot: float,
    *,
    hl_mid: float | None,
    hl_oracle: float | None,
) -> tuple[float | None, str, float | None]:
    """Preferred: |CG − HL oracle| / oracle. Fallback: |CG − mid| / mid (labeled)."""
    if hl_oracle is not None and hl_oracle != 0:
        return abs(cg_spot - hl_oracle) / abs(hl_oracle) * 10_000.0, "oracle_adjusted", hl_oracle
    if hl_mid is not None and hl_mid != 0:
        return (
            abs(cg_spot - hl_mid) / abs(hl_mid) * 10_000.0,
            "raw_mid_vs_spot",
            hl_mid,
        )
    return None, "unavailable", None


def _fmt_as_of(value: datetime | None) -> str:
    if value is None:
        return "n/a"
    return as_utc(value).isoformat()


def _fmt_px(value: float | None) -> str:
    if value is None:
        return "n/a"
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text if text else "0"


def live_macro_spec(macro: dict[str, Any]) -> dict[str, Any]:
    """Enable configured public maps for a --live run. Missing keys stay visible."""
    spec = dict(macro)
    live = dict(spec.get("live") or {})
    live["enabled"] = True
    stooq = dict(live.get("stooq") or {})
    if stooq.get("symbols"):
        stooq["enabled"] = True
    live["stooq"] = stooq
    polygon = dict(live.get("polygon") or {})
    if polygon.get("symbols") or polygon.get("structural_unavailable"):
        polygon["enabled"] = True
    live["polygon"] = polygon
    gecko = dict(live.get("coingecko") or {})
    if gecko.get("ids"):
        gecko["enabled"] = True
    live["coingecko"] = gecko
    fred = dict(live.get("fred") or {})
    if fred.get("series"):
        fred["enabled"] = True
    live["fred"] = fred
    spec["live"] = live
    spec["mode"] = "live"
    return spec


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
        sleep: Callable[[float], None] | None = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> None:
        self.spec = spec
        self._client = client
        self._env = env
        self._sleep = sleep or time.sleep
        self._max_attempts = max_attempts
        self._freshness = load_freshness_config(spec)

    def fetch(self, as_of: datetime, *, prior_us_close: datetime) -> MacroSnapshot:
        notes: list[str] = []
        assets: list[AssetPrint] = []
        live = self.spec.get("live") or {}
        if not live or not live.get("enabled", True):
            return empty_snapshot(as_of, prior_us_close, reason="live macro disabled", source="live")
        captured = as_utc(as_of)

        timeout = float(live.get("timeout_seconds") or DEFAULT_TIMEOUT)
        owns = self._client is None
        client = self._client or httpx.Client(timeout=timeout)
        try:
            # Stooq optional canary only (SRC-STOOQ-404). Polygon ETF proxies overwrite
            # the same slot symbols when both are enabled so Pulse is never stooq-only.
            stooq = live.get("stooq") or {}
            if stooq.get("enabled"):
                rows, note = self._fetch_stooq(client, stooq, captured=captured)
                assets.extend(rows)
                if note:
                    notes.append(note)
            polygon = live.get("polygon") or {}
            if polygon.get("enabled"):
                rows, note = self._fetch_polygon(client, polygon, captured=captured)
                assets.extend(rows)
                if note:
                    notes.append(note)
            fred = live.get("fred") or {}
            if fred.get("enabled"):
                rows, note = self._fetch_fred(client, fred, captured=captured)
                assets.extend(rows)
                if note:
                    notes.append(note)
            gecko = live.get("coingecko") or {}
            if gecko.get("enabled"):
                rows, note = self._fetch_coingecko(client, gecko, captured=captured)
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
                data_quality="unavailable",
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
        snap = MacroSnapshot(
            as_of=as_utc(as_of),
            prior_us_close=as_utc(prior_us_close),
            assets=merged,
            data_quality=quality,
            source="live",
            notes=tuple(notes),
        )
        return gate_snapshot_freshness(snap, reference_as_of=captured, config=self._freshness)

    def _getenv(self, name: str) -> str | None:
        if self._env is not None:
            value = self._env.get(name)
        else:
            value = os.environ.get(name)
        if value is None or value.strip() == "":
            return None
        return value

    def _fetch_stooq(
        self, client: httpx.Client, spec: dict[str, Any], *, captured: datetime
    ) -> tuple[list[AssetPrint], str | None]:
        symbols = spec.get("symbols") or {}
        base = str(spec.get("base_url") or "https://stooq.com/q/l/").rstrip("/") + "/"
        out: list[AssetPrint] = []
        errors = 0
        missing: list[str] = []
        classes: list[str] = []
        max_attempts_seen = 1
        for symbol, ticker in symbols.items():
            query = urlencode({"s": ticker, "f": "sd2t2ohlcv", "h": "", "e": "csv"})
            url = f"{base}?{query}"
            result = http_get(
                client,
                url,
                max_attempts=self._max_attempts,
                sleep=self._sleep,
            )
            max_attempts_seen = max(max_attempts_seen, result.attempts)
            if not result.ok or result.text is None:
                errors += 1
                missing.append(str(symbol).upper())
                classes.append(result.error_class)
                continue
            parsed = _parse_stooq_csv(
                result.text,
                symbol=str(symbol).upper(),
                captured=captured,
                source_url=url,
            )
            if parsed is None:
                errors += 1
                missing.append(str(symbol).upper())
                classes.append(ERROR_PARSE)
                continue
            out.append(parsed)
        note = None
        if errors:
            class_txt = ", ".join(dict.fromkeys(classes)) or "error"
            note = (
                f"stooq unavailable (error_class={class_txt}) for {errors} symbol(s): "
                f"{', '.join(missing)}; no scrape fallback (ToS); "
                f"attempts<={max_attempts_seen} (retry only timeout/5xx/429). "
                "See docs/runbooks/market-pulse.md and lab data source-health. "
                "SRC-STOOQ-404; prefer polygon ETF proxies."
            )
        return out, note

    def _fetch_polygon(
        self, client: httpx.Client, spec: dict[str, Any], *, captured: datetime
    ) -> tuple[list[AssetPrint], str | None]:
        """Stocks-plan ETF proxies for Pulse slots. Never invent CME futures prints."""
        env_name = str(spec.get("api_key_env") or "POLYGON_API_KEY")
        key = self._getenv(env_name)
        symbols = spec.get("symbols") or {}
        structural = spec.get("structural_unavailable") or {}
        base = str(spec.get("base_url") or POLYGON_BASE_URL).rstrip("/")
        lookback = int(spec.get("lookback_calendar_days") or 10)
        out: list[AssetPrint] = []
        note_parts: list[str] = []

        for symbol, meta in structural.items():
            reason = _polygon_structural_reason(meta)
            slot = str(symbol).upper()
            out.append(
                AssetPrint(
                    symbol=slot,
                    name=ASSET_NAMES.get(slot, slot),
                    last=None,
                    prior_close=None,
                    unit="idx",
                    data_quality="unavailable",
                    source="polygon",
                    as_of=captured,
                    source_url=base,
                )
            )
            note_parts.append(f"polygon structural unavailable for {slot}: {reason}")

        if not symbols:
            return out, "; ".join(note_parts) if note_parts else None

        if not key:
            for symbol, meta in symbols.items():
                slot = str(symbol).upper()
                label = _polygon_label(slot, meta)
                out.append(
                    AssetPrint(
                        symbol=slot,
                        name=label,
                        last=None,
                        prior_close=None,
                        unit="usd",
                        data_quality="unavailable",
                        source="polygon",
                        as_of=captured,
                        source_url=base,
                    )
                )
            note_parts.extend(missing_env_notes(env_name, source="Polygon"))
            return out, " ".join(note_parts)

        end = captured.date()
        start = end - timedelta(days=max(lookback, 2))
        errors = 0
        missing: list[str] = []
        classes: list[str] = []
        for symbol, meta in symbols.items():
            slot = str(symbol).upper()
            ticker = _polygon_ticker(meta)
            label = _polygon_label(slot, meta)
            if not ticker:
                errors += 1
                missing.append(slot)
                classes.append(ERROR_PARSE)
                out.append(
                    AssetPrint(
                        symbol=slot,
                        name=label,
                        last=None,
                        prior_close=None,
                        unit="usd",
                        data_quality="unavailable",
                        source="polygon",
                        as_of=captured,
                        source_url=base,
                    )
                )
                continue
            path = f"/v2/aggs/ticker/{ticker}/range/1/day/{start.isoformat()}/{end.isoformat()}"
            url = f"{base}{path}"
            result = http_get(
                client,
                url,
                params={"adjusted": "true", "sort": "asc", "limit": 15, "apiKey": key},
                max_attempts=self._max_attempts,
                sleep=self._sleep,
                parse_json=True,
            )
            if not result.ok:
                errors += 1
                missing.append(slot)
                classes.append(result.error_class)
                out.append(
                    AssetPrint(
                        symbol=slot,
                        name=label,
                        last=None,
                        prior_close=None,
                        unit="usd",
                        data_quality="unavailable",
                        source="polygon",
                        as_of=captured,
                        source_url=url,
                    )
                )
                continue
            payload = result.json_payload if isinstance(result.json_payload, dict) else {}
            parsed = _parse_polygon_aggs(
                payload,
                symbol=slot,
                label=label,
                ticker=ticker,
                captured=captured,
                source_url=url,
            )
            if parsed is None:
                errors += 1
                missing.append(slot)
                classes.append(ERROR_PARSE)
                out.append(
                    AssetPrint(
                        symbol=slot,
                        name=label,
                        last=None,
                        prior_close=None,
                        unit="usd",
                        data_quality="unavailable",
                        source="polygon",
                        as_of=captured,
                        source_url=url,
                    )
                )
                continue
            out.append(parsed)
        if errors:
            class_txt = ", ".join(dict.fromkeys(classes)) or "error"
            note_parts.append(
                f"polygon unavailable (error_class={class_txt}) for {errors} slot(s): "
                f"{', '.join(missing)}; ETF proxy only — not CME futures; no invent. "
                "See docs/runbooks/market-pulse.md (SRC-STOOQ-404)."
            )
        return out, "; ".join(note_parts) if note_parts else None

    def _fetch_fred(
        self, client: httpx.Client, spec: dict[str, Any], *, captured: datetime
    ) -> tuple[list[AssetPrint], str | None]:
        env_name = str(spec.get("api_key_env") or "FRED_API_KEY")
        key = self._getenv(env_name)
        if not key:
            return [], " ".join(missing_env_notes(env_name, source="FRED"))
        series = spec.get("series") or {}
        base = str(spec.get("base_url") or "https://api.stlouisfed.org/fred/series/observations")
        out: list[AssetPrint] = []
        errors = 0
        classes: list[str] = []
        for symbol, series_id in series.items():
            params = {
                "series_id": series_id,
                "api_key": key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 2,
            }
            result = http_get(
                client,
                base,
                params=params,
                max_attempts=self._max_attempts,
                sleep=self._sleep,
                parse_json=True,
            )
            if not result.ok:
                errors += 1
                classes.append(result.error_class)
                continue
            payload = result.json_payload if isinstance(result.json_payload, dict) else {}
            observations = payload.get("observations") or []
            values = [obs for obs in observations if str(obs.get("value")) not in {"", "."}]
            if not values:
                errors += 1
                classes.append(ERROR_PARSE)
                continue
            last = _maybe_float(values[0].get("value"))
            prior = _maybe_float(values[1].get("value")) if len(values) > 1 else None
            obs_date = values[0].get("date")
            quote_as_of = _date_as_utc(str(obs_date)) if obs_date else captured
            # Quality from observation age vs brief as_of_knowledge — not fetch success.
            # Per-series lag with daily default (monthly CPI/NFP override in freshness config).
            resolved = self._freshness.lag_for(
                source="fred",
                symbol=str(symbol).upper(),
                series_id=str(series_id),
            )
            max_lag = resolved[1] if resolved else DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS
            quality = "ok" if last is not None else "unavailable"
            quality = quality_from_observation_age(
                quality,
                observation_as_of=quote_as_of,
                reference_as_of=captured,
                max_calendar_lag_days=max_lag,
            )
            out.append(
                AssetPrint(
                    symbol=str(symbol).upper(),
                    name=ASSET_NAMES.get(str(symbol).upper(), str(symbol).upper()),
                    last=last,
                    prior_close=prior,
                    unit="%" if str(symbol).upper() == "US10Y" else "idx",
                    data_quality=quality,
                    source="fred",
                    as_of=quote_as_of or captured,
                    source_url=f"{base}?series_id={series_id}",
                )
            )
        note = None
        if errors:
            class_txt = ", ".join(dict.fromkeys(classes)) or "error"
            note = (
                f"fred failed for {errors} series (error_class={class_txt}); "
                "key value not printed. See docs/runbooks/market-pulse.md."
            )
        return out, note

    def _fetch_coingecko(
        self, client: httpx.Client, spec: dict[str, Any], *, captured: datetime
    ) -> tuple[list[AssetPrint], str | None]:
        ids = spec.get("ids") or {}
        if not ids:
            return [], None
        base = str(spec.get("base_url") or "https://api.coingecko.com/api/v3/simple/price")
        params = {
            "ids": ",".join(str(v) for v in ids.values()),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        }
        result = http_get(
            client,
            base,
            params=params,
            max_attempts=self._max_attempts,
            sleep=self._sleep,
            parse_json=True,
        )
        if not result.ok:
            return [], f"coingecko unavailable (error_class={result.error_class}); no prices invented"
        payload = result.json_payload if isinstance(result.json_payload, dict) else {}
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
                    data_quality="ok" if last is not None else "unavailable",
                    source="coingecko",
                    as_of=captured,
                    source_url=base,
                )
            )
        return out, None


def _parse_stooq_csv(
    text: str,
    *,
    symbol: str,
    captured: datetime | None = None,
    source_url: str | None = None,
) -> AssetPrint | None:
    reader = csv.DictReader(io.StringIO(text.strip()))
    rows = list(reader)
    if not rows:
        return None
    row = rows[0]
    last = _maybe_float(row.get("Close") or row.get("close"))
    opened = _maybe_float(row.get("Open") or row.get("open"))
    if last is None:
        return None
    quote_as_of = captured
    quality = "ok"
    date_raw = row.get("Date") or row.get("date")
    time_raw = row.get("Time") or row.get("time")
    parsed_quote = _stooq_quote_time(date_raw, time_raw)
    if parsed_quote is not None:
        quote_as_of = parsed_quote
        if captured is not None and (captured.date() - parsed_quote.date()).days > 3:
            quality = "stale"
    return AssetPrint(
        symbol=symbol,
        name=ASSET_NAMES.get(symbol, symbol),
        last=last,
        prior_close=opened,
        unit="idx" if symbol in {"DXY", "VIX"} else "pts" if symbol in {"ES", "NQ"} else "usd",
        data_quality=quality,
        source="stooq",
        open=opened,
        as_of=quote_as_of,
        source_url=source_url,
    )


def _parse_polygon_aggs(
    payload: dict[str, Any],
    *,
    symbol: str,
    label: str,
    ticker: str,
    captured: datetime,
    source_url: str | None = None,
) -> AssetPrint | None:
    results = payload.get("results") or []
    if not isinstance(results, list) or not results:
        return None
    bars: list[tuple[datetime, float, float | None]] = []
    for row in results:
        if not isinstance(row, dict):
            continue
        close = _maybe_float(row.get("c"))
        if close is None:
            continue
        ts = row.get("t")
        if ts is None:
            continue
        try:
            market_time = from_unix_ms(int(ts))
        except (TypeError, ValueError):
            continue
        opened = _maybe_float(row.get("o"))
        bars.append((market_time, close, opened))
    if not bars:
        return None
    bars.sort(key=lambda item: item[0])
    last_time, last, last_open = bars[-1]
    prior = bars[-2][1] if len(bars) >= 2 else last_open
    quality = "ok"
    if (captured.date() - last_time.date()).days > 3:
        quality = "stale"
    return AssetPrint(
        symbol=symbol,
        name=label,
        last=last,
        prior_close=prior,
        unit="usd",
        data_quality=quality,
        source="polygon",
        open=last_open,
        as_of=last_time,
        source_url=source_url,
    )


def _polygon_ticker(meta: Any) -> str:
    if isinstance(meta, dict):
        return str(meta.get("ticker") or "").upper().strip()
    return str(meta or "").upper().strip()


def _polygon_label(symbol: str, meta: Any) -> str:
    if isinstance(meta, dict):
        label = str(meta.get("label") or "").strip()
        if label:
            return label
        ticker = _polygon_ticker(meta)
        if ticker:
            return f"{ticker} ETF (proxy; not {symbol} futures)"
    return ASSET_NAMES.get(symbol, symbol)


def _polygon_structural_reason(meta: Any) -> str:
    if isinstance(meta, dict):
        reason = str(meta.get("reason") or "").strip()
        if reason:
            return " ".join(reason.split())
    return "structurally unavailable on configured Polygon plan"


def _stooq_quote_time(date_raw: Any, time_raw: Any) -> datetime | None:
    if not date_raw or str(date_raw) in {"N/D", "N/A"}:
        return None
    text = str(date_raw).strip()
    clock = str(time_raw).strip() if time_raw and str(time_raw) not in {"N/D", "N/A"} else "00:00:00"
    try:
        return parse_utc(f"{text}T{clock}Z") if "T" not in text else parse_utc(text)
    except ValueError:
        return _date_as_utc(text)


def _date_as_utc(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    try:
        return parse_utc(f"{text}T00:00:00Z")
    except ValueError:
        return None


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
