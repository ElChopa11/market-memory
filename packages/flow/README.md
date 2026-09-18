# mm-flow

Phase 6b **flow / liquidity** library (IMP-015). Derived from existing Hyperliquid structure and equities tape already in Market Memory / fixtures.

**May:** compute PIT-safe funding z, OI delta, basis, depth/spread proxies, ADV/turnover, and a slippage estimate at configured clip sizes; emit `OK | THIN | UNTRADEABLE_AT_SIZE` plus max clip under the slippage budget; persist observation envelopes with `as_of_knowledge = ingested_at`.

**Must not:** depend on `mm_execution` or signing; invent missing book or ADV; call a trade; treat a clip size as an order.

Config: [`config/flow/liquidity.yaml`](../../config/flow/liquidity.yaml).

Runbook: [../../docs/runbooks/flow-desk.md](../../docs/runbooks/flow-desk.md).

Knowledge watermark is `as_of_knowledge` (lockstep with `ingested_at`). Never `published_at` / `market_time`.
