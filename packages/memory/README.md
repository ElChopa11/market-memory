# mm-memory

Phase 0 stub for **Market Memory** (Postgres + object-store pointers).

Implementation starts in Phase 1. Logical tables (from the founding proposal):

`source`, `observation`, `observation_link`, `regime_label`, `hypothesis`/`thesis`, `thesis_evidence`, `research_run`, `skeptic_review`, `paper_trade`, `live_trade`, `risk_decision`, `post_mortem`, `agent_scorecard`, `unicorn_candidate`.

Point-in-time contract: `what_did_we_know(ts)` is observations with `ingested_at <= ts`. Never use `published_at` alone.

**Must not:** execute trades or store private keys.

See [../../docs/founding-brief.md](../../docs/founding-brief.md) and [../../AGENTS.md](../../AGENTS.md).
