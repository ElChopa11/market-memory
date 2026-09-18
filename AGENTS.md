# Agent roles and permissions

This file is the permission constitution for humans and LLM agents working in `market-memory`. It is stricter than convenience.

**Phase 6d (IMP-017):** Research listings / IPO screen (not a sixth desk). Naming via `mm_common.naming`. Ops-owned `lab deliver listings --no-send`. Quant math inherited. IC/Risk gates still required. **No** live trading, no wallet code, no `hl_trade` / signing.

**Phase 6c-5 (IMP-021 DONE #53):** Ops-owned Telegram delivery expansion. Channel matrix + presentation bound to `mm_common.naming`. Watchlist monitor artifacts from IMP-020 fan out `--no-send`. Coord is not the publisher.

**Phase 6c-4 (IMP-020 DONE #52):** Research watchlist monitor + daily scan of locked `in_universe` ∪ `watch_only`. Deterministic artifact with `as_of_knowledge` + `content_hash`. Naming via `mm_common.naming`.

**Phase 6c-2 (IMP-019 DONE #51):** Canonical desk slugs + display names in `mm_common.naming` / `config/desks/naming.yaml`. PLAYBOOK artifact machine ids vs human labels. Unknown slug fails closed.

**Phase 6c-1 (IMP-018 DONE #49):** Publishing roster cut over to **exactly five desks**: Intel (Market Intelligence), Research (Investment Research), Quant, IC/Risk (Investment Committee & Risk — two gates, not two desks), Ops. Don/Coord is orchestration only. Delivery is Ops-owned.

**Phase 6c (IMP-016 DONE #47):** Per-desk Telegram fan-out + presentation + chart *product* + inbound in `packages/delivery`. Hive PLAYBOOK ladder in `packages/desks` (`mm_desks.playbook`). Quant-owned trade math in `mm_quant.trade_math`. Addendum 6c-0: LLM is WRITER/CRITIC only.

Desk operating model (private research lab, not a fund): [ops/desk-charters.md](ops/desk-charters.md), [ops/decision-rights.md](ops/decision-rights.md), [ops/improvement-queue.md](ops/improvement-queue.md), [docs/runbooks/desks.md](docs/runbooks/desks.md), [docs/runbooks/flow-desk.md](docs/runbooks/flow-desk.md), [docs/runbooks/macro-desk.md](docs/runbooks/macro-desk.md), [docs/runbooks/telegram.md](docs/runbooks/telegram.md), [docs/runbooks/llm-budget.md](docs/runbooks/llm-budget.md), [docs/runbooks/listings.md](docs/runbooks/listings.md), [docs/playbook.md](docs/playbook.md). Hive roles in this file remain the permission constitution; desks are how work is assigned. **No desk overrides the Principal.** Execution & Fund Ops is future-only. Delivery (Telegram) is Ops-owned (Phase 5e + 6c fan-out). Listings/IPO is **Phase 6d** (IMP-017, Research sleeve).

## Non-negotiables

1. **Research cannot access trading credentials.** No API wallet keys, no agent-wallet secrets, no treasury material, no `.env` live keys, no vault paths for execution. Research tools are Market Memory read + artifact write. `packages/research_kit`, `packages/desks`, `packages/quant`, `packages/delivery`, `packages/flow`, `packages/macro`, and `packages/listings` must not import `mm_execution`, ingest private keys, or grow a signing surface.
2. Risk is **code + versioned config**. No LLM at order time.
3. Execution accepts only a typed `OrderIntent` that already passed Risk (when Execution exists).
4. No process both **authors a thesis** and **approves risk** for that thesis. **No self-approve** at any gate (Skeptic, Risk, Principal override).
5. Promotions are git-reviewed and Principal-signed.
6. Do not commit secrets. Do not add Hyperliquid signing, order submission, or exchange-module usage. Ingest is public `/info` only. Intel (Tier 2) must not import opine packages (`mm_research_kit`, `mm_desks`, `mm_quant`, `mm_delivery`, `mm_flow`, `mm_macro`, `mm_listings`).
7. Do not edit `config/risk/environments/live.yaml` unless the Principal requested it and the `principal-review` path in `.github/workflows/risk-config-guard.yml` is followed.

### Delivery desks (Phase 6c-1 Principal hive)

Exactly **five** publishing desks. Don/Coord is orchestration only.

| Desk | Slug | May | Must not |
|---|---|---|---|
| Intel (Market Intelligence) | `intel` | Read-only public feeds + flow/macro sleeves into observations | Sign orders; scrape in violation of ToS; **import opine packages**; author theses |
| Research (Investment Research) | `research` | Crypto + equities + chart sleeves; thesis cards; fixture backtests | Import `mm_execution`; edit `live.yaml`; approve own Skeptic or Risk; submit orders |
| Quant | `quant` | Closed-verdict triage; factor math | Call a trade; size; skip Skeptic |
| IC/Risk | `ic_risk` | **Two gates, not two desks:** Skeptic FAIL return/archive; Risk allow/block | Self-approve; LLM at decision time; lift a BLOCK |
| Ops | `ops` | Queue; pack assemble; delivery (Telegram, `--no-send` default) | Hold trading credentials; waive Skeptic; publish as Coord-the-desk |

Gate numbers 0–7 in the table below remain the permission constitution (Skeptic and Risk are **gates** inside IC/Risk). They are not extra publishing desks.

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

Hive aliases that are **not** numbered delivery tiers: Briefing (Macro Pulse; Intel sleeve), Unicorn (later), Execution & Fund Ops (**future-only**).

## Role matrix (hive ↔ tier)

| Role | Tier | May | Must not | Credentials |
|---|---|---|---|---|
| **Principal** | 0 | Set mandate and risk budget; approve promotion; halt; change `live.yaml`; own treasury; **override a Risk BLOCK** | Place treasury keys on servers or in git | Hardware wallet (offline); vault admin |
| **Coordinator** | 1 (orchestration; not a publishing desk) | Queue work; run DoD / `check-lifecycle`; `lab thesis` / `lab skeptic` / `lab backtest` / `lab paper` / `lab desk run` / `lab mesh` / `lab deliver` / `lab playbook`; decompose tasks; open PRs for research; run `lab migrate` / `lab ingest` | Hold or inject trading credentials; promote to live; waive skeptic; self-approve; publish as a sixth desk | None for trading |
| **Intel / ingest** | 2 | Read-only public feeds into observations (`hl_info` + Polygon) | Sign orders; scrape in violation of ToS; call user-private info types; import opine packages | Public / info endpoints; `POLYGON_API_KEY` / `FRED_API_KEY` env only |
| **Research** | Research desk (crypto 3a / equities 3b sleeves) | Read Market Memory; write `research/` artifacts from templates via `lab thesis` / `mm_research_kit`; run fixture backtests; propose tests | Read trading secrets; import live signing or `mm_execution`; edit live.yaml; approve own risk; submit orders | Read-only / none |
| **Quant** | 4 | Closed-verdict triage; Quant cards / board; **research factor math** (IMP-011; not a call) | Call a trade; skip pipeline; import execution; treat a budget-fraction helper as an order | Read-only / none |
| **Skeptic** | 5 (gate inside IC/Risk) | Adversarial review; fail leakage/look-ahead; demand fixes; return or archive on FAIL | Rubber-stamp own thesis; approve risk; access live keys; skip invalidation quality | Read-only / none |
| **Risk** | 6 (gate inside IC/Risk) | Deterministic allow/block from config; explain `rule_id` + `config_version` | Call LLMs at decision time; submit orders; silently change live.yaml; self-clear a BLOCK | Config only |
| **Paper** | 7 | Shadow ledger bound to theses | Live keys; open without invalidation + max loss | None |
| **Execution** | (later) | Submit Risk-allowed intents; check halt before every order; log intent hash | Run inside research workers; sign without Risk id; bypass halt; touch treasury | API/agent wallet in **live env only** |
| **Briefing** | (Macro desk; not a numbered tier) | Market Pulse from memory | Alert without thresholds; execute | Read-only |
| **Delivery** | Ops-owned (5e Telegram + 6c fan-out) | Desk-pack send via Bot API; dry-run default | Alert without thresholds; trading inbound | `TELEGRAM_*` env on the bot box only |
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

Before claiming a code change is done: no secrets in the diff, tests/CI green, Phase 6d scope respected (listings/IPO Research sleeve on the five-desk roster; naming from IMP-019; Ops delivery from IMP-021; 6c PLAYBOOK/fan-out already on main via #47; no execution/signing, no risk service, no live path, no Redis, no 6e/6f, no live LLM HTTP), live still hard-gated, `what_did_we_know` keyed off `as_of_knowledge` (lockstep with `ingested_at`; never `published_at` / `market_time`), backtests keyed off `available_at`, rejected theses still queryable, paper open still requires invalidation + max loss. Import-boundary check (`scripts/check_import_boundaries.py`) is green and statement-anchored. Pytest never hits the live Telegram API. A no-setup fixture day makes zero LLM calls.
