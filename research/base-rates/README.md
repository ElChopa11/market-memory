# Standalone Phase-1 instrument base rates

**Outside the desk system.** This folder is a Principal research dump, not Quant sleeve IMP-040 (`research/quant/base-rates/`), not a Memory table, and not a Telegram product.

```bash
python scripts/research/base_rates_phase1.py
```

With this repo’s workspace venv:

```bash
uv run python scripts/research/base_rates_phase1.py
```

Writes `research/base-rates/phase1-<YYYY-MM-DD>.md` using the **Australia/Sydney** calendar date when the run finishes (UTC finish time is printed inside the file). Ticker set is `config/watchlist/monitor.yaml` only. Universe overlay of non-monitor names is deferred (queue Gaps); do not fetch AVGO/MSFT/META/JPM/XOM/SMH/XLF in this pass.

On a box with `POLYGON_API_KEY` (never commit the key; do **not** pass `--no-sleep` on free tier):

```bash
uv run python scripts/research/base_rates_phase1.py
```

Principal actions on the 2026-09-19 dump (SPCX void, 2-year cap, permission filter, BMNR audit): [`phase1-2026-09-19-principal-actions.md`](phase1-2026-09-19-principal-actions.md).

- Equities: Polygon (`POLYGON_API_KEY`). Crypto: Hyperliquid public `/info` `candleSnapshot` (no key); CoinGecko OHLC only as fallback.
- Offline / cached: `--offline` reads `--bars-dir` / `--cache-dir` only. Live fetches also write `research/base-rates/cache/` (gitignored).
- Polygon free tier is 5 req/min. **Do not** pass `--no-sleep` on a live free-tier run.
- Continuity check (`mm_ingest.equities.continuity`, listing dates in `config/research/ticker_continuity.yaml`): first bar before known listing date, or a single-bar move beyond N=8 robust-sigma (1.4826×MAD), flags `suspected_ticker_reuse` and **excludes** the series from pools. Resolving a ticker to an identifier does not prove the series is one entity.
- Every `config/watchlist/monitor.yaml` `names:` ticker appears in the monitor report (computed, void, or excluded with a reason). Under 200 daily bars → exclude; no substitute symbol, no synthetic fill.
- Equity daily history on the free tier **IS** Polygon's **2-year** cap. Equity base rates are **PROVISIONAL** until more history exists.
- No Market Memory write, no `run_id`, no desk runner, no Telegram, no LLM.
