# ADR 0001 — v1 monorepo for a private trading intelligence lab

- **Status:** Accepted
- **Date:** 2026-09-16
- **Deciders:** Principal
- **Phase:** 0 (foundations). No production trading code.

## Context

This lab needs compounding institutional memory (observations → theses → reviews → trades) with a small blast radius. A hive of always-on agents, a message bus, and live execution would multiply credentials and provenance gaps before the artifact chain exists.

Constraints already decided:

- Private GitHub repo (`market-memory`).
- Python 3.12 + uv workspace.
- First instruments: BTC and ETH perpetuals (config only).
- Live trading hard-gated until later Principal promotion.
- Hyperliquid first; Australia-based research; hardware-wallet treasury never on a lab server.

## Decision

Ship **one monorepo, four logical processes, one database of record**.

```text
Principal (mandate, risk budget, promote/halt)
    └── Coordinator (queue + DoD; no trading credentials)
            ├── Intel / ingest (read-only)
            ├── Research (hypotheses; artifacts only)
            ├── Skeptic (adversarial review)
            └── Briefing (Market Pulse; later)
                    └── Market Memory (Postgres + object store)
                            ├── Risk Engine (deterministic allow/block)
                            ├── Paper Ledger (shadow P&L)
                            └── Execution (HL API wallet — live later)
```

Specialised “cells” in v1 are **packages with credential boundaries**, not separate always-on agent processes. Coordinator is the Principal plus a thin `lab` CLI (and optional LLM assist for decomposition).

### What is in v1 vs deferred

| Include | Defer |
|---|---|
| Read-only HL + public macro/crypto feeds | Autonomous live trading |
| Observation → thesis → skeptic artifact chain | Multi-venue execution |
| Market Memory as source of truth | Full hive of always-on LLM agents |
| Market Pulse briefs (later phase) | Unicorn Hunter as a product surface |
| Paper/shadow ledger | Wallet/treasury automation |
| Deterministic risk config + simulator | Agent self-modification of live logic |
| Manual Principal promote/halt | Social scraping at scale |

### Control plane (hard)

1. Research packages read Market Memory and write research artifacts only.
2. Risk is code + config only; never an LLM at order time.
3. Execution accepts only a typed `OrderIntent` that already passed Risk.
4. No process may both author a thesis and approve risk for the same thesis.
5. All promotions are git-reviewed and Principal-signed (signed commit or recorded approval).

### Technology (v1)

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Packaging | uv workspace |
| DB of record | Postgres 16 |
| Object store | S3-compatible (MinIO locally) |
| Contracts | Pydantic v2 (introduced when ingest lands) |
| Secrets | Vault / OS keychain injection; never git |
| Local infra | Docker Compose (this phase) |

Deliberate non-choices: no Kafka/NATS yet, no multi-agent orchestration framework as the core, no Rust/C++ execution, no vector-DB-only memory. Facts live in Postgres; git holds human-reviewed artifacts. Each artifact gets a content hash in Market Memory so the two stay linked.

### Repository shape

`packages/` (capability boundaries), `apps/` (process boundaries — execution is a separate deploy unit), `templates/` + `research/` (artifact chain), `config/` (risk/instruments/schedules), `ADR/` + `docs/`, `tests/` (including adversarial later), `scripts/` (DoD gates).

## Consequences

- **Positive:** Auditability, small initial scope, credentials cannot leak into Research by construction, promotions are reviewable, memory compounds in git and Postgres.
- **Negative:** More boilerplate than a single notebook repo; execution latency is not a v1 goal; Coordinator is not a full hive scheduler.
- **Follow-ups:** Phase 1 ingest + Market Memory; later phases add briefing, backtest, paper, risk service, then a tiny manually approved live path.

## Notes

Live trading remains disabled in `config/risk/environments/live.yaml`. Changing that file is Principal-owned and CI-guarded.
