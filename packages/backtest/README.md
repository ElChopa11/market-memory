# mm-backtest

Phase 4 reproducible evaluation harness.

Replay JSON or parquet candles with explicit `available_at` knowledge timestamps. Same `params_hash` yields the same `result_hash`. Look-ahead fixtures are rejected.

**Must not:** submit live orders, hold wallets, or leak future bars/observations into fits.

```bash
uv run lab backtest run --fixture tests/fixtures/backtest/clean_bars.json --strategy buy_hold --no-db
```

See [../../docs/runbooks/backtest.md](../../docs/runbooks/backtest.md).
