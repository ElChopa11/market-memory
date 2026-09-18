# ADR 0002 — Desk / delivery architecture (Phase 5a)

- **Status:** Accepted (Phase 5a). Follow-ons 5b–5e are **not** implemented here.
- **Date:** 2026-09-18
- **Deciders:** Principal (Phase 5a–5e approved; this PR is 5a only)
- **Phase:** 5a desk boundaries. No production trading code. No Polygon client. No Telegram send.

## Context

Hive roles in [AGENTS.md](../AGENTS.md) and the IMP-000 desk charters describe a private research lab, not a fund. Phase 4 shipped fixture backtests and a paper/shadow ledger. The Principal approved a numbered **Tier 0–7** delivery model and a five-slice Phase 5, with **equities default vendor = Polygon** (ingest in 5b, not 5a).

Without an explicit architecture ADR, later slices (adapters, factors, Telegram) can collapse credential and opinion boundaries: research importing execution, Intel opining, Skeptic self-pass, Risk BLOCK treated as allow.

Constraints already decided:

- Live trading hard-gated (`live_trading_enabled: false`).
- Research / desks / quant / delivery must not import `mm_execution` or signing surfaces.
- Intel must not import opine packages.
- No process both authors a thesis and approves it (Skeptic / Risk / Principal override).
- Point-in-time law: `as_of_knowledge` lockstep with `ingested_at`.
- Degrade, never invent.

## Decision

**Commit the desk model in 5a.** Delivery *product* (Telegram, schedules, secrets) is deferred to **5e**.

```text
Tier0 Principal
  └── Tier1 Ops / Chief of Staff
        ├── Tier2 Intel (facts into Market Memory)
        ├── Tier3a Crypto          ─┐
        ├── Tier3b Equities        ─┼─ opine (theses / cards)
        ├── Tier4 Quant            ─┘
        ├── Tier5 Skeptic  (FAIL return | FAIL archive)
        ├── Tier6 Risk     (BLOCK terminal w/o Principal override)
        └── Tier7 Paper Ledger
```

Pipeline (no skipped gates):

```text
Intel → 3a|3b → Quant → Skeptic → Risk → Principal → Paper
```

Macro Pulse remains an operating desk **outside** the numbered 5a tiers. Execution & Fund Ops remains **future-only**. Unicorn remains later / research-class.

### What 5a includes vs defers

| Include in 5a | Defer |
|---|---|
| Tier 0–7 in AGENTS.md + desk charters | 5b Polygon equities ingest + HL funding/OI/basis/depth + spot cross-check |
| Import-boundary CI + skeleton packages (`desks`, `quant`, `delivery`) | 5c–5d Principal-scoped follow-on PRs (one phase per PR) |
| Lifecycle state-machine skeleton over existing statuses + transition log hook (`actor`, `ts`, `reason`) | Full risk *service*, execution, live path |
| Output-contract template (HEADER / TAPE / WHAT CHANGED / TRADE IDEAS intent-only / QUANT NOTE / SKEPTIC FLAGS / RISK STATUS / BOOK / DATA GAPS) | 5e delivery: Telegram client, schedules, secrets |
| Runbook `docs/runbooks/desks.md` (boundaries only) | Desk full runners, quant factor implementations |

### Control plane (hard)

1. **No self-approve.** Author ≠ Skeptic of record ≠ Risk allow ≠ Principal override.
2. **Skeptic FAIL return** (`revise`) → `in_research`. **Skeptic FAIL archive** (`reject`) → `rejected` (terminal learning record; new intent to revive).
3. **Risk BLOCK is terminal** without Principal override. The proposing desk cannot lift it.
4. Research / desks / quant / delivery packages cannot import `mm_execution`, `mm_execution_service`, or signing / live-trade surfaces.
5. Intel (`packages/ingest`) cannot import opine packages: `mm_research_kit`, `mm_desks`, `mm_quant`, `mm_delivery`.
6. Paper open still requires Skeptic `pass`, invalidation, and max loss. Live stays hard-gated.

### Package shape (5a)

Capability packages stay as they are (`research_kit`, `ingest`, `paper`, `risk` stub, `execution` stub). 5a adds **empty-ish skeletons** so CI can enforce import walls before runners exist:

| Package | Tier | 5a contents |
|---|---|---|
| `packages/desks` | 3a / 3b | Constants only |
| `packages/quant` | 4 | Empty `FactorRegistry` |
| `packages/delivery` | 5e later | `SEND_ENABLED = False` |

Equities default Polygon is an **ADR note for 5b**, not a dependency or client in this revision.

## Consequences

- **Positive:** Later slices have a named wall; Skeptic/Risk outcomes are explicit; Principal briefing copy has one contract; Intel cannot grow opinions by import.
- **Negative:** Three stub packages until 5c–5e fill them; Macro is not a numbered tier (operators must not treat that as “Macro is retired”).
- **Follow-ups:** IMP-010 / Phase 5b Polygon + HL structure — **DONE** (#41). IMP-011 / Phase 5c quant factors — **DONE** (#42). IMP-012 / Phase 5d desk runners — **DONE** (#43). IMP-013 / Phase 5e Telegram — **DONE** (#44). Multi-channel mesh is Phase 6a / IMP-014 (this tree).

## Notes

Live trading remains disabled in `config/risk/environments/live.yaml`. Changing that file is Principal-owned and CI-guarded. This ADR does not change Phase 4 paper/backtest behaviour except to log legal status transitions when Market Memory is connected.
