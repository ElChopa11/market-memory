# mm-ingest

Read-only Hyperliquid **info** ingest (mids, funding, open interest, candles, liquidations when the public `/info` API provides them).

**Must not:** sign orders, import an exchange/signing module, hold API wallets, or call user-private info types.

Default Hyperliquid ingest instruments: BTC, ETH, UNI, AAVE perps from `config/instruments/perps.yaml` (locked universe membership: `config/universe.yaml`). ETH, UNI, and AAVE are watch-only for research (no thesis-priority membership); they still ingest. BTC is the crypto in-universe name. Equities on the universe file are not HL ingest.

See [../../docs/runbooks/ingest.md](../../docs/runbooks/ingest.md).
