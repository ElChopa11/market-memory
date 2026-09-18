# ADR 0011 — Phase 6d listings / IPO screen

- **Status:** Accepted
- **Date:** 2026-09-18
- **Phase:** 6d listings / IPO. No live trading. No signing. No Redis. No 6e scorecards. No 6f decay-watch.

## Context

6c-1..6c-5 are on main (#49, #51, #47, #52, #53). The hive still lacked a listings / IPO product. Draft PR #48 sketched a sixth `listings` desk on pre-6c-1 code and was parked. Universe promotion, paid listing feeds, and invented prints are forbidden.

## Decision

Research owns a listings / IPO **screen** (sleeve `listings`), not a sixth publishing desk:

| Piece | Rule |
|---|---|
| Roster | Publishing desks remain `intel` `research` `quant` `ic_risk` `ops`. Unknown slug `listings` fails closed as a desk. |
| Naming | `listings` sleeve in `mm_common.naming` / `config/desks/naming.yaml`; publishing desk is `research` |
| Cadence | `lab listings scan --fixture --no-send` |
| Delivery | Ops-owned `lab deliver listings --no-send` on the research route + Ops mirror; inherit `content_hash` |
| Knowledge | `as_of_knowledge` lockstep with `ingested_at`. Future deals / bars stay invisible. Never invent a print. |
| Quant | Closed verdicts only. Inherit `trade_math_hash` when Quant/PLAYBOOK already computed it. Do not invent R/sizing. |
| IC/Risk | Skeptic + Risk still required. No self-approve. `UNTRADEABLE_AT_SIZE` is observation only. Paper stays closed. |
| Universe | Screen-only names. Does not expand `config/universe.yaml`. |
| LLM / send | Fixture path is zero LLM. `--no-send`. `SEND_ENABLED` stays false |

Index add/delete/rebalance is a **separate** event stream from IPO / direct-listing deals. Base rates come from our own Market Memory listing history; `n < n_min` → no claim.

## Consequences

- Same fixture twice → identical `content_hash`.
- Missing listing feed → degraded / unavailable, never invented.
- Post-IPO reclaim screen (`lab equities reclaim-screen`) remains a separate Research product.

## Not this ADR

Scorecards automation (6e). Strategy decay-watch (6f). Universe ticker expansion. Live/signing/Redis. Paid data. Closing OPEN ops incidents. Reopening the five-desk roster.
