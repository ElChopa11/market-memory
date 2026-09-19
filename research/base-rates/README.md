# Standalone Phase-1 instrument base rates

**Outside the desk system.** This folder is a Principal research dump, not Quant sleeve IMP-040 (`research/quant/base-rates/`), not a Memory table, and not a Telegram product.

```bash
python scripts/research/base_rates_phase1.py
```

With this repo’s workspace venv:

```bash
uv run python scripts/research/base_rates_phase1.py
```

Writes `research/base-rates/phase1-<YYYY-MM-DD>.md` using the **Australia/Sydney** calendar date when the run finishes (UTC finish time is printed inside the file).

- Equities: Polygon (`POLYGON_API_KEY`). Crypto: Hyperliquid public `/info` `candleSnapshot` (no key); CoinGecko OHLC only as fallback.
- Offline / cached: `--offline` reads `--bars-dir` / `--cache-dir` only. Live fetches also write `research/base-rates/cache/` (gitignored).
- Every `config/watchlist/monitor.yaml` `names:` ticker appears in the report (computed, or excluded with a reason). Under 200 daily bars → exclude; no substitute symbol, no synthetic fill.
- No Market Memory write, no `run_id`, no desk runner, no Telegram, no LLM.
