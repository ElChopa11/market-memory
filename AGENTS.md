# Agent roles and permissions

This file is the permission constitution for humans and LLM agents working in `market-memory`. It is stricter than convenience.

**Phase 5b (IMP-010):** Polygon equities adapter (default vendor; Ask N/A) + Hyperliquid public `/info` structure (funding / OI / basis / L2 depth) + optional public spot DQ + FRED/calendar ingest. Phase 4 capabilities (fixture backtest + paper/shadow ledger) and Phase 5a desk boundaries remain. **No** Telegram send, **no** quant-factor implementations, **no** desk runners, **no** live trading, no wallet code, no `hl_trade` / signing. Do not implement the deterministic risk *service*, execution service, or live paths in this phase.

Desk operating model (private research lab, not a fund): [ops/desk-charters.md](ops/desk-charters.md), [ops/decision-rights.md](ops/decision-rights.md), [ops/improvement-queue.md](ops/improvement-queue.md), [docs/runbooks/desks.md](docs/runbooks/desks.md). Hive roles in this file remain the permission constitution; desks are how work is assigned. **No desk overrides the Principal.** Execution & Fund Ops is future-only. Delivery (Telegram / schedules) is **Phase 5e**.

## Non-negotiables

1. **Research cannot access trading credentials.** No API wallet keys, no agent-wallet secrets, no treasury material, no `.env` live keys, no vault paths for execution. Research tools are Market Memory read + artifact write. `packages/research_kit`, `packages/desks`, `packages/quant`, and `packages/delivery` must not import `mm_execution`, ingest private keys, or grow a signing surface.
2. Risk is **code + versioned config**. No LLM at order time.
3. Execution accepts only a typed `OrderIntent` that already passed Risk (when Execution exists).
4. No process both **authors a thesis** and **approves risk** for that thesis. **No self-approve** at any gate (Skeptic, Risk, Principal override).
5. Promotions are git-reviewed and Principal-signed.
6. Do not commit secrets. Do not add Hyperliquid signing, order submission, or exchange-module usage. Ingest is public `/info` only. Intel (Tier 2) must not import opine packages (`mm_research_kit`, `mm_desks`, `mm_quant`, `mm_delivery`).
7. Do not edit `config/risk/environments/live.yaml` unless the Principal requested it and the `principal-review` path in `.github/workflows/risk-config-guard.yml` is followed.

## Tier model (0–7)

Canonical delivery/desk tiers (Principal lock). Charters: [ops/desk-charters.md](ops/desk-charters.md). Architecture: [ADR/0002-desk-delivery-architecture.md](ADR/0002-desk-delivery-architecture.md).

| Tier | Cell | May | Must not |
|---|---|---|---|
| 0 | Principal | Mandate, risk budget, promotion, halt, `live.yaml`, treasury | Place treasury keys on servers or in git; delegate a Principal-only gate |
| 1 | Ops / Chief of Staff | Queue work; run DoD / `check-lifecycle`; `lab thesis` / `lab skeptic` / `lab backtest` / `lab paper`; decompose tasks; open PRs; `lab migrate` / `lab ingest` | Hold trading credentials; promote to live; waive Skeptic; self-approve a thesis |
| 2 | Intel | Read-only public feeds into observations (`hl_info` + Polygon env-key equities in 5b) | Sign orders; scrape in violation of ToS; call user-private info types; **import opine packages**; author theses or Quant verdicts |
| 3a | Crypto | Read Market Memory; write crypto research artifacts from templates; propose tests; fixture backtests | Read trading secrets; import `mm_execution` / signing; edit `live.yaml`; approve own Skeptic or Risk; submit orders |
| 3b | Equities | Same as 3a for equity / post-IPO names (Polygon ingest is **mm_ingest**, not this desk package) | Same as 3a; treat a drawdown as a thesis; invent catalysts |
| 4 | Quant | Closed-verdict triage (`RESEARCH_PRIORITY` \| `MONITOR` \| `DEFER` \| `REJECT` \| `INSUFFICIENT_DATA`); challenge structure / DQ | Call a trade; size; import execution/signing; treat membership as a verdict; skip Skeptic |
| 5 | Skeptic | Adversarial review; fail leakage/look-ahead; **FAIL → return** (`revise` → `in_research`) or **FAIL → archive** (`reject` → `rejected`) | Rubber-stamp own thesis; approve risk; access live keys; skip invalidation quality; self-approve |
| 6 | Risk | Deterministic allow/block from config; explain `rule_id` + `config_version`; **BLOCK is terminal** without Principal override | Call LLMs at decision time; submit orders; silently change `live.yaml`; approve own exception; author theses |
| 7 | Paper Ledger | Shadow ledger bound to theses; open only with invalidation + max loss after Skeptic `pass` | Live keys; bypass Skeptic/Risk; treat paper as Execution |

Hive aliases that are **not** numbered delivery tiers: Briefing (Macro Pulse; still a desk), Unicorn (later), Execution & Fund Ops (**future-only**).

## Role matrix (hive ↔ tier)

| Role | Tier | May | Must not | Credentials |
|---|---|---|---|---|
| **Principal** | 0 | Set mandate and risk budget; approve promotion; halt; change `live.yaml`; own treasury; **override a Risk BLOCK** | Place treasury keys on servers or in git | Hardware wallet (offline); vault admin |
| **Coordinator** | 1 | Queue work; run DoD / `check-lifecycle`; `lab thesis` / `lab skeptic` / `lab backtest` / `lab paper`; decompose tasks; open PRs for research; run `lab migrate` / `lab ingest` | Hold or inject trading credentials; promote to live; waive skeptic; self-approve | None for trading |
| **Intel / ingest** | 2 | Read-only public feeds into observations (`hl_info` + Polygon) | Sign orders; scrape in violation of ToS; call user-private info types; import opine packages | Public / info endpoints; `POLYGON_API_KEY` / `FRED_API_KEY` env only |
| **Research** | 3a Crypto / 3b Equities | Read Market Memory; write `research/` artifacts from templates via `lab thesis` / `mm_research_kit`; run fixture backtests; propose tests | Read trading secrets; import live signing or `mm_execution`; edit live.yaml; approve own risk; submit orders | Read-only / none |
| **Quant** | 4 | Closed-verdict triage; Quant cards / board | Call a trade; skip pipeline; import execution | Read-only / none |
| **Skeptic** | 5 | Adversarial review; fail leakage/look-ahead; demand fixes; return or archive on FAIL | Rubber-stamp own thesis; approve risk; access live keys; skip invalidation quality | Read-only / none |
| **Risk** | 6 | Deterministic allow/block from config; explain `rule_id` + `config_version` | Call LLMs at decision time; submit orders; silently change live.yaml; self-clear a BLOCK | Config only |
| **Paper** | 7 | Shadow ledger bound to theses | Live keys; open without invalidation + max loss | None |
| **Execution** | (later) | Submit Risk-allowed intents; check halt before every order; log intent hash | Run inside research workers; sign without Risk id; bypass halt; touch treasury | API/agent wallet in **live env only** |
| **Briefing** | (Macro desk; not a numbered tier) | Market Pulse from memory | Alert without thresholds; execute | Read-only |
| **Unicorn** | (Later) | Score overlooked candidates | Auto-promote to paper/live | Research-class |

## Escalation

| Event | Path |
|---|---|
| Lifecycle gate fail | Coordinator fixes artifacts; do not patch the checker to skip |
| Skeptic FAIL **return** (`revise`) | Thesis returns to `in_research`; authoring desk fixes; **no self-approve** |
| Skeptic FAIL **archive** (`reject`) | Thesis stays a learning record (`rejected`); new intent required to revive |
| Risk **BLOCK** | **Terminal.** No paper/live. Only the Principal may override. The proposing desk cannot override. |
| Want live.yaml change | Principal-labelled PR (`principal-review`); see security model |
| Halt | Principal (or runbook); drop `config/halt.flag`; Execution must stop new orders |
| Secret leak | Rotation runbook; treat as incident; never recommit the secret |
| Self-approve attempt | Fail the gate. Author ≠ Skeptic of record ≠ Risk allow ≠ Principal override |

**No self-approve.** No desk both authors a thesis and clears Skeptic, Risk, or a Principal override for that thesis.

## Definition of done (agents)

Before claiming a research stage is done, run `./scripts/check-lifecycle.sh` and meet [docs/research-lifecycle.md](docs/research-lifecycle.md).

Before claiming a code change is done: no secrets in the diff, tests/CI green, Phase 5b scope respected (Polygon + HL structure ingest; backtest harness + paper ledger remain; no execution/signing, no risk service, no live path, no Telegram/factors/runners), live still hard-gated, `what_did_we_know` keyed off `as_of_knowledge` (lockstep with `ingested_at`; never `published_at` / `market_time`), backtests keyed off `available_at`, rejected theses still queryable, paper open still requires invalidation + max loss. Import-boundary check (`scripts/check_import_boundaries.py`) is green.
