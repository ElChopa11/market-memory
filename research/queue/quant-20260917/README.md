# QUANT-20260917 active-calls pack

Quant snapshot for Skeptic methodology review. **Not a trade.** No thesis folders, no universe expand, no must-cuts.

- Pack write-up: [`../QUANT-20260917-active-calls.md`](../QUANT-20260917-active-calls.md)
- Active names: BTC, ETH, NVDA, AVGO, MSFT, META, JPM, XLF, XOM
- Watch-only appendix: UNI, AAVE, SMH

CSVs and `run_meta.json` in this directory are the 2026-09-17 run of record (`run_ts_aest` `2026-09-17T11:15:47.495030+10:00`). Hyperliquid liquidity in the write-up is **stale/partial** (live refresh HTTP 429).

## Re-run (price/vol/corr only)

`build_quant_pack.py` writes yfinance/Kraken CSVs and `run_meta.json` next to this README. It does **not** refresh Hyperliquid liquidity or `equity_adv_5d_from_universe_scan.csv` (that CSV is copied from the 2026-09-17 universe scan).

```bash
# from repo root; needs pandas, numpy, yfinance
python research/queue/quant-20260917/build_quant_pack.py
```

Re-running overwrites CSVs with a new as-of. Do not treat a later run as the 2026-09-17 pack of record.
