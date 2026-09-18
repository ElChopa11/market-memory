# ADR 0007 — Phase 6c-1 five-desk roster

- **Status:** Accepted
- **Date:** 2026-09-19
- **Phase:** 6c-1 desk consolidation (11 → 5). No live trading. No signing. No Redis. No 6d listings.

## Context

Phase 5/6a/6b treated Intel, Crypto, Equities, Flow, Macro, Quant, Skeptic, Risk, Coord, Chart, and Briefing as publishing desks. Principal resume-build order 2026-09-19 locks the hive at five desks. Don/Coord remains orchestration only.

## Decision

Canonical publishing desks:

| Slug | Desk | Maps from |
|---|---|---|
| `intel` | Intel (Market Intelligence) | intel assemble + flow + macro + briefing |
| `research` | Research (Investment Research) | crypto + equities + chart |
| `quant` | Quant | quant |
| `ic_risk` | IC/Risk (Investment Committee & Risk) | skeptic + risk **gates** (not two desks) |
| `ops` | Ops | coord pack + delivery ownership |

`coord.assemble` stays a PG NOTIFY orchestration channel. It is not a desk slug. Delivery is Ops-owned.

## Consequences

- `lab desk run --all` runs exactly those five slugs.
- Mesh required publishers are intel, research, quant, ic_risk. Ops assembles.
- IC/Risk still records Skeptic FAIL return/archive and Risk BLOCK as independent gates. No self-approve.
- Telegram fan-out routes the five desks plus `alerts`. Retired `TELEGRAM_CHAT_ID_CRYPTO` / `_CHART` / `_FLOW` are not configured.

## Not this ADR

6c-2 naming layer. 6c-4 watchlist monitor. 6c-5 delivery expansion. 6d listings/IPO (IMP-017, parked until 6c-1..6c-5). Live/signing/Redis.
