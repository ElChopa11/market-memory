#!/usr/bin/env python3
"""QUANT-20260917 reproducible metrics for ElChopa11/market-memory in-universe membership names.

Sources (public only):
  - yfinance daily auto-adjusted Close for equities + BTC-USD/ETH-USD/AAVE-USD/SMH/SPY
  - Kraken public OHLC for UNIUSD (yfinance UNI-USD unavailable / delisted stub)
  - HL liquidity is NOT fetched. Stale lab snapshot belongs in the markdown appendix
    only (DO NOT SIZE). Equity ADV CSV is also not produced here.

Methodology (Skeptic-readable):
  - Daily simple returns r_t = P_t / P_{t-1} - 1 on each name's *native* series
    (NaN closes dropped). RV/MDD/trailing returns use native pct_change, not the
    aligned corr panel.
  - Realized vol = sample std(ddof=1) * sqrt(252) equities / sqrt(365) crypto
    over last 20 / 60 native return bars. NOT cross-asset comparable.
  - Max drawdown: min(P/cummax(P)-1) over last 252 equity / 365 crypto price bars.
  - Trailing returns are BAR COUNTS, not calendar months: 21/63 equities, 30/90 crypto.
  - Relative return = name total return minus benchmark total return (SPY for
    equities/SMH; BTC for ETH/UNI/AAVE). BTC absolute only.
    THIS IS NOT ALPHA (not residual, not beta-adjusted).
  - YTD = first native bar with date >= 2026-01-01 through asof; post-selection
    descriptive only.
  - Windows are arbitrary dashboard defaults — not a registered research design.
  - Corr: Pearson on last 60 complete rows of an *aligned-panel* pct_change after
    dropna(how="any") across 9 names. Crypto weekends drop when equities are
    absent; a hole in any name (META NaN) truncates everyone's corr window.
    Title as pre-FOMC if end < FOMC date. Point estimate only.

NO fabricated fills. Failures → None / unavailable in CSV.
A later run overwrites CSVs and is NOT the 2026-09-17 pack of record.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yfinance as yf

OUT = Path(__file__).resolve().parent
AEST = ZoneInfo("Australia/Sydney")
RUN_TS = datetime.now(tz=AEST)

ACTIVE_YF = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "NVDA": "NVDA",
    "AVGO": "AVGO",
    "MSFT": "MSFT",
    "META": "META",
    "JPM": "JPM",
    "XLF": "XLF",
    "XOM": "XOM",
}
WATCH_YF = {"AAVE": "AAVE-USD", "SMH": "SMH"}  # UNI via Kraken
BENCH = {"SPY": "SPY"}
CRYPTO = {"BTC", "ETH", "UNI", "AAVE"}
CORR_NAMES = ["BTC", "ETH", "NVDA", "AVGO", "MSFT", "META", "JPM", "XLF", "XOM"]


def fetch_yf_close(ticker: str, period: str = "2y") -> pd.Series:
    hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
    if hist is None or hist.empty:
        raise RuntimeError(f"empty history for {ticker}")
    s = hist["Close"].dropna().copy()
    if s.empty:
        raise RuntimeError(f"all-NaN Close for {ticker}")
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    # de-duplicate index if any
    s = s[~s.index.duplicated(keep="last")]
    s.name = ticker
    return s


def fetch_kraken_uni() -> pd.Series:
    url = "https://api.kraken.com/0/public/OHLC?pair=UNIUSD&interval=1440"
    req = urllib.request.Request(url, headers={"User-Agent": "mm-quant/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    if d.get("error"):
        raise RuntimeError(f"kraken error: {d['error']}")
    key = [k for k in d["result"].keys() if k != "last"][0]
    rows = d["result"][key]
    df = pd.DataFrame(
        rows, columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
    )
    s = pd.Series(
        df["close"].astype(float).values,
        index=pd.to_datetime(df["time"], unit="s").dt.normalize(),
        name="UNIUSD",
    )
    s = s[~s.index.duplicated(keep="last")]
    return s


def ann_factor(name: str) -> float:
    return 365.0 if name in CRYPTO else 252.0


def realized_vol(rets: pd.Series, window: int, name: str) -> float | None:
    x = rets.dropna()
    if len(x) < window:
        return None
    x = x.iloc[-window:]
    return float(x.std(ddof=1) * np.sqrt(ann_factor(name)))


def native_bar_span(index: pd.Index) -> tuple[str | None, str | None]:
    if index is None or len(index) == 0:
        return None, None
    return str(pd.Timestamp(index.min()).date()), str(pd.Timestamp(index.max()).date())


def return_window_span(rets: pd.Series, window: int) -> tuple[str | None, str | None]:
    x = rets.dropna()
    if len(x) < window:
        return None, None
    return native_bar_span(x.iloc[-window:].index)


def price_step_span(prices: pd.Series, steps: int) -> tuple[str | None, str | None]:
    """Start/end dates of last `steps` price increments (steps+1 prices)."""
    p = prices.dropna()
    if len(p) < 5:
        return None, None
    steps = min(steps, len(p) - 1)
    sl = p.iloc[-(steps + 1) :]
    return native_bar_span(sl.index)


def lookback_price_span(prices: pd.Series, lookback: int) -> tuple[str | None, str | None]:
    p = prices.dropna()
    if len(p) < 20:
        return None, None
    sl = p.iloc[-lookback:]
    return native_bar_span(sl.index)


def ytd_price_span(prices: pd.Series, year: int = 2026) -> tuple[str | None, str | None]:
    p = prices.dropna()
    after = p[p.index >= pd.Timestamp(f"{year}-01-01")]
    if after.empty:
        return None, None
    return native_bar_span(after.index)


def max_drawdown(prices: pd.Series, lookback: int) -> float | None:
    p = prices.dropna()
    if len(p) < 20:
        return None
    p = p.iloc[-lookback:]
    dd = p / p.cummax() - 1.0
    return float(dd.min())


def total_return(prices: pd.Series, days: int) -> float | None:
    p = prices.dropna()
    if len(p) < 5:
        return None
    days = min(days, len(p) - 1)
    a, b = p.iloc[-(days + 1)], p.iloc[-1]
    if a == 0 or pd.isna(a) or pd.isna(b):
        return None
    return float(b / a - 1.0)


def ytd_return(prices: pd.Series, year: int = 2026) -> float | None:
    p = prices.dropna()
    if p.empty:
        return None
    after = p[p.index >= pd.Timestamp(f"{year}-01-01")]
    if after.empty:
        return None
    return float(after.iloc[-1] / after.iloc[0] - 1.0)


def main() -> int:
    meta = {
        "run_ts_aest": RUN_TS.isoformat(),
        "run_ts_utc": datetime.now(timezone.utc).isoformat(),
        "as_of_knowledge": RUN_TS.isoformat(),
        "yfinance_version": getattr(yf, "__version__", "unknown"),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "methodology": {
            "as_of_knowledge": RUN_TS.isoformat(),
            "window_policy": "arbitrary dashboard defaults (20/60/21/63/30/90/252/365) — not a registered research design",
            "returns": "simple daily P_t/P_{t-1}-1 on auto-adjusted Close (NaNs dropped) on each name's native series",
            "rv_equity": "std(ddof=1)*sqrt(252) — NOT comparable to rv_crypto",
            "rv_crypto": "std(ddof=1)*sqrt(365) — NOT comparable to rv_equity",
            "corr_window": "last 60 overlapping dates with all 9 names non-null on ALIGNED-PANEL pct_change (not native-series RV)",
            "corr_title": "pre-FOMC 60d dependence if corr.end < FOMC date",
            "mdd": "min peak-to-trough over lookback bars (252 equity / 365 crypto)",
            "rel_returns": "simple difference name total return minus benchmark total return — NOT alpha, NOT beta-adjusted",
            "ret_bars": "equities 21/63 price steps; crypto 30/90 price steps; do not label as calendar months",
            "ytd": "first native bar with date >= 2026-01-01 through asof; post-selection descriptive only",
            "UNI_source": "Kraken public OHLC UNIUSD interval=1440",
            "hl": "NOT fetched by this script; stale lab snapshot is appendix-only",
        },
        "tickers": {},
        "errors": [],
    }

    prices: dict[str, pd.Series] = {}
    all_yf = {**ACTIVE_YF, **WATCH_YF, **BENCH}
    for name, yf_sym in all_yf.items():
        try:
            s = fetch_yf_close(yf_sym)
            prices[name] = s
            meta["tickers"][name] = {
                "source": f"yfinance:{yf_sym}",
                "n_bars": int(len(s)),
                "start": str(s.index.min().date()),
                "end": str(s.index.max().date()),
                "last_close": float(s.iloc[-1]),
            }
            print(f"OK {name} yf:{yf_sym} n={len(s)} last={s.iloc[-1]:.4f} end={s.index.max().date()}")
        except Exception as e:
            meta["errors"].append({"name": name, "error": str(e)})
            print(f"FAIL {name}: {e}", file=sys.stderr)

    try:
        s = fetch_kraken_uni()
        prices["UNI"] = s
        meta["tickers"]["UNI"] = {
            "source": "kraken:UNIUSD",
            "n_bars": int(len(s)),
            "start": str(s.index.min().date()),
            "end": str(s.index.max().date()),
            "last_close": float(s.iloc[-1]),
        }
        print(f"OK UNI kraken n={len(s)} last={s.iloc[-1]:.4f} end={s.index.max().date()}")
    except Exception as e:
        meta["errors"].append({"name": "UNI", "error": str(e)})
        print(f"FAIL UNI: {e}", file=sys.stderr)

    names_order = list(ACTIVE_YF) + ["UNI", "AAVE", "SMH"]
    rows = []
    for name in names_order:
        row: dict = {"name": name}
        if name not in prices:
            row.update({
                "source": None, "last_close": None, "asof": None,
                "rv_20d": None, "rv_60d": None, "mdd_1y": None,
                "ret_1m": None, "ret_3m": None, "ret_ytd": None,
                "rel_1m": None, "rel_3m": None, "rel_ytd": None,
                "bench": None, "status": "unavailable: download failed",
                "ann_factor": ann_factor(name),
                "ret_short_bars": None, "ret_long_bars": None,
                "mdd_lookback_bars": None,
                "rel_method": "simple_diff_NOT_alpha",
                "asof_note": None,
                "rv_20d_start": None, "rv_20d_end": None,
                "rv_60d_start": None, "rv_60d_end": None,
                "mdd_start": None, "mdd_end": None,
                "ret_short_start": None, "ret_short_end": None,
                "ret_long_start": None, "ret_long_end": None,
                "ytd_start": None, "ytd_end": None,
            })
            rows.append(row)
            continue
        p = prices[name]
        r = p.pct_change().dropna()
        lookback = 365 if name in CRYPTO else 252
        d1, d3 = (30, 90) if name in CRYPTO else (21, 63)
        if name == "BTC":
            bench_name = None
        elif name in ("ETH", "UNI", "AAVE"):
            bench_name = "BTC"
        else:
            bench_name = "SPY"

        asof = str(p.index.max().date())
        asof_note = None
        if name == "META":
            asof_note = "LAG_vs_equity_peers"
        elif name == "UNI":
            asof_note = "shorter_kraken_history_starts_2024-09-27"

        row["source"] = meta["tickers"][name]["source"]
        row["last_close"] = float(p.iloc[-1])
        row["asof"] = asof
        row["rv_20d"] = realized_vol(r, 20, name)
        row["rv_60d"] = realized_vol(r, 60, name)
        row["mdd_1y"] = max_drawdown(p, lookback)
        row["ret_1m"] = total_return(p, d1)
        row["ret_3m"] = total_return(p, d3)
        row["ret_ytd"] = ytd_return(p, 2026)
        row["bench"] = bench_name
        row["ann_factor"] = ann_factor(name)
        row["ret_short_bars"] = d1
        row["ret_long_bars"] = d3
        row["mdd_lookback_bars"] = lookback
        row["rel_method"] = "absolute_not_alpha" if bench_name is None else "simple_diff_NOT_alpha"
        row["asof_note"] = asof_note
        row["rv_20d_start"], row["rv_20d_end"] = return_window_span(r, 20)
        row["rv_60d_start"], row["rv_60d_end"] = return_window_span(r, 60)
        row["mdd_start"], row["mdd_end"] = lookback_price_span(p, lookback)
        row["ret_short_start"], row["ret_short_end"] = price_step_span(p, d1)
        row["ret_long_start"], row["ret_long_end"] = price_step_span(p, d3)
        row["ytd_start"], row["ytd_end"] = ytd_price_span(p, 2026)
        if bench_name and bench_name in prices:
            bp = prices[bench_name]

            def rel(days: int | None = None, ytd: bool = False):
                if ytd:
                    a, b = ytd_return(p, 2026), ytd_return(bp, 2026)
                else:
                    a, b = total_return(p, days), total_return(bp, days)
                if a is None or b is None:
                    return None
                return float(a - b)

            row["rel_1m"] = rel(d1)
            row["rel_3m"] = rel(d3)
            row["rel_ytd"] = rel(ytd=True)
        else:
            row["rel_1m"] = row["rel_3m"] = row["rel_ytd"] = None
        row["status"] = "ok"
        rows.append(row)

    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "metrics_active_and_watch.csv", index=False)

    window_rows = []
    for row in rows:
        name = row["name"]
        for metric, nkey, skey, ekey, unit in (
            ("RV20", "unused", "rv_20d_start", "rv_20d_end", "native_return_bars"),
            ("RV60", "unused", "rv_60d_start", "rv_60d_end", "native_return_bars"),
            ("MDD", "mdd_lookback_bars", "mdd_start", "mdd_end", "native_price_bars"),
            ("ret_short", "ret_short_bars", "ret_short_start", "ret_short_end", "native_price_steps"),
            ("ret_long", "ret_long_bars", "ret_long_start", "ret_long_end", "native_price_steps"),
            ("YTD", "unused", "ytd_start", "ytd_end", "first_native_bar_ge_year_start_to_asof"),
        ):
            n_val = { "RV20": 20, "RV60": 60, "YTD": None }.get(metric, row.get(nkey))
            window_rows.append({
                "name": name,
                "metric": metric,
                "n": n_val,
                "unit": unit,
                "end": row.get(ekey),
                "start": row.get(skey),
                "ann_factor": row.get("ann_factor"),
                "rel_method": row.get("rel_method"),
                "asof_note": row.get("asof_note"),
            })
    pd.DataFrame(window_rows).to_csv(OUT / "metric_windows.csv", index=False)

    panel_names = [n for n in CORR_NAMES + ["SPY"] if n in prices]
    panel = pd.DataFrame({n: prices[n] for n in panel_names})
    rets = panel.pct_change()
    corr_rets = rets[CORR_NAMES].dropna(how="any")
    window = 60
    btc_weekends = 0
    if "BTC" in rets.columns:
        btc_r = rets["BTC"].dropna()
        btc_weekends = int((btc_r.index.dayofweek >= 5).sum())
    if len(corr_rets) >= window:
        corr_slice = corr_rets.iloc[-window:]
        corr = corr_slice.corr()
        corr.to_csv(OUT / "corr_matrix_60d.csv")
        corr_slice.to_csv(OUT / "daily_returns_60d_corr_window.csv")
        meta_end = None
        if "META" in prices:
            meta_end = str(prices["META"].index.max().date())
        nvda_end = str(prices["NVDA"].index.max().date()) if "NVDA" in prices else None
        fomc = "2026-09-16"
        corr_end = str(corr_slice.index.max().date())
        meta["corr"] = {
            "window_bars": window,
            "start": str(corr_slice.index.min().date()),
            "end": corr_end,
            "n_obs": int(len(corr_slice)),
            "alignment": "inner-join dates with non-null returns for all 9 on aligned-panel pct_change",
            "title": "pre-FOMC 60d dependence (ends {})".format(corr_end),
            "fomc_date": fomc,
            "pre_fomc": corr_end < fomc,
            "meta_asof": meta_end,
            "nvda_asof": nvda_end,
            "meta_truncation": meta_end is not None and nvda_end is not None and meta_end < nvda_end,
            "inner_join_complete_rows": int(len(corr_rets)),
            "inner_join_span": "{} → {}".format(
                corr_rets.index.min().date(), corr_rets.index.max().date()
            ),
            "btc_weekend_return_bars_in_panel": btc_weekends,
            "point_estimate_only": True,
            "no_hedge_ratio": True,
            "not_native_series_rv": True,
        }
    else:
        meta["corr"] = {"status": "unavailable", "n_obs": int(len(corr_rets))}
        meta["errors"].append({"name": "corr", "error": f"only {len(corr_rets)} bars"})

    rets.dropna(how="all").to_csv(OUT / "daily_returns_full_panel.csv")
    pd.DataFrame([
        {
            "name": row["name"],
            "asset_class": "crypto" if row["name"] in CRYPTO else "equity",
            "rv_20d_ann": row["rv_20d"],
            "rv_60d_ann": row["rv_60d"],
            "ann_factor": ann_factor(row["name"]),
            "mdd_1y": row["mdd_1y"],
            "cross_asset_rv_comparable": False,
        }
        for row in rows
    ]).to_csv(OUT / "vol_mdd_summary.csv", index=False)

    if "META" in meta["tickers"]:
        peer_end = meta["tickers"].get("NVDA", {}).get("end")
        meta_end = meta["tickers"]["META"].get("end")
        if peer_end and meta_end and meta_end < peer_end:
            meta["tickers"]["META"]["asof_flag"] = (
                f"LAG_vs_equity_peers — series end {meta_end} vs NVDA {peer_end}; "
                "truncates 9-name corr"
            )
    if "UNI" in meta["tickers"]:
        meta["tickers"]["UNI"]["sample_note"] = (
            "shorter than yfinance crypto peers; do not compare MDD/YTD without alignment"
        )

    with open(OUT / "run_meta.json", "w") as f:
        json.dump(meta, f, indent=2, default=str)

    print(json.dumps({"corr": meta.get("corr"), "errors": meta["errors"]}, indent=2))
    # print metrics nicely
    print(metrics.to_string(float_format=lambda x: f"{x:.4f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
