#!/usr/bin/env python3
"""QUANT-20260917 reproducible metrics for ElChopa11/market-memory active calls.

Sources (public only):
  - yfinance daily auto-adjusted Close for equities + BTC-USD/ETH-USD/AAVE-USD/SMH/SPY
  - Kraken public OHLC for UNIUSD (yfinance UNI-USD unavailable / delisted stub)
  - HL liquidity cited separately from lab JSON (not fetched by this script)

Methodology (Skeptic-readable):
  - Daily simple returns r_t = P_t / P_{t-1} - 1 after dropping NaN closes
  - Realized vol N-day annualized = sample std(ddof=1) * sqrt(252) equities / sqrt(365) crypto
  - Max drawdown ~1y: min(P/cummax(P)-1) over last 252 equity bars or 365 crypto bars
  - Relative return = name total return − benchmark total return (SPY for equities/SMH;
    BTC for ETH/UNI/AAVE). BTC absolute only.
  - Corr: Pearson on last 60 overlapping daily returns after inner-join of the 9 names
    (crypto weekend rows dropped when equities missing).

NO fabricated fills. Failures → None / unavailable in CSV.
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
        "yfinance_version": getattr(yf, "__version__", "unknown"),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "methodology": {
            "returns": "simple daily P_t/P_{t-1}-1 on auto-adjusted Close (NaNs dropped)",
            "rv_equity": "std(ddof=1)*sqrt(252)",
            "rv_crypto": "std(ddof=1)*sqrt(365)",
            "corr_window": "last 60 overlapping dates with all 9 names non-null",
            "mdd": "min peak-to-trough over lookback bars",
            "rel_returns": "name total return minus benchmark total return",
            "UNI_source": "Kraken public OHLC UNIUSD interval=1440",
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

        row["source"] = meta["tickers"][name]["source"]
        row["last_close"] = float(p.iloc[-1])
        row["asof"] = str(p.index.max().date())
        row["rv_20d"] = realized_vol(r, 20, name)
        row["rv_60d"] = realized_vol(r, 60, name)
        row["mdd_1y"] = max_drawdown(p, lookback)
        row["ret_1m"] = total_return(p, d1)
        row["ret_3m"] = total_return(p, d3)
        row["ret_ytd"] = ytd_return(p, 2026)
        row["bench"] = bench_name
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

    panel_names = [n for n in CORR_NAMES + ["SPY"] if n in prices]
    panel = pd.DataFrame({n: prices[n] for n in panel_names})
    rets = panel.pct_change()
    corr_rets = rets[CORR_NAMES].dropna(how="any")
    window = 60
    if len(corr_rets) >= window:
        corr_slice = corr_rets.iloc[-window:]
        corr = corr_slice.corr()
        corr.to_csv(OUT / "corr_matrix_60d.csv")
        corr_slice.to_csv(OUT / "daily_returns_60d_corr_window.csv")
        meta["corr"] = {
            "window_bars": window,
            "start": str(corr_slice.index.min().date()),
            "end": str(corr_slice.index.max().date()),
            "n_obs": int(len(corr_slice)),
            "alignment": "inner-join dates with non-null returns for all 9",
        }
    else:
        meta["corr"] = {"status": "unavailable", "n_obs": int(len(corr_rets))}
        meta["errors"].append({"name": "corr", "error": f"only {len(corr_rets)} bars"})

    rets.dropna(how="all").to_csv(OUT / "daily_returns_full_panel.csv")
    pd.DataFrame([
        {
            "name": row["name"],
            "rv_20d_ann": row["rv_20d"],
            "rv_60d_ann": row["rv_60d"],
            "ann_factor": ann_factor(row["name"]),
            "mdd_1y": row["mdd_1y"],
        }
        for row in rows
    ]).to_csv(OUT / "vol_mdd_summary.csv", index=False)

    with open(OUT / "run_meta.json", "w") as f:
        json.dump(meta, f, indent=2, default=str)

    print(json.dumps({"corr": meta.get("corr"), "errors": meta["errors"]}, indent=2))
    # print metrics nicely
    print(metrics.to_string(float_format=lambda x: f"{x:.4f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
