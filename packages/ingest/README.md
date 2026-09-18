# mm-ingest

Read-only ingest: Hyperliquid **info** (mids, funding, open interest, candles, liquidations, L2 snapshot, predicted funding) plus **Polygon** equities (default vendor; Principal lock) and FRED/calendar.

**Must not:** sign orders, import an exchange/signing module, hold API wallets, or call user-private info types.

Default Hyperliquid ingest instruments: BTC, ETH, UNI, AAVE perps from `config/instruments/perps.yaml` (locked universe membership: `config/universe.yaml`). ETH, UNI, and AAVE are watch-only for research (no thesis-priority membership); they still ingest. BTC is the crypto in-universe name. Equities on the universe file ingest via `mm_ingest.equities` (Polygon), not Hyperliquid.

Dry-run without keys: `uv run lab ingest --fixture tests/fixtures/phase5b/polygon_ohlcv.json --no-db`. See [../../docs/runbooks/polygon-hl-structure.md](../../docs/runbooks/polygon-hl-structure.md) and [../../docs/runbooks/ingest.md](../../docs/runbooks/ingest.md).
