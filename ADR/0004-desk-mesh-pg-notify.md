# ADR 0004 — Desk mesh + Postgres LISTEN/NOTIFY bus (Phase 6a)

- **Status:** Accepted (Phase 6a). Follow-ons 6b–6f are **not** implemented here.
- **Date:** 2026-09-18
- **Deciders:** Principal (Phase 6a–6f locked; **bus = Postgres LISTEN/NOTIFY, no Redis**)
- **Phase:** 6a desk protocol hardening + Coord worker stub. No live trading. No signing. No new market-data.

## Context

Phase 5 delivered desk runners (5d) and Telegram as a single Coordinator sink (5e). Desks still ran as a Coordinator CLI pipeline. There was no durable fan-out, no per-desk health, and no way for Coord to assemble a daily pack from Market Memory after a desk published — or failed to.

Without an explicit 6a ADR, later slices can sneak Redis, extra Telegram channels, flow/macro packages, or live paths into the first mesh.

Constraints already decided:

- Live trading hard-gated (`live_trading_enabled: false`).
- Research / desks / quant / delivery must not import `mm_execution`.
- Intel must not import opine packages.
- Degrade, never invent. Point-in-time law: `as_of_knowledge` lockstep with `ingested_at`.
- Telegram remains one sink (5e). Per-desk channel fan-out is 6c.
- **Principal lock: the bus is Postgres `LISTEN/NOTIFY`. Redis is not the bus and is not a source of truth.**

## Decision

**Harden the desk protocol and put a Postgres notify mesh under it.**

1. Every desk output is wrapped in a **DeskEnvelope** with the Principal Phase 6 header:
   `desk`, `as_of` (UTC + Australia/Sydney), `status`, `n`, `completeness`, `regime` (placeholder `unset` until 6b), `op=paper|observation`, `universe`, `sources` / `missing`.
2. **`content_hash`** is SHA-256 of the canonical header+body. `envelope_id` (ULID) is **not** hashed. Re-run the same `as_of` → identical hash unless observations changed.
3. Cadence metadata lives in `config/desks/cadence.yaml` (default `daily`).
4. Full envelopes persist to Market Memory tables `desk_envelope` and `desk_health`. **NOTIFY payloads are lightweight keys only** (`id`, `desk`, `as_of`, `content_hash`, `channel`, `status`) — never pack markdown.
5. Channels / topics:
   - `desk.<slug>.output`
   - `desk.<slug>.alert`
   - `coord.assemble`
   - `dq.event`
6. Coord worker stub subscribes, tracks desk health, and assembles the daily pack from Memory. Killing or omitting a desk still yields a pack: that desk is `FAILED` with `error_class` (`desk_killed` | `desk_missing`).
7. CLI: `lab desk run` remains; `lab mesh dry --fixture --no-db` is the fixture mesh (deterministic double-run hashes). `--kill-desk` is the missing-desk probe.

Body of the envelope is a passthrough of the Phase 5d `DeskOutput` canonical payload. Telegram send is unchanged (5e).

### What 6a includes vs defers

| Include in 6a | Defer |
|---|---|
| Envelope + cadence + `content_hash` idempotency | 6b flow / macro packages + regime (not placeholder) |
| Postgres `LISTEN/NOTIFY` bus (no Redis) | 6c per-desk Telegram channel fan-out |
| Persist envelopes + desk health in Memory | 6d listings / IPO desk |
| Coord worker stub + `lab mesh dry` | 6e scorecards automation |
| Missing-desk assemble (`FAILED` + `error_class`) | 6f decay / prompt versioning |
| ADR + runbook mesh section | Live trading, signing, order endpoints, paid deps |

## Consequences

- **Positive:** Coord can assemble when a desk is down; hashes are stable; Memory is the payload store; NOTIFY stays small; no new network/key/order dependency.
- **Negative:** Listeners need a dedicated Postgres connection (LISTEN is session-scoped). Operators still cron `lab mesh dry` / `lab desk run` until a supervised worker lands.
- **Follow-ups:** IMP-015 / Phase 6b flow+macro+regime — READY/PARKED. Do not fold 6b–6f into 6a.

## Notes

Live trading remains disabled in `config/risk/environments/live.yaml`. Delivery / desks / quant / research must not import `mm_execution`. Do not add Redis.
