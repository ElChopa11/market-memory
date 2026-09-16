# mm-ingest

Read-only Hyperliquid **info** ingest (mids, funding, open interest, candles, liquidations when the public `/info` API provides them).

**Must not:** sign orders, import an exchange/signing module, hold API wallets, or call user-private info types.

Default instruments: BTC and ETH perps from `config/instruments/perps.yaml`.

See [../../docs/runbooks/ingest.md](../../docs/runbooks/ingest.md).
