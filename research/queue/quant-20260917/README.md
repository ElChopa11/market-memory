# QUANT-20260917 scripts + CSV outputs

Public-data pack for Principal-locked **active calls** (PR #15): HL BTC, ETH; equities NVDA, AVGO, MSFT, META, JPM, XLF, XOM.

Citation tables: [`../QUANT-20260917-active-calls.md`](../QUANT-20260917-active-calls.md).

Parallel Research pack: [PR #19](https://github.com/ElChopa11/market-memory/pull/19) uses the same directory. This copy is stdlib `run_pack.py` (live HL `/info` + Yahoo chart). #19 is `build_quant_pack.py` (yfinance + watch-only appendix). Same-path merge needs a Coordinator choice.

```bash
python3 research/queue/quant-20260917/run_pack.py
```

Stdlib only. Hyperliquid public `/info` + Yahoo Finance v8 chart. No secrets, no signing, no `universe.yaml` edits, no must-cut reopens.

This directory is **not** a thesis workspace (no `intent.md`). Lifecycle checker must keep treating it as a queue note.
