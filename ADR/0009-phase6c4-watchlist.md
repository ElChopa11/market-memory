# ADR 0009 — Phase 6c-4 watchlist monitor + daily scan

- **Status:** Accepted
- **Date:** 2026-09-18
- **Phase:** 6c-4 watchlist monitor. No live trading. No signing. No Redis. No 6d listings. No 6c-5 delivery expansion.

## Context

The locked universe (`config/universe.yaml`) partitions membership as `in_universe` ∪ `watch_only`. PLAYBOOK (`EDGE_SCAN`) is idea-gated and Quant-math-owned. There was no daily Research product that listed every locked name with provenance without inventing a trade.

## Decision

Research owns a watchlist monitor product:

| Piece | Rule |
|---|---|
| Universe | `in_universe` ∪ `watch_only` only. Never `deferred_must_cut`. Never promotion. |
| Cadence | Daily fixture/job: `lab watchlist scan --fixture --no-send` |
| Artifact | Markdown + JSON + `content_hash`; watermark is `as_of_knowledge` |
| States | `COVERED` \| `PARTIAL` \| `UNAVAILABLE` — not Quant verdicts, not calls |
| Naming | `watchlist` sleeve in `mm_common.naming` / `config/desks/naming.yaml`; publishing desk remains `research` |
| Mesh | Existing `desk.research.output` envelope. No new Telegram route (that is 6c-5) |
| PLAYBOOK | Flag existing setups only. Do not compute or inherit `trade_math` |
| LLM / send | Fixture path is zero LLM. `--no-send`. `SEND_ENABLED` stays false |

## Consequences

- Same fixture twice → identical `content_hash`.
- Missing tape stays unavailable.
- Membership remains Principal language, not a Quant Board verdict.

## Not this ADR

6c-5 delivery expansion (IMP-021). 6d listings/IPO (IMP-017). Universe ticker expansion. Live/signing/Redis. Paid data.
