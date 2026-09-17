# Founding brief

Private, Australia-based trading intelligence lab. Hyperliquid perpetuals first. Optimise for **auditability, small blast radius, and compounding institutional memory** — not maximum automation.

This brief freezes the operating philosophy for v1. Implementation proceeds in numbered phases; **this repository is at Phase 4 (backtest harness + paper/shadow ledger).**

## Operating philosophy

- Every claim is an **observation with provenance**. Theses link observations. Trades link theses.
- Git holds human review, blame, and promotion history. Postgres (Market Memory) holds queryable facts, analogues, and source scorecards. Artifact content hashes link the two.
- Point-in-time knowledge is `as_of_knowledge <= T` (lockstep with `ingested_at`). Never treat `published_at` or `market_time` as “what we knew at T”.
- Soft-delete never removes audit rows; mark data quality rejected instead.
- LLMs may research. They may not trade. Risk is deterministic code + config. Execution never sees an unsigned, un-risked intent.
- No process both authors a thesis and approves risk for that thesis.
- Promotions are git-reviewed and Principal-signed. Playbook changes open a PR; live logic is never hot-patched.
- Lawful collection / ToS only. No credential stuffing, no TOS-violating scrapers.

## Hive roles (v1: packages + permissions, not always-on agents)

| Role | Mandate | Credentials |
|---|---|---|
| **Principal** | Mandate, risk budget, promote, halt | Owns live.yaml and the treasury (hardware wallet; never on a server) |
| **Coordinator** | Research queue, DoD checks, task decomposition | No trading credentials |
| **Intel (ingest)** | Read-only feeds into Market Memory | Public / read-only only |
| **Research** | Hypotheses, artifact chain, evidence links | Market Memory read + artifact write. **No trading credentials** |
| **Skeptic** | Adversarial review of theses | Same as Research; cannot approve risk or submit orders |
| **Briefing** | Market Pulse (pre-open / close / threshold-gated alerts) | Read-only |
| **Risk** | Deterministic allow/block from versioned config | No LLM at order time; no order submission |
| **Paper** | Shadow ledger bound to theses | No live keys |
| **Execution** | Typed `OrderIntent` after Risk allow (live later) | API/agent wallet in live env only; isolated deploy |
| **Unicorn** | Candidate scoring (later phase) | Research-class; cannot self-promote |

Coordinator in v1 is the Principal plus a thin `lab` CLI. Cells are packages with boundaries. Agents, when added, are clients of those packages.

## Lifecycle (artifact chain)

```text
intent → thesis → research-plan → evidence/backtests
      → skeptic-review → paper → promotion-decision → live (gated)
      → post-mortem (required before size increase)
```

Statuses: `draft | in_research | in_skeptic | paper | live | rejected | retired`.

Rejected theses remain learning records. A thesis cannot skip Skeptic. Paper cannot open without invalidation and max loss. Live cannot open without dual control (Risk allow **and** Principal promotion). Halt is checked before every live order (when live exists).

Definition-of-done gates: [research-lifecycle.md](research-lifecycle.md). Role permissions: [AGENTS.md](../AGENTS.md). Security: [security-model.md](security-model.md).

## v1 scope

**In:** read-only ingest, artifact chain, Market Memory, paper ledger, deterministic risk config + simulator, manual promote/halt.

**Out (this repo phase and several after):** autonomous live trading, multi-venue execution, wallet automation, always-on multi-agent hive, Unicorn as a product surface, social scraping at scale.

Default Hyperliquid instruments: **BTC, ETH, UNI, AAVE perps** (Principal lock 2026-09-17 in `config/universe.yaml`). Equities on that file are a briefing / future equity-feed watchlist, not HL. Live trading is **hard-gated** until the Principal explicitly promotes after later-phase acceptance.
