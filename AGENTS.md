# Agent roles and permissions

This file is the permission constitution for humans and LLM agents working in `market-memory`. It is stricter than convenience.

**Phase 0:** no live trading, no wallet code, no market ingest. Do not implement those in this phase.

## Non-negotiables

1. **Research cannot access trading credentials.** No API wallet keys, no agent-wallet secrets, no treasury material, no `.env` live keys, no vault paths for execution. Research tools are Market Memory read + artifact write.
2. Risk is **code + versioned config**. No LLM at order time.
3. Execution accepts only a typed `OrderIntent` that already passed Risk (when Execution exists).
4. No process both **authors a thesis** and **approves risk** for that thesis.
5. Promotions are git-reviewed and Principal-signed.
6. Do not commit secrets. Do not add Hyperliquid signing, order submission, or live ingest in Phase 0.
7. Do not edit `config/risk/environments/live.yaml` unless the Principal requested it and the `principal-review` path in `.github/workflows/risk-config-guard.yml` is followed.

## Role matrix

| Role | May | Must not | Credentials |
|---|---|---|---|
| **Principal** | Set mandate and risk budget; approve promotion; halt; change `live.yaml`; own treasury | Place treasury keys on servers or in git | Hardware wallet (offline); vault admin |
| **Coordinator** | Queue work; run DoD / `check-lifecycle`; decompose tasks; open PRs for research | Hold or inject trading credentials; promote to live; waive skeptic | None for trading |
| **Research** | Read Market Memory; write `research/` artifacts from templates; propose tests | Read trading secrets; import live signing; edit live.yaml; approve own risk; submit orders | Read-only / none |
| **Skeptic** | Adversarial review; fail leakage/look-ahead; demand fixes | Rubber-stamp own thesis; approve risk; access live keys; skip invalidation quality | Read-only / none |
| **Risk** | Deterministic allow/block from config; explain `rule_id` + `config_version` | Call LLMs at decision time; submit orders; silently change live.yaml | Config only |
| **Execution** | (Later) submit Risk-allowed intents; check halt before every order; log intent hash | Run inside research workers; sign without Risk id; bypass halt; touch treasury | API/agent wallet in **live env only** |
| **Intel / ingest** | (Later) read-only feeds into observations | Sign orders; scrape in violation of ToS | Public / info endpoints |
| **Briefing** | (Later) Market Pulse from memory | Alert without thresholds; execute | Read-only |
| **Unicorn** | (Later) score overlooked candidates | Auto-promote to paper/live | Research-class |

## Escalation

| Event | Path |
|---|---|
| Lifecycle gate fail | Coordinator fixes artifacts; do not patch the checker to skip |
| Skeptic `reject` | Thesis stays as a learning record; new intent required to revive |
| Want live.yaml change | Principal-labelled PR (`principal-review`); see security model |
| Halt | Principal (or runbook); drop `config/halt.flag`; Execution must stop new orders |
| Secret leak | Rotation runbook; treat as incident; never recommit the secret |

## Definition of done (agents)

Before claiming a research stage is done, run `./scripts/check-lifecycle.sh` and meet [docs/research-lifecycle.md](docs/research-lifecycle.md).

Before claiming a code change is done: no secrets in the diff, tests/CI green, Phase 0 scope respected, live still hard-gated.
