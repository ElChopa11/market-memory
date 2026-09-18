# ADR 0013 — Phase 6f prompt-hash decay watch

- **Status:** Accepted
- **Date:** 2026-09-18
- **Phase:** 6f strategy decay-watch + versioned prompt hashes. No live trading. No signing. No Redis. No gate waiver.

## Context

6c–6e are on main (#49 roster, #51 naming, #47 playbook, #52 watchlist, #53 Ops delivery, #54 listings, #55 scorecards). 6e stubbed decay inputs with `watch_enabled: false`. Prompt files under `config/prompts/` are already versioned (6c-0); operators still had no standing watch that alerts on hash drift. BRIEF-TAG-20260918 remains `NOT_COMPARABLE` on scorecards — decay must not invent a comparable score for that tag.

## Decision

Quant owns a **decay** sleeve (`decay`), not a sixth publishing desk. Ops owns the alert / Telegram path:

| Piece | Rule |
|---|---|
| Roster | Publishing desks remain `intel` `research` `quant` `ic_risk` `ops`. Unknown slug `decay` fails closed as a desk. |
| Naming | `decay` sleeve in `mm_common.naming` / `config/desks/naming.yaml`; publishing desk is `quant` |
| Cadence | `lab decay watch --fixture --no-send` |
| Hashes | SHA-256 of versioned prompt files + listed strategy/config files vs pinned `expected_sha256` |
| Match | `MATCH` / status `OK`; output channel only |
| Drift | `MISMATCH` \| `MISSING` \| `UNPINNED` → `DEGRADED` + NOTIFY `desk.quant.alert` + queue *signal* |
| Queue signal | Kind `NOTIFY`. Does not write the queue, merge, waive gates, auto-disable, or close OPEN incidents |
| Delivery | Ops-owned `lab deliver decay --no-send` on the quant route + Ops mirror; inherit `content_hash` |
| Scorecards | Attached IMP-030 pairs pass through. `NOT_COMPARABLE` stays tagged. No invented numeric compare. |
| LLM / send | Fixture path is zero LLM. `--no-send`. `SEND_ENABLED` stays false |
| Auto-disable | `auto_disable: false`. Changing a prompt is a PR. Principal only for disable. |

## Consequences

- Same fixture twice → identical `content_hash`.
- Prompt edit without updating the pin fires a mismatch alert.
- 90m vs 30m pre-open stays tagged when decay attaches a scorecard fixture.
- Dual IMP-* `IN_PROGRESS` still fails CI hygiene.

## Not this ADR

Universe ticker expansion. Live/signing/Redis. Paid data. Closing OPEN ops incidents. Auto-merge. Gate waivers. Auto-disable of prompts. Reopening the five-desk roster.
