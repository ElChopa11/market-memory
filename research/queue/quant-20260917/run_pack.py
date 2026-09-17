#!/usr/bin/env python3
"""Fetch public data and write the QUANT-20260917 active-calls pack.

Usage (from repo root):

    python3 research/queue/quant-20260917/run_pack.py

No trading credentials. Hyperliquid public /info + Yahoo Finance chart only.
Does not invent numbers: failed fetches are logged and table cells stay blank/n/a.
"""

from __future__ import annotations

import csv
import json
import math
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PACK_DIR = Path(__file__).resolve().parent
QUEUE_DIR = PACK_DIR.parent
if str(PACK_DIR) not in sys.path:
    sys.path.insert(0, str(PACK_DIR))

import fetch as fetch_mod  # noqa: E402
import metrics as m  # noqa: E402

PACK_ID = "QUANT-20260917-active-calls"
CRYPTO = ("BTC", "ETH")
EQUITIES = ("NVDA", "AVGO", "MSFT", "META", "JPM", "XLF", "XOM")
NAMES = CRYPTO + EQUITIES
SPY = "SPY"
BENCH = SPY

WATCH_ONLY_EXCLUDED = ("UNI", "AAVE", "SMH")
MUST_CUTS_NOT_REOPENED = ("HYPE", "SOL", "XRP", "ARB", "NEAR", "LINK", "GLD", "LLY")
EQUITY_CLASS = {
    "NVDA": "us_equity",
    "AVGO": "us_equity",
    "MSFT": "us_equity",
    "META": "us_equity",
    "JPM": "us_equity",
    "XLF": "us_etf",
    "XOM": "us_equity",
    "SPY": "us_etf",
}

EQUITY_LOOKBACK_DAYS = 800  # calendar buffer so ~2y of sessions are available
CRYPTO_LOOKBACK_DAYS = 400
FUNDING_LOOKBACK_HOURS = 72


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(ts: datetime | None = None) -> str:
    return fetch_mod.iso(ts)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    names = fieldnames or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_cell(row.get(key)) for key in names})


def _csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return repr(value) if abs(value) < 1e-4 and value != 0.0 else f"{value:.10g}"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def fmt_pct(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.{digits}f}%"


def fmt_num(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.{digits}f}"


def fmt_corr(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


def prices_from_rows(rows: list[dict[str, Any]]) -> tuple[list[str], list[float]]:
    dates = [str(row["date"]) for row in rows]
    prices = [float(row["close"]) for row in rows]
    return dates, prices


def native_metrics(ticker: str, rows: list[dict[str, Any]], *, crypto: bool) -> dict[str, Any]:
    dates, prices = prices_from_rows(rows)
    ann = m.CRYPTO_ANN_FACTOR if crypto else m.EQUITY_ANN_FACTOR
    one_m = m.CRYPTO_1M_BARS if crypto else m.EQUITY_1M_BARS
    three_m = m.CRYPTO_3M_BARS if crypto else m.EQUITY_3M_BARS
    one_y = m.CRYPTO_1Y_BARS if crypto else m.EQUITY_1Y_BARS
    window_px = m.trailing(prices, one_y)
    window_dt = dates[-len(window_px) :] if window_px else []
    rets = m.log_returns(prices) if len(prices) >= 2 else []
    last = prices[-1] if prices else None
    prev = prices[-2] if len(prices) >= 2 else None
    day_ret = (last / prev - 1.0) if last is not None and prev else None
    out: dict[str, Any] = {
        "ticker": ticker,
        "asset_class": "hl_perp" if crypto else EQUITY_CLASS.get(ticker, "us_equity"),
        "source": rows[-1]["source"] if rows else "",
        "n_bars": len(prices),
        "first_date": dates[0] if dates else "",
        "last_date": dates[-1] if dates else "",
        "last_close": last,
        "day_return": day_ret,
        "ann_factor": ann,
        "ret_1m": m.total_return(prices, one_m),
        "ret_1m_bars": one_m,
        "ret_3m": m.total_return(prices, three_m),
        "ret_3m_bars": three_m,
        "rv_20d": m.realized_vol(rets, 20, ann),
        "rv_60d": m.realized_vol(rets, 60, ann),
        "max_dd_1y": m.max_drawdown(window_px) if window_px else None,
        "max_dd_window_bars": len(window_px),
        "max_dd_window_start": window_dt[0] if window_dt else "",
        "max_dd_window_end": window_dt[-1] if window_dt else "",
        "status": "ok" if prices else "missing",
    }
    return out


def align_on_dates(
    series: dict[str, list[dict[str, Any]]], required: tuple[str, ...]
) -> tuple[list[str], dict[str, list[float]]]:
    by_ticker: dict[str, dict[str, float]] = {}
    for ticker, rows in series.items():
        by_ticker[ticker] = {str(row["date"]): float(row["close"]) for row in rows}
    if not required:
        return [], {name: [] for name in series}
    common: set[str] | None = None
    for ticker in required:
        dates = set(by_ticker.get(ticker, {}))
        common = dates if common is None else common & dates
    ordered = sorted(common or [])
    aligned = {
        ticker: [by_ticker[ticker][day] for day in ordered]
        for ticker in required
        if ticker in by_ticker
    }
    return ordered, aligned


def beta_corr_vs_spy(
    equity_aligned: dict[str, list[float]], spy: list[float], dates: list[str]
) -> list[dict[str, Any]]:
    spy_rets = m.log_returns(spy)
    rows: list[dict[str, Any]] = []
    for ticker in EQUITIES:
        prices = equity_aligned.get(ticker) or []
        rets = m.log_returns(prices)
        n = min(len(rets), len(spy_rets))
        if n < 3:
            rows.append(
                {
                    "ticker": ticker,
                    "benchmark": BENCH,
                    "n_return_pairs": n,
                    "window_start": dates[0] if dates else "",
                    "window_end": dates[-1] if dates else "",
                    "beta": None,
                    "alpha_daily": None,
                    "corr": None,
                    "status": "insufficient_overlap",
                }
            )
            continue
        y = rets[-n:]
        x = spy_rets[-n:]
        alpha, beta = m.ols_alpha_beta(y, x)
        corr = m.pearson(y, x)
        rows.append(
            {
                "ticker": ticker,
                "benchmark": BENCH,
                "n_return_pairs": n,
                "window_start": dates[1] if len(dates) > 1 else (dates[0] if dates else ""),
                "window_end": dates[-1] if dates else "",
                "beta": beta,
                "alpha_daily": alpha,
                "corr": corr,
                "status": "ok",
            }
        )
    return rows


def cross_corr_matrix(
    aligned: dict[str, list[float]],
    names: tuple[str, ...],
    *,
    window: int | None = None,
) -> tuple[list[str], dict[str, dict[str, float | None]], int]:
    rets = {name: m.log_returns(aligned[name]) for name in names if name in aligned}
    n = min((len(values) for values in rets.values()), default=0)
    if window is not None:
        n = min(n, window)
    matrix: dict[str, dict[str, float | None]] = {a: {} for a in names}
    for a in names:
        for b in names:
            if a not in rets or b not in rets:
                matrix[a][b] = None
            elif a == b:
                matrix[a][b] = 1.0
            elif n < 3:
                matrix[a][b] = None
            else:
                matrix[a][b] = m.pearson(rets[a][-n:], rets[b][-n:])
    return list(names), matrix, n


def last_dates(series: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for ticker, rows in series.items():
        if rows:
            out[ticker] = str(rows[-1]["date"])
    return out


def describe_gaps(
    *,
    fetch_day: str,
    last: dict[str, str],
    nine_dates: list[str],
    eq_spy_dates: list[str],
) -> list[str]:
    lines: list[str] = []
    equity_last = {ticker: last.get(ticker) for ticker in EQUITIES if last.get(ticker)}
    if equity_last:
        latest = max(equity_last.values())
        lagging = sorted(ticker for ticker, day in equity_last.items() if day != latest)
        if lagging:
            detail = ", ".join(f"{ticker} ends {equity_last[ticker]}" for ticker in lagging)
            lines.append(
                f"Yahoo session lag vs peers ({latest}): {detail}. "
                "9-name inner join stops at the earliest of those last dates."
            )
    for coin in CRYPTO:
        day = last.get(coin)
        if day == fetch_day:
            lines.append(
                f"HL {coin} 1d candle for {day} is the **in-progress** UTC day (open, not a finished daily bar)."
            )
        elif day:
            lines.append(f"HL {coin} last daily close date: {day}.")
    if nine_dates:
        lines.append(
            f"9-name heatmap calendar: {nine_dates[0]} → {nine_dates[-1]} ({len(nine_dates)} session dates). "
            "Limited by HL lookback and any equity session gaps (weekends/holidays dropped)."
        )
    if eq_spy_dates:
        lines.append(
            f"Equity–SPY beta calendar: {eq_spy_dates[0]} → {eq_spy_dates[-1]} ({len(eq_spy_dates)} session dates). "
            "Does **not** require BTC/ETH dates (uses full Yahoo overlap)."
        )
    if not lines:
        lines.append("No extra gaps beyond fetch failures listed above.")
    return lines


def funding_stats(history: list[dict[str, Any]], snapshot_rate: float | None) -> dict[str, Any]:
    rates = [float(row["funding_rate"]) for row in history]
    last = history[-1] if history else None
    mean_72h = (sum(rates) / len(rates)) if rates else None
    return {
        "funding_snapshot": snapshot_rate,
        "funding_last_history": last["funding_rate"] if last else None,
        "funding_last_history_time_utc": last["time_utc"] if last else "",
        "funding_history_n_72h": len(rates),
        "funding_mean_72h": mean_72h,
        "funding_ann_naive_snapshot": m.naive_funding_annualized(snapshot_rate) if snapshot_rate is not None else None,
        "oi_history_public": False,
        "oi_history_note": "Hyperliquid public /info has no OI history; OI is snapshot-only (metaAndAssetCtxs).",
    }


def render_heatmap(names: tuple[str, ...], matrix: dict[str, dict[str, float | None]]) -> str:
    header = "| | " + " | ".join(names) + " |"
    sep = "|---|" + "|".join("---:" for _ in names) + "|"
    lines = [header, sep]
    for a in names:
        cells = [fmt_corr(matrix.get(a, {}).get(b)) for b in names]
        lines.append("| " + a + " | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_markdown(ctx: dict[str, Any]) -> str:
    fetch_log: fetch_mod.FetchLog = ctx["fetch_log"]
    native_rows: list[dict[str, Any]] = ctx["native_rows"]
    beta_rows: list[dict[str, Any]] = ctx["beta_rows"]
    names: tuple[str, ...] = ctx["names"]
    matrix: dict[str, dict[str, float | None]] = ctx["matrix"]
    corr_n: int = ctx["corr_n"]
    matrix_60: dict[str, dict[str, float | None]] = ctx["matrix_60"]
    corr_n_60: int = ctx["corr_n_60"]
    nine_dates: list[str] = ctx["nine_dates"]
    window_60: tuple[str, str] = ctx["window_60"]
    eq_spy_dates: list[str] = ctx["eq_spy_dates"]
    gap_lines: list[str] = ctx["gap_lines"]
    hl_rows: list[dict[str, Any]] = ctx["hl_rows"]
    failures = fetch_log.failures()
    native_by = {row["ticker"]: row for row in native_rows}
    beta_by = {row["ticker"]: row for row in beta_rows}

    failure_lines = []
    for row in failures:
        failure_lines.append(
            f"- `{row.started_at}` {row.source} `{row.action}` status={row.status} attempt={row.attempt}: {row.error}"
        )
    if not failure_lines:
        failure_lines = ["- None recorded in this run."]

    native_table = [
        "| Ticker | Class | Last close | Last date | 20d RV | 60d RV | ~1y max DD | 1m return | 3m return | n bars |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for ticker in NAMES:
        row = native_by.get(ticker) or {"status": "missing"}
        native_table.append(
            "| {ticker} | {klass} | {last} | {last_d} | {rv20} | {rv60} | {dd} | {r1} | {r3} | {n} |".format(
                ticker=ticker,
                klass=row.get("asset_class") or "n/a",
                last=fmt_num(row.get("last_close"), 2) if row.get("last_close") is not None else "n/a",
                last_d=row.get("last_date") or "n/a",
                rv20=fmt_pct(row.get("rv_20d")),
                rv60=fmt_pct(row.get("rv_60d")),
                dd=fmt_pct(row.get("max_dd_1y")),
                r1=fmt_pct(row.get("ret_1m")),
                r3=fmt_pct(row.get("ret_3m")),
                n=row.get("n_bars") if row.get("n_bars") is not None else "n/a",
            )
        )

    beta_table = [
        "| Ticker | vs | n pairs | window | beta | corr |",
        "|---|---|---:|---|---:|---:|",
    ]
    for ticker in EQUITIES:
        row = beta_by.get(ticker) or {}
        window = ""
        if row.get("window_start") and row.get("window_end"):
            window = f"{row['window_start']} → {row['window_end']}"
        beta_table.append(
            "| {ticker} | {bench} | {n} | {window} | {beta} | {corr} |".format(
                ticker=ticker,
                bench=row.get("benchmark") or BENCH,
                n=row.get("n_return_pairs") if row.get("n_return_pairs") is not None else "n/a",
                window=window or "n/a",
                beta=fmt_num(row.get("beta"), 2),
                corr=fmt_corr(row.get("corr")),
            )
        )

    hl_table = [
        "| Coin | mid | mark | oracle | funding 8h | naive ann. | OI (coin) | OI notional (mark×OI) | day ntl vol | 72h funding n | 72h mean 8h |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in hl_rows:
        hl_table.append(
            "| {coin} | {mid} | {mark} | {oracle} | {fund} | {ann} | {oi} | {ntl} | {day} | {n} | {mean} |".format(
                coin=row.get("coin"),
                mid=fmt_num(row.get("mid_px"), 2),
                mark=fmt_num(row.get("mark_px"), 2),
                oracle=fmt_num(row.get("oracle_px"), 2),
                fund=fmt_num(row.get("funding"), 8) if row.get("funding") is not None else "n/a",
                ann=fmt_pct(row.get("funding_ann_naive_snapshot"), 1),
                oi=fmt_num(row.get("open_interest"), 2),
                ntl=fmt_num(row.get("oi_notional"), 0),
                day=fmt_num(row.get("day_ntl_vlm"), 0),
                n=row.get("funding_history_n_72h") if row.get("funding_history_n_72h") is not None else "n/a",
                mean=fmt_num(row.get("funding_mean_72h"), 8) if row.get("funding_mean_72h") is not None else "n/a",
            )
        )

    nine_span = "n/a"
    if nine_dates:
        nine_span = f"{nine_dates[0]} → {nine_dates[-1]} ({len(nine_dates)} session dates)"
    eq_spy_span = "n/a"
    if eq_spy_dates:
        eq_spy_span = f"{eq_spy_dates[0]} → {eq_spy_dates[-1]} ({len(eq_spy_dates)} session dates)"

    return f"""# QUANT-20260917 — Active-call pack

| Field | Value |
|---|---|
| **Purpose** | Principal ask — public-data QUANT pack on **active_calls only** so Research can cite measured vol / DD / returns / beta / corr / HL funding+OI. |
| **As-of (fetch start)** | `{fetch_log.started_at}` |
| **As-of (fetch end)** | `{fetch_log.finished_at}` |
| **Timezone** | UTC timestamps on every fetch attempt. Equity session dates from Yahoo unix timestamps converted via UTC date (US cash session timestamps fall on the NY session date). HL daily candles keyed by candle **open** UTC date. |
| **Scope** | `config/universe.yaml` `active_calls` after PR #15: HL **BTC, ETH**; equities **NVDA, AVGO, MSFT, META, JPM, XLF, XOM**. |
| **Excluded** | Watch-only (still universe membership, **not** this pack): {", ".join(WATCH_ONLY_EXCLUDED)}. Must-cuts **not reopened**: {", ".join(MUST_CUTS_NOT_REOPENED)}. |
| **Status** | Snapshot pack / citation tables. **Not** a thesis, **not** orders, **not** risk approval, **not** Market Memory observations (no `obs_id`s). |
| **Sources** | Equities + SPY: Yahoo Finance v8 chart (public; same series yfinance uses). BTC/ETH: Hyperliquid public `/info` (`allMids`, `metaAndAssetCtxs`, `candleSnapshot` 1d, `fundingHistory`). |
| **Scripts / CSVs** | [`research/queue/quant-20260917/`](quant-20260917/) |
| **Coordinate with** | Call cards PR #13 (`research/queue/UNIVERSE-20260917-call-cards.md`); Skeptic PR #14; universe tiers PR #15. RQ-20260917-A (PR #9) remains a **separate** BTC funding/basis workstream. **Path overlap:** Research PR #19 wrote the same `QUANT-20260917-active-calls.md` + `quant-20260917/` prefix — see below. |

**Honesty bar:** numbers below come from this run's CSVs. Empty / `n/a` means insufficient history or a documented fetch failure — **not** a guessed fill. HTTP 429s are counted in the fetch log.

---

## Overlap with Research PR #19

Research already opened [PR #19](https://github.com/ElChopa11/market-memory/pull/19) (`research: QUANT-20260917 active-calls pack`) at the **same citation paths**. Do not merge both blindly.

| | This pack | Research PR #19 |
|---|---|---|
| Paths | `research/queue/QUANT-20260917-active-calls.md` + `quant-20260917/` | same |
| Universe | **active_calls only** (no UNI/AAVE/SMH tables) | active center + watch-only appendix |
| BTC/ETH prices | HL public `candleSnapshot` 1d | yfinance `BTC-USD` / `ETH-USD` |
| HL funding / OI | Live `/info` this run (see fetch log) | Lab cache `2026-09-17T00:28:03Z`, labeled **stale/partial** after HTTP **429**; `fundingHistory` unavailable |
| 9-name corr | Full session inner-join (**n** below) **and** trailing 60d (`corr_matrix_60d.csv`, same filename as #19) | Trailing **60** overlapping days only |
| Equity vs SPY | OLS **beta + Pearson** on full Yahoo overlap | Relative total returns vs SPY; ADV 5d from a prior scan |
| Script | `run_pack.py` (stdlib, backoff) | `build_quant_pack.py` (yfinance/pandas) |

Cite **this pack** for a live HL funding/OI+fundingHistory snapshot and for OLS beta. Cite **#19** for the watch-only appendix, yfinance spot crypto, and ADV 5d. Numbers will not match exactly (HL perp vs Yahoo spot; log vs simple returns on corr; different as-of).

---

## How Research should cite this pack

1. Quote **this file** for tables (human-readable) and the sibling CSVs for exact floats.
2. Always include the **fetch-end timestamp** (`{fetch_log.finished_at}`) — these are public snapshots, not `what_did_we_know(T)` rows. Ingest into Market Memory before treating them as lab knowledge.
3. Theme roles stay with call cards PR #13: **NVDA primary / AVGO satellite** (SMH watch-only, not here); **JPM primary / XLF diversifier**. Do not treat high cross-corr as independent alpha.
4. BTC card ≠ RQ-20260917-A thesis (PR #9). This pack's BTC/ETH funding+OI is a **point snapshot** plus 72h fundingHistory prints.
5. Do not promote any name to `thesis.md` from these tables alone (Skeptic PR #14: 0 pass / 9 revise keepers).

---

## Methodology (no silent conventions)

| Metric | Definition used here |
|---|---|
| Price | Equities/ETFs: Yahoo **adjclose** when present, else **close**. HL: daily candle **close**. |
| Log return | `ln(P_t / P_{{t-1}})` on consecutive bars of that series. |
| 20d / 60d realized vol | Sample stdev (`ddof=1`) of the last 20 / 60 log returns, annualized by `√252` (equities) or `√365` (HL 1d candles, 24/7). |
| 1m / 3m return | Simple total return. Equities: 21 / 63 **session** bars. Crypto: 30 / 90 **calendar** daily bars. |
| ~1y max DD | Peak-to-trough on the trailing 252 session closes (equities) or 365 daily closes (crypto), or shorter if history is shorter. Reported as a negative percent. |
| Equity beta / corr vs SPY | OLS slope and Pearson corr of overlapping daily log returns vs SPY on the **inner-join of US session dates for the 7 equities + SPY** (Yahoo history; does not require BTC/ETH). |
| 9-name heatmap | Pearson of session-aligned **log** returns on the **inner-join of the 9 names**. Primary table uses the full overlap. A trailing-**60** session heatmap is also written (`corr_matrix_60d.csv`) so it can be compared with Research PR #19 (which used 60 simple-return days). Weekend/holiday crypto bars are dropped. |
| Funding | HL 8h `funding` from `metaAndAssetCtxs`. "Naive ann." = `rate × 3 × 365` (arithmetic; **not** a forecast). 72h mean uses `fundingHistory` prints in the last 72 hours. |
| Open interest | Snapshot only (`openInterest` in **coin** units). Notional ≈ `markPx × openInterest`. **No public OI history** on `/info`. |

Native-calendar vol/returns (first table) are **not** mixed across 252 vs 365 without reading `ann_factor` / `ret_*_bars` in `metrics_by_name.csv`.

---

## Fetch status

| Item | Value |
|---|---|
| Attempts | {len(fetch_log.attempts)} |
| HTTP 429 count | {fetch_log.count_status(429)} |
| Failed attempts | {len(failures)} |
| Successful attempts | {sum(1 for row in fetch_log.attempts if row.ok)} |

Attempt-level log: [`quant-20260917/fetch_log.json`](quant-20260917/fetch_log.json), [`quant-20260917/fetch_attempts.csv`](quant-20260917/fetch_attempts.csv).

### Failures / 429s

{chr(10).join(failure_lines)}

### Data gaps (observed, not filled)

{chr(10).join("- " + line for line in gap_lines)}

---

## HL BTC / ETH funding + OI snapshot

Captured `{fetch_log.finished_at}`. OI history is **not** in this pack (API limitation, not a skipped download).

{chr(10).join(hl_table)}

Last `fundingHistory` print per coin is in [`hl_snapshot.csv`](quant-20260917/hl_snapshot.csv); raw prints: [`hl_funding_history_72h.csv`](quant-20260917/hl_funding_history_72h.csv).

---

## Native-calendar vol, drawdown, returns

RV annualization: equities `√252`, crypto `√365`. 1m/3m bar counts differ by class (see methodology).

{chr(10).join(native_table)}

Exact floats + window dates: [`metrics_by_name.csv`](quant-20260917/metrics_by_name.csv).

---

## Equity beta / corr vs SPY

Calendar is **7 equities ∩ SPY** (Yahoo), **not** the 9-name heatmap calendar: **{eq_spy_span}**. BTC/ETH are excluded from beta.

{chr(10).join(beta_table)}

CSV: [`equity_spy_beta_corr.csv`](quant-20260917/equity_spy_beta_corr.csv). Aligned closes: [`aligned_equities_spy_closes.csv`](quant-20260917/aligned_equities_spy_closes.csv).

---

## Cross-correlation heatmap (9 active calls)

Pearson of daily log returns on the 9-name inner-join calendar **{nine_span}**. Return pairs **n = {corr_n}**. This is correlation, not causation; NVDA/AVGO and JPM/XLF are **theme-linked** in PR #13.

{render_heatmap(names, matrix)}

Long form: [`cross_corr.csv`](quant-20260917/cross_corr.csv). Matrix: [`cross_corr_matrix.csv`](quant-20260917/cross_corr_matrix.csv). Aligned closes: [`aligned_session_closes.csv`](quant-20260917/aligned_session_closes.csv).

### Trailing 60 session days (comparable filename to PR #19)

Pearson of the last **{corr_n_60}** overlapping log returns on **{window_60[0]} → {window_60[1]}**. PR #19 used simple returns on a 60-day window; do not treat the two matrices as identical.

{render_heatmap(names, matrix_60)}

CSV (same basename as #19): [`corr_matrix_60d.csv`](quant-20260917/corr_matrix_60d.csv).

---

## What this pack is not

- Not `config/universe.yaml` membership change (PR #15 already locked active vs watch-only).
- Not a must-cut reopen (HYPE, SOL, XRP, ARB, NEAR, LINK, GLD, LLY stay archived).
- Not live trading, signing, wallet code, or `hl_trade`.
- Not Market Memory ingest (no observation envelopes, no `as_of_knowledge`).
- Not a Skeptic pass and not a paper-trade open.

---

## Reproduce

```bash
python3 research/queue/quant-20260917/run_pack.py
```

Requires outbound HTTPS to `query1.finance.yahoo.com` / `query2.finance.yahoo.com` and `api.hyperliquid.xyz`. Stdlib only. Re-running **overwrites** CSVs and this markdown with a new as-of.

**— End QUANT-20260917 active-calls pack —**
"""


def main() -> int:
    started = utcnow()
    log = fetch_mod.FetchLog(pack_id=PACK_ID, started_at=iso(started))
    errors: dict[str, str] = {}

    period2 = int(started.timestamp())
    period1 = int((started - timedelta(days=EQUITY_LOOKBACK_DAYS)).timestamp())
    candle_end_ms = int(started.timestamp() * 1000)
    candle_start_ms = int((started - timedelta(days=CRYPTO_LOOKBACK_DAYS)).timestamp() * 1000)
    funding_start_ms = int((started - timedelta(hours=FUNDING_LOOKBACK_HOURS)).timestamp() * 1000)

    equity_rows: dict[str, list[dict[str, Any]]] = {}
    for ticker in (*EQUITIES, SPY):
        try:
            equity_rows[ticker] = fetch_mod.yahoo_daily_adj_closes(log, ticker, period1=period1, period2=period2)
        except fetch_mod.FetchError as exc:
            errors[f"yahoo:{ticker}"] = str(exc)
            equity_rows[ticker] = []
        time.sleep(0.35)

    crypto_rows: dict[str, list[dict[str, Any]]] = {}
    hl_snap: dict[str, dict[str, Any]] = {}
    funding_hist: dict[str, list[dict[str, Any]]] = {}
    try:
        hl_snap = fetch_mod.hl_asset_snapshot(log, CRYPTO)
    except fetch_mod.FetchError as exc:
        errors["hl:snapshot"] = str(exc)

    for coin in CRYPTO:
        try:
            crypto_rows[coin] = fetch_mod.hl_daily_candles(log, coin, candle_start_ms, candle_end_ms)
        except fetch_mod.FetchError as exc:
            errors[f"hl:candles:{coin}"] = str(exc)
            crypto_rows[coin] = []
        try:
            funding_hist[coin] = fetch_mod.hl_funding_history(log, coin, funding_start_ms, candle_end_ms)
        except fetch_mod.FetchError as exc:
            errors[f"hl:funding:{coin}"] = str(exc)
            funding_hist[coin] = []

    log.finished_at = iso()

    native_rows: list[dict[str, Any]] = []
    for coin in CRYPTO:
        row = native_metrics(coin, crypto_rows.get(coin) or [], crypto=True)
        if coin not in crypto_rows or not crypto_rows[coin]:
            row["status"] = "fetch_failed"
            row["error"] = errors.get(f"hl:candles:{coin}", errors.get("hl:snapshot", ""))
        native_rows.append(row)
    for ticker in EQUITIES:
        row = native_metrics(ticker, equity_rows.get(ticker) or [], crypto=False)
        if not equity_rows.get(ticker):
            row["status"] = "fetch_failed"
            row["error"] = errors.get(f"yahoo:{ticker}", "")
        native_rows.append(row)

    series_for_align: dict[str, list[dict[str, Any]]] = {}
    series_for_align.update({k: v for k, v in crypto_rows.items() if v})
    series_for_align.update({k: v for k, v in equity_rows.items() if v})

    nine_required = tuple(name for name in NAMES if series_for_align.get(name))
    nine_dates, nine_aligned = align_on_dates(series_for_align, nine_required)
    have_all_nine = all(name in nine_aligned and nine_aligned[name] for name in NAMES)
    heatmap_names = NAMES if have_all_nine else tuple(name for name in NAMES if name in nine_aligned)
    _, matrix, corr_n = cross_corr_matrix(nine_aligned, heatmap_names)
    _, matrix_60, corr_n_60 = cross_corr_matrix(nine_aligned, heatmap_names, window=60)
    if corr_n_60 and len(nine_dates) >= corr_n_60:
        window_60 = (nine_dates[-corr_n_60], nine_dates[-1])
    else:
        window_60 = ("", "")

    eq_spy_required = tuple(name for name in (*EQUITIES, SPY) if series_for_align.get(name))
    eq_spy_dates, eq_spy_aligned = align_on_dates(series_for_align, eq_spy_required)
    spy_for_beta = eq_spy_aligned.get(SPY) or []
    equity_for_beta = {ticker: eq_spy_aligned[ticker] for ticker in EQUITIES if ticker in eq_spy_aligned}
    beta_rows = beta_corr_vs_spy(equity_for_beta, spy_for_beta, eq_spy_dates) if spy_for_beta else [
        {
            "ticker": ticker,
            "benchmark": BENCH,
            "n_return_pairs": 0,
            "window_start": "",
            "window_end": "",
            "beta": None,
            "alpha_daily": None,
            "corr": None,
            "status": "spy_fetch_failed",
        }
        for ticker in EQUITIES
    ]

    fetch_day = started.date().isoformat()
    gap_lines = describe_gaps(
        fetch_day=fetch_day,
        last=last_dates(series_for_align),
        nine_dates=nine_dates,
        eq_spy_dates=eq_spy_dates,
    )

    hl_rows: list[dict[str, Any]] = []
    for coin in CRYPTO:
        snap = hl_snap.get(coin) or {"coin": coin}
        stats = funding_stats(funding_hist.get(coin) or [], snap.get("funding"))
        mark = snap.get("mark_px")
        oi = snap.get("open_interest")
        notional = mark * oi if mark is not None and oi is not None else None
        hl_rows.append({**snap, **stats, "oi_notional": notional, "snapshot_captured_at": log.finished_at})

    daily_equity = [row for ticker in (*EQUITIES, SPY) for row in equity_rows.get(ticker) or []]
    daily_crypto = [row for coin in CRYPTO for row in crypto_rows.get(coin) or []]

    nine_wide: list[dict[str, Any]] = []
    for idx, day in enumerate(nine_dates):
        rec: dict[str, Any] = {"date": day}
        for name in heatmap_names:
            rec[name] = nine_aligned[name][idx]
        nine_wide.append(rec)

    eq_spy_wide: list[dict[str, Any]] = []
    for idx, day in enumerate(eq_spy_dates):
        rec = {"date": day}
        for name in (*EQUITIES, SPY):
            rec[name] = eq_spy_aligned[name][idx] if name in eq_spy_aligned else None
        eq_spy_wide.append(rec)

    corr_long: list[dict[str, Any]] = []
    matrix_wide: list[dict[str, Any]] = []
    for a in heatmap_names:
        wide = {"ticker": a}
        for b in heatmap_names:
            value = matrix.get(a, {}).get(b)
            wide[b] = value
            corr_long.append(
                {
                    "a": a,
                    "b": b,
                    "corr": value,
                    "n_return_pairs": corr_n,
                    "window_start": nine_dates[1] if len(nine_dates) > 1 else "",
                    "window_end": nine_dates[-1] if nine_dates else "",
                    "calendar": "us_session_inner_join_9_active_calls",
                }
            )
        matrix_wide.append(wide)

    matrix_60_wide: list[dict[str, Any]] = []
    for a in heatmap_names:
        wide60 = {"ticker": a}
        for b in heatmap_names:
            wide60[b] = matrix_60.get(a, {}).get(b)
        matrix_60_wide.append(wide60)

    funding_flat = [row for coin in CRYPTO for row in funding_hist.get(coin) or []]
    attempt_rows = [row.as_dict() for row in log.attempts]

    write_csv(PACK_DIR / "equity_daily_closes.csv", daily_equity)
    write_csv(PACK_DIR / "crypto_daily_closes.csv", daily_crypto)
    write_csv(PACK_DIR / "spy_daily_closes.csv", equity_rows.get(SPY) or [])
    write_csv(PACK_DIR / "aligned_session_closes.csv", nine_wide)
    write_csv(PACK_DIR / "aligned_equities_spy_closes.csv", eq_spy_wide)
    write_csv(PACK_DIR / "metrics_by_name.csv", native_rows)
    write_csv(PACK_DIR / "equity_spy_beta_corr.csv", beta_rows)
    write_csv(PACK_DIR / "cross_corr.csv", corr_long)
    write_csv(PACK_DIR / "cross_corr_matrix.csv", matrix_wide)
    write_csv(PACK_DIR / "corr_matrix_60d.csv", matrix_60_wide)
    write_csv(PACK_DIR / "hl_snapshot.csv", hl_rows)
    write_csv(PACK_DIR / "hl_funding_history_72h.csv", funding_flat)
    write_csv(PACK_DIR / "fetch_attempts.csv", attempt_rows)

    meta = {
        "pack_id": PACK_ID,
        "started_at": log.started_at,
        "finished_at": log.finished_at,
        "active_calls": {"crypto_perps": list(CRYPTO), "equities": list(EQUITIES)},
        "excluded_watch_only": list(WATCH_ONLY_EXCLUDED),
        "must_cuts_not_reopened": list(MUST_CUTS_NOT_REOPENED),
        "sources": {
            "equities": "Yahoo Finance v8 chart (adjclose preferred)",
            "crypto": "Hyperliquid public /info",
        },
        "conventions": {
            "equity_ann_factor": m.EQUITY_ANN_FACTOR,
            "crypto_ann_factor": m.CRYPTO_ANN_FACTOR,
            "equity_1m_bars": m.EQUITY_1M_BARS,
            "equity_3m_bars": m.EQUITY_3M_BARS,
            "equity_1y_bars": m.EQUITY_1Y_BARS,
            "crypto_1m_bars": m.CRYPTO_1M_BARS,
            "crypto_3m_bars": m.CRYPTO_3M_BARS,
            "crypto_1y_bars": m.CRYPTO_1Y_BARS,
            "stdev_ddof": 1,
            "funding_naive_ann": "rate_8h * 3 * 365",
        },
        "nine_name_session_n_dates": len(nine_dates),
        "equity_spy_session_n_dates": len(eq_spy_dates),
        "cross_corr_n_return_pairs": corr_n,
        "cross_corr_60d_n_return_pairs": corr_n_60,
        "cross_corr_60d_window": {"start": window_60[0], "end": window_60[1]},
        "overlap_research_pr": 19,
        "http_429_count": log.count_status(429),
        "last_dates": last_dates(series_for_align),
        "errors": errors,
        "notes": [
            "Not Market Memory observations; no obs_ids.",
            "OI is snapshot-only; no public OI history on /info.",
            "Do not invent fills for failed tickers.",
            "Beta calendar is equities+SPY; heatmap calendar is the 9 active calls.",
        ],
    }
    (PACK_DIR / "fetch_log.json").write_text(json.dumps(log.as_dict(), indent=2) + "\n", encoding="utf-8")
    (PACK_DIR / "pack_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    summary = render_markdown(
        {
            "fetch_log": log,
            "native_rows": native_rows,
            "beta_rows": beta_rows,
            "names": heatmap_names,
            "matrix": matrix,
            "corr_n": corr_n,
            "matrix_60": matrix_60,
            "corr_n_60": corr_n_60,
            "window_60": window_60,
            "nine_dates": nine_dates,
            "eq_spy_dates": eq_spy_dates,
            "gap_lines": gap_lines,
            "hl_rows": hl_rows,
        }
    )
    summary_path = QUEUE_DIR / "QUANT-20260917-active-calls.md"
    summary_path.write_text(summary, encoding="utf-8")

    print(f"wrote {summary_path}")
    print(f"fetch {log.started_at} → {log.finished_at}")
    print(f"attempts={len(log.attempts)} http_429={log.count_status(429)} errors={errors or '{}'}")
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
