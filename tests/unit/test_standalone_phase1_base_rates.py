"""Standalone Phase-1 instrument base rates (outside the desk system)."""

from __future__ import annotations

import ast
import importlib.util
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "research" / "base_rates_phase1.py"
MONITOR = ROOT / "config" / "watchlist" / "monitor.yaml"


def _load():
    spec = importlib.util.spec_from_file_location("base_rates_phase1", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _bar(d: date, close: float, *, high: float | None = None, low: float | None = None, open_: float | None = None):
    mod = _load()
    o = close if open_ is None else open_
    return mod.Bar(
        date=d,
        open=o,
        high=close + 1.0 if high is None else high,
        low=close - 1.0 if low is None else low,
        close=close,
    )


def _spec(mod, ticker: str = "BTCUSD"):
    return mod.SymbolSpec(
        ticker=ticker,
        membership_key="BTC",
        tape_alias="BTC",
        round="crypto",
        tier="universe",
        cluster="crypto_major",
        venue="hyperliquid",
        kind="perp",
        qualified_id="HL:BTC",
        coin="BTC",
        note="",
    )


def _walk_series(n: int, start: date, start_px: float = 100.0, step: float = 0.1) -> list:
    bars = []
    px = start_px
    for i in range(n):
        d = start + timedelta(days=i)
        o = px
        c = px + step
        bars.append(_bar(d, c, open_=o, high=max(o, c) + 0.5, low=min(o, c) - 0.5))
        px = c
    return bars


def test_script_has_no_desk_or_memory_or_telegram_imports() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    forbidden = {
        "mm_desks",
        "mm_memory",
        "mm_delivery",
        "mm_execution",
        "mm_quant",
        "mm_flow",
        "mm_macro",
        "mm_listings",
        "mm_research_kit",
        "redis",
    }
    assert names & forbidden == set(), names & forbidden


def test_monitor_tickers_all_appear_when_offline_missing(tmp_path: Path) -> None:
    mod = _load()
    symbols = mod.load_monitor_symbols(MONITOR)
    tickers = [s.ticker for s in symbols]
    assert "BTCUSD" in tickers and "NVDA" in tickers and "CHIPIUSD" in tickers
    assert len(tickers) == len(set(tickers))

    out_dir = tmp_path / "out"
    rc = mod.run(
        [
            "--monitor",
            str(MONITOR),
            "--output-dir",
            str(out_dir),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--bars-dir",
            str(tmp_path / "empty_bars"),
            "--offline",
            "--now",
            "2026-09-19T12:00:00+00:00",
            "--no-sleep",
        ]
    )
    assert rc == 0
    report = (out_dir / "phase1-2026-09-19.md").read_text(encoding="utf-8")
    for ticker in tickers:
        assert ticker in report
    assert "excluded" in report
    assert "Australia/Sydney" in report
    assert "offline: no bars-dir/cache file" in report
    assert "2-year free-tier history limit" in report
    assert "PROVISIONAL" in report
    assert "principal-actions" in report


def test_under_200_bars_excluded_no_substitute() -> None:
    mod = _load()
    bars = _walk_series(199, date(2024, 1, 1))
    result = mod.compute_for_bars(_spec(mod), bars, source="fixture", cost_frac=0.0029, ann=365.0)
    assert result.exclusion is not None
    assert "199 daily bars" in result.exclusion
    assert "no substitute" in result.exclusion
    assert result.regimes == {}


def test_sma_has_no_lookahead() -> None:
    mod = _load()
    closes = [float(i) for i in range(1, 221)]
    sma = mod.sma_series(closes, 200)
    assert sma[198] is None
    assert sma[199] == sum(closes[:200]) / 200
    # A spike on the last bar must not affect the SMA 10 bars earlier.
    spiked = list(closes)
    spiked[-1] = 10_000.0
    sma2 = mod.sma_series(spiked, 200)
    assert sma2[209] == sma[209]


def test_forward_return_is_from_bar_after_signal() -> None:
    mod = _load()
    start = date(2024, 1, 1)
    bars = []
    px = 100.0
    for i in range(220):
        d = start + timedelta(days=i)
        bars.append(_bar(d, px, open_=px, high=px + 1, low=px - 1))
        px += 1.0
    result = mod.compute_for_bars(_spec(mod), bars, source="fixture", cost_frac=0.0, ann=365.0)
    assert result.exclusion is None
    d1 = result.regimes["unconditional"].fwd[1]
    # close[t+1]/close[t] - 1 = 1/close[t]; first 1-bar from t=0 is 1/100 = 0.01
    assert d1.n >= 200
    assert abs(d1.mean - statistics_mean_1bar(bars)) < 1e-12


def statistics_mean_1bar(bars) -> float:
    xs = [bars[i + 1].close / bars[i].close - 1.0 for i in range(len(bars) - 1)]
    return sum(xs) / len(xs)


def test_bracket_target_stop_tie_timeout() -> None:
    mod = _load()
    entry = 100.0
    r = 2.0
    future_target = [_bar(date(2024, 1, 2), 101, high=105, low=99.5)]
    future_stop = [_bar(date(2024, 1, 2), 99, high=100.5, low=97)]
    future_tie = [_bar(date(2024, 1, 2), 100, high=105, low=97)]
    future_to = [_bar(date(2024, 1, 2), 100.2, high=100.5, low=99.5)]
    assert mod.evaluate_long_bracket(entry, entry - r, entry + 2 * r, future_target) == "target"
    assert mod.evaluate_long_bracket(entry, entry - r, entry + 2 * r, future_stop) == "stop"
    assert mod.evaluate_long_bracket(entry, entry - r, entry + 2 * r, future_tie) == "tie"
    assert mod.evaluate_long_bracket(entry, entry - r, entry + 2 * r, future_to) == "timeout"


def test_regime_under_100_flagged() -> None:
    mod = _load()
    # Strong uptrend so most bars after SMA200 are trend-up; chop/down stay small.
    bars = _walk_series(250, date(2024, 1, 1), start_px=50.0, step=0.8)
    result = mod.compute_for_bars(_spec(mod), bars, source="fixture", cost_frac=0.0, ann=365.0)
    assert result.exclusion is None
    down = result.regimes["trend-down"]
    assert down.n_bars < 100
    assert down.under_min is True


def test_end_to_end_bars_dir_writes_sydney_dated_report(tmp_path: Path) -> None:
    mod = _load()
    bars_dir = tmp_path / "bars"
    bars_dir.mkdir()
    start = date(2023, 1, 1)
    payload = {
        "ticker": "BTCUSD",
        "source": "fixture",
        "bars": [
            {
                "date": (start + timedelta(days=i)).isoformat(),
                "open": 100 + i,
                "high": 101 + i,
                "low": 99 + i,
                "close": 100.5 + i,
            }
            for i in range(250)
        ],
    }
    import json

    (bars_dir / "BTCUSD.json").write_text(json.dumps(payload), encoding="utf-8")
    out_dir = tmp_path / "out"
    rc = mod.run(
        [
            "--monitor",
            str(MONITOR),
            "--output-dir",
            str(out_dir),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--bars-dir",
            str(bars_dir),
            "--offline",
            "--now",
            "2026-09-19T14:00:00+10:00",  # 04:00 UTC same Sydney date
            "--no-sleep",
        ]
    )
    assert rc == 0
    report_path = out_dir / "phase1-2026-09-19.md"
    assert report_path.is_file()
    text = report_path.read_text(encoding="utf-8")
    assert "BTCUSD" in text and "computed" in text
    assert "NVDA" in text
    assert "insufficient history" in text or "offline:" in text
    assert "Coin-flip 1R:2R" in text or "Descriptive mixture" in text
    assert "Australia/Sydney" in text
    # Deterministic given same bars + frozen clock.
    rc2 = mod.run(
        [
            "--monitor",
            str(MONITOR),
            "--output-dir",
            str(out_dir),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--bars-dir",
            str(bars_dir),
            "--offline",
            "--now",
            "2026-09-19T14:00:00+10:00",
            "--no-sleep",
        ]
    )
    assert rc2 == 0
    assert report_path.read_text(encoding="utf-8") == text


def test_hl_coin_uses_resolution_chip_not_chipi() -> None:
    mod = _load()
    symbols = {s.ticker: s for s in mod.load_monitor_symbols(MONITOR)}
    assert mod.hl_coin(symbols["CHIPIUSD"]) == "CHIP"
    assert mod.polygon_ticker(symbols["NQ1!"]) is None
    assert mod.polygon_ticker(symbols["NVDA"]) == "NVDA"
    assert mod.polygon_ticker(symbols["SPX"]) == "I:SPX"
    assert symbols["CBRS"].listing_date == date(2026, 5, 14)
    assert symbols["SPCX"].listing_date is None  # unresolved in monitor; yaml listed_on is 2026-06-11


def test_spcx_listing_date_voids_and_drops_from_pool(tmp_path: Path) -> None:
    import json

    mod = _load()
    bars_dir = tmp_path / "bars"
    bars_dir.mkdir()
    start = date(2024, 9, 19)
    btc = {
        "ticker": "BTCUSD",
        "source": "fixture",
        "bars": [
            {
                "date": (date(2023, 1, 1) + timedelta(days=i)).isoformat(),
                "open": 100 + i,
                "high": 101 + i,
                "low": 99 + i,
                "close": 100.5 + i,
            }
            for i in range(250)
        ],
    }
    # Pre-IPO SpaceX ticker string: ETF tape from the 2y window start.
    spcx = {
        "ticker": "SPCX",
        "source": "polygon:SPCX",
        "bars": [
            {
                "date": (start + timedelta(days=i)).isoformat(),
                "open": 10.0,
                "high": 10.1,
                "low": 9.9,
                "close": 10.0 if i < 200 else 10.0 + (i - 199) * 0.01,
                "volume": 1670,
            }
            for i in range(250)
        ],
    }
    (bars_dir / "BTCUSD.json").write_text(json.dumps(btc), encoding="utf-8")
    (bars_dir / "SPCX.json").write_text(json.dumps(spcx), encoding="utf-8")
    out_dir = tmp_path / "out"
    rc = mod.run(
        [
            "--monitor",
            str(MONITOR),
            "--output-dir",
            str(out_dir),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--bars-dir",
            str(bars_dir),
            "--offline",
            "--now",
            "2026-09-19T12:00:00+00:00",
            "--no-sleep",
        ]
    )
    assert rc == 0
    text = (out_dir / "phase1-2026-09-19.md").read_text(encoding="utf-8")
    assert "PROVISIONAL" in text
    assert "2-year free-tier history limit" in text
    assert "IS** the vendor cap" in text or "**IS** the vendor cap" in text
    assert "suspected_ticker_reuse" in text
    assert "| SPCX |" in text and "void" in text
    assert "Voided ``suspected_ticker_reuse`` names are **not** in the void-excluded pool: SPCX" in text
    # BTC is in the pool; SPCX is not listed as computed in three-line "Enough history".
    assert "Enough history to study at all" in text
    assert "BTCUSD" in text
    line2 = [ln for ln in text.splitlines() if "Enough history to study at all" in ln][0]
    assert "SPCX" not in line2
    assert "full pool" in text.lower() or "Full pool" in text
    assert "continuity-void-excluded" in text
    assert "descriptive mixture holds regardless" in text.lower()
    assert "listing-date" in text.lower() or "listing date" in text.lower()
    assert "level-shift" in text.lower() or "level shift" in text.lower()
    assert "FLAG only" in text or "flag only" in text.lower()
    assert "adjusted=true" in text
    assert "permission filter" in text.lower()
    assert "VVVUSD" in text or "interpretable outlier" in text
    assert "BMNR" in text and "STRC" in text
    assert "--overlay" not in text
    assert "universe-overlay" not in text
    assert "--overlay" not in SCRIPT.read_text(encoding="utf-8")
    assert "descriptive mixture" in text.lower()
    assert "NOT** a strategy hurdle" in text or "not a strategy hurdle" in text.lower()
    assert "IC Gate 1" in text and "FAIL" in text
    assert "median headline" in text.lower() or "1-bar median" in text
    assert "must beat this after costs" not in text.lower()


def _eq_spec(mod, ticker: str = "NVDA"):
    return mod.SymbolSpec(
        ticker=ticker,
        membership_key=ticker,
        tape_alias=ticker,
        round="base",
        tier="universe",
        cluster="eq",
        venue="nasdaq",
        kind="equity",
        qualified_id=f"NASDAQ:{ticker}",
        coin=None,
        note="",
    )


def test_nvda_like_fat_tail_stays_in_void_excluded_pool() -> None:
    mod = _load()
    start = date(2024, 9, 19)
    bars = []
    px = 100.0
    for i in range(250):
        if i == 120:
            px = px * 1.1872
        else:
            px = px * 1.0015
        bars.append(_bar(start + timedelta(days=i), px, open_=px, high=px + 1, low=px - 1))
    result = mod.compute_for_bars(
        _eq_spec(mod, "NVDA"), bars, source="polygon:NVDA", cost_frac=0.0019, ann=252.0
    )
    result = mod.apply_continuity(
        result,
        bars,
        spec=_eq_spec(mod, "NVDA"),
        source="polygon:NVDA",
        continuity_cfg=mod.load_continuity_config(ROOT / "config" / "research" / "ticker_continuity.yaml"),
    )
    assert result.exclusion is None
    assert result.void_code is None
    assert result.regimes
    # Dual pools: this name is in both.
    assert result in mod._void_excluded_pool([result])
    assert result in mod._full_pool([result])


def test_level_shift_voids_but_remains_in_full_pool() -> None:
    mod = _load()
    start = date(2024, 9, 19)
    bars = []
    for i in range(220):
        px = 22.0 if i < 40 else 150.0
        bars.append(_bar(start + timedelta(days=i), px, open_=px, high=px + 1, low=px - 1))
    spec = _eq_spec(mod, "SPCX")
    result = mod.compute_for_bars(spec, bars, source="polygon:SPCX", cost_frac=0.0019, ann=252.0)
    cfg = {
        "level_shift_window": 20,
        "level_shift_ratio": 3.0,
        "single_bar_flag_abs": 0.20,
        "instruments": {},  # no listed_on — void on B only
    }
    result = mod.apply_continuity(result, bars, spec=spec, source="polygon:SPCX", continuity_cfg=cfg)
    assert result.void_code == "suspected_ticker_reuse"
    assert result.exclusion is not None
    assert result.regimes  # stats kept so the full pool can include it
    full = mod._full_pool([result])
    clean = mod._void_excluded_pool([result])
    assert full == [result]
    assert clean == []
    rates_full = mod._pool_long_rates(full)
    rates_clean = mod._pool_long_rates(clean)
    assert rates_full["gross_hits"] + rates_full["gross_stops"] > 0
    assert rates_clean["gross_hits"] == 0 and rates_clean["gross_stops"] == 0


def test_three_line_summary_median_headline_and_pooled_not_hurdle() -> None:
    """FIX 2 / Attack A8: median first. FIX 1 / Attack 5: pooled is descriptive only."""
    mod = _load()
    bars = _walk_series(250, date(2024, 1, 1), start_px=50.0, step=0.8)
    result = mod.compute_for_bars(_spec(mod), bars, source="fixture", cost_frac=0.0, ann=365.0)
    summary = mod._three_line_summary([result])
    assert "1-bar median" in summary
    assert "10-bar median" in summary
    assert "1-bar mean" not in summary.split("1-bar median")[0]
    # Mean is parenthetical, after median.
    assert "(mean " in summary
    assert "median headline" in summary.lower()
    assert "descriptive mixture" in summary.lower()
    assert "NOT a strategy hurdle" in summary or "not a strategy hurdle" in summary.lower()
    assert "must beat this after costs" not in summary.lower()
    assert "instrument's own" in summary.lower()
    banner = "\n".join(mod._provisional_banner([result]))
    assert "IC Gate 1" in banner
    assert "FAIL" in banner
    assert "descriptive coin-flip mixture" in banner
    assert "NOT** a strategy hurdle" in banner or "NOT a strategy hurdle" in banner
    assert FWD_TABLE_HEADER_MEDIAN_FIRST(mod)


def FWD_TABLE_HEADER_MEDIAN_FIRST(mod) -> bool:
    assert mod.FWD_TABLE_HEADER[2] == "median"
    assert mod.FWD_TABLE_HEADER[3] == "mean"
    return True


