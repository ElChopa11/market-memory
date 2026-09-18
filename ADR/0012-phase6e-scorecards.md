# ADR 0012 — Phase 6e pack scorecards + queue hygiene

- **Status:** Accepted
- **Date:** 2026-09-18
- **Phase:** 6e scorecards + queue automation. No live trading. No signing. No Redis. No 6f decay-watch.

## Context

6c-1..6c-5 and 6d are on main (#49, #51, #47, #52, #53, #54). Packs were still compared by eye. The Fri 18 Sep pre-market artifact (BRIEF-TAG-20260918) fired ~90m pre-open versus the 30m-pre-open anchor. Treating those packs as like-for-like would be dishonest. The improvement queue's single-threaded READY→IN_PROGRESS rule was documentation-only.

## Decision

Quant owns a pack **scorecard** sleeve (`scorecard`), not a sixth publishing desk:

| Piece | Rule |
|---|---|
| Roster | Publishing desks remain `intel` `research` `quant` `ic_risk` `ops`. Unknown slug `scorecard` fails closed as a desk. |
| Naming | `scorecard` sleeve in `mm_common.naming` / `config/desks/naming.yaml`; publishing desk is `quant` |
| Cadence | `lab scorecard compare --fixture --no-send` |
| Delivery | Ops-owned `lab deliver scorecard --no-send` on the quant route + Ops mirror; inherit `content_hash` |
| Like-for-like | Same `product` + `schedule_anchor` + `universe` and no incomparable tag. Else `NOT_COMPARABLE` with reason codes. No invented numeric compare. |
| Provenance | Every pack and pair carries `content_hash`, `as_of_knowledge`, sources. Knowledge clock is `as_of_knowledge`. |
| Tags | `config/scorecards/tags.yaml` records BRIEF-TAG-20260918. Incident stays OPEN. |
| Queue | `lab queue check` / `scripts/check_queue.py` enforce at most one IMP-* `IN_PROGRESS`. OPEN incidents do not occupy the slot. Helpers do not write, merge, or waive gates. |
| Decay | 6e stubs prompt hashes (`watch_enabled: false`). Full watch is IMP-031 / 6f. |
| LLM / send | Fixture path is zero LLM. `--no-send`. `SEND_ENABLED` stays false |

## Consequences

- Same fixture twice → identical `content_hash`.
- 90m vs 30m pre-open is tagged, never scored as equals.
- Dual IMP-* `IN_PROGRESS` fails CI hygiene.

## Not this ADR

Strategy decay-watch (6f). Universe ticker expansion. Live/signing/Redis. Paid data. Closing OPEN ops incidents. Auto-merge. Gate waivers. Reopening the five-desk roster.
