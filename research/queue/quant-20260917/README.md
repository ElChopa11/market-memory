# QUANT-20260917 active-calls pack

Quant snapshot for Skeptic methodology review. **Not a trade. No sizing. No allocation implication.** No thesis folders, no universe expand, no must-cuts.

- Pack write-up: [`../QUANT-20260917-active-calls.md`](../QUANT-20260917-active-calls.md)
- Skeptic REVISE: [PR #21](https://github.com/ElChopa11/market-memory/pull/21) (`research/queue/QUANT-20260917-active-calls-skeptic.md` on that branch)
- Active names: BTC, ETH, NVDA, AVGO, MSFT, META, JPM, XLF, XOM
- Watch-only appendix: UNI, AAVE, SMH
- Conditioned on Principal lock after Skeptic #11/#14 — **not** an evaluation of the selection rule

**Pack `as_of_knowledge`:** `2026-09-17T11:15:47.495030+10:00` (yfinance/Kraken run of record). Do not mix clocks:

| Clock | Stamp | Use |
| --- | --- | --- |
| Price/vol | `2026-09-17T11:15:47.495030+10:00` | native series RV/returns |
| Equity asof | 2026-09-16 (META **2026-09-15** lag) | last Close |
| Yahoo ADV | `2026-09-17T00:49:39Z` | ADV **shares** only |
| HL lab | `2026-09-17T00:28:03Z` | **appendix only** (stale/429) — DO NOT SIZE |

Corr is **pre-FOMC 60d dependence (ends 2026-09-15)**. Relative returns are **simple diff, NOT alpha**. Crypto vol uses √365; equity vol uses √252 — **do not compare**.

## Re-run (price/vol/corr only)

`build_quant_pack.py` writes yfinance/Kraken CSVs and `run_meta.json` next to this README. It does **not** refresh Hyperliquid liquidity or `equity_adv_5d_from_universe_scan.csv`.

```bash
# from repo root; needs pandas, numpy, yfinance
python research/queue/quant-20260917/build_quant_pack.py
```

Re-running **overwrites** CSVs with a new as-of. **Do not treat a later run as the 2026-09-17 pack of record.** Native-series window start/end dates are emitted on new runs; the 2026-09-17 CSVs did not store those starts (see `metric_windows.csv`).
