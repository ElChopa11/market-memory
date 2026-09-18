# mm-risk

Phase 5d deterministic **allow/block** library (Tier 6). Code + versioned `config/risk/*.yaml` only.

**Must not:** call an LLM at decision time; submit orders; edit `live.yaml`; act as the risk *service* (`apps/risk-service` stays a stub).

BLOCK is terminal without Principal override. `live_trading_enabled` stays false.

See [../../docs/runbooks/desks.md](../../docs/runbooks/desks.md) and [../../AGENTS.md](../../AGENTS.md).
