# mm-paper

Phase 4 shadow ledger. Paper trades bind to theses and **cannot open** without invalidation and max loss.

**Must not:** hold live API wallets, sign orders, or call Hyperliquid exchange.

```bash
uv run lab paper open THESIS-0001 \
  --size 0.01 \
  --max-loss "500 USDC" \
  --invalidation "Close < 60k on daily" \
  --checkpoint "funding mean-reverts in 48h" \
  --no-db
```

See [../../docs/runbooks/paper-trade.md](../../docs/runbooks/paper-trade.md).
