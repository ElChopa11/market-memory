# Desk charters

Market Memory is a **private research lab**, not a managed fund and not an autonomous trading system. These charters encode a hedge-fund-style desk model for how work is owned **today** (Phase 5a: desk boundaries over Phase 4 backtest + paper/shadow ledger). They do not raise external capital, enable live trading, or authorise any desk to place orders.

**Canonical desk names (Principal lock)** — use these strings in reports, the improvement queue, and PR titles:

| Desk | Notes |
|---|---|
| Principal | Sole mandate, risk budget, promotion, execution enablement |
| Chief of Staff / Hive Coordinator | Operating system (Don); not an investment desk |
| Data & Market Memory Desk | Trusted information infrastructure (Intel + Memory) |
| Crypto Desk | Digital-asset research |
| Equities & Post-IPO Desk | Equity / thematic / post-IPO research |
| Macro & Cross-Asset Desk | Rates, USD, energy, vol, US session context (not a numbered delivery tier) |
| Quant & Market Structure Desk | Triage only; closed verdict set |
| Independent Skeptic | Cannot author and approve the same thesis |
| Risk (independent veto) | Blocks unsafe progression; never creates theses |
| Paper Ledger | Shadow ledger; not Execution |
| Execution & Fund Ops | **Future-only** until Principal separately activates |

### Delivery tiers (0–7)

Principal lock for Phase 5. Hive roles stay in [AGENTS.md](../AGENTS.md). Runbook: [docs/runbooks/desks.md](../docs/runbooks/desks.md). ADR: [ADR/0002-desk-delivery-architecture.md](../ADR/0002-desk-delivery-architecture.md).

| Tier | Cell | Desk name | Package skeleton (5a) |
|---|---|---|---|
| 0 | Principal | Principal | (human; no package) |
| 1 | Ops / CoS | Chief of Staff / Hive Coordinator | `apps/lab-cli` (existing) |
| 2 | Intel | Data & Market Memory Desk | `packages/ingest` (existing; no opine imports) |
| 3a | Crypto | Crypto Desk | `packages/desks` (`mm_desks.crypto` stub) |
| 3b | Equities | Equities & Post-IPO Desk | `packages/desks` (`mm_desks.equities` stub) |
| 4 | Quant | Quant & Market Structure Desk | `packages/quant` (IMP-011 factor library; no runners) |
| 5 | Skeptic | Independent Skeptic | `packages/research_kit` skeptic (existing) |
| 6 | Risk | Risk (independent veto) | `packages/risk` (stub service; config exists) |
| 7 | Paper Ledger | Paper Ledger (lab control) | `packages/paper` (existing) |

**Not a numbered tier in 5a:** Macro & Cross-Asset (Pulse still operates), Unicorn, Execution & Fund Ops (future-only), Delivery/Telegram (`packages/delivery` skeleton; **send is 5e**).

**Hard rules**

- **No self-approve.** Authoring desk ≠ Skeptic of record ≠ Risk allow ≠ Principal override for the same thesis.
- **Skeptic FAIL return:** verdict `revise` → status `in_research`. Authoring desk fixes; independent Skeptic re-reviews.
- **Skeptic FAIL archive:** verdict `reject` → status `rejected` (terminal learning record). Revival requires a **new intent**.
- **Risk BLOCK is terminal** without Principal override. The proposing desk cannot lift a BLOCK.
- Pipeline is not skippable: `Intel → 3a/3b → Quant → Skeptic → Risk → Principal → Paper`.

Hive roles in [AGENTS.md](../AGENTS.md) remain the permission constitution. This file maps those roles onto desks, names artifacts, and forbids skipped gates. Decision tables live in [decision-rights.md](decision-rights.md). Work is queued in [improvement-queue.md](improvement-queue.md).

**No agent or desk may override the Principal.** Research priority is not a trading decision.

## Status of the lab

| Today | Not today |
|---|---|
| Lawful public ingest into Market Memory | Managed-fund operations or investor reporting |
| Thesis / skeptic / backtest / paper-ledger research | Autonomous order generation |
| US Market Pulse briefs (read-only) | Live execution, wallets, signing |
| Versioned risk **config** (live hard-gated off) | Deterministic risk *service* as an operational gate |
| Coordinator-run improvement queue | Multi-desk concurrent implementation |
| Phase 5a desk-tier boundaries (docs + CI + skeletons) | Telegram send, desk runners |
| Phase 5b Polygon + HL structure ingest (IMP-010) | Paid data beyond Polygon env key; order endpoints |
| Phase 5c quant factor library (IMP-011) | Desk runners (5d); Telegram (5e); live path |

Paper trading exists as a **shadow ledger bound to theses**. It is not Execution. Opening paper still requires Skeptic pass, invalidation, and max loss. Enabling paper for a thesis, or enabling live later, is a Principal act.

## Mandatory decision pipeline

No skipped gates. A Quant `RESEARCH_PRIORITY` verdict is triage, not permission to trade.

```text
Data → Research desk → Quant → Skeptic → Risk → Principal
```

Research desk is Crypto / Equities & Post-IPO / Macro & Cross-Asset as applicable. No skipped gates. After Principal: paper trading only when authorised; constrained Execution & Fund Ops only when separately authorised (future-only).

| Gate | Question the gate answers | What it is not |
|---|---|---|
| Data & Market Memory Desk | Was this knowable, lawful, and durable at `as_of_knowledge`? | A thesis or ranking |
| Research desk | What is the falsifiable claim, catalyst, and invalidation? | A size, allocation, or order |
| Quant & Market Structure Desk | Relative-value / reclaim / structure triage with one verdict + reason code | An “active call,” buy, sell, or size |
| Independent Skeptic | Does the claim survive leakage, crowding, stale data, already-priced narrative? | Authorship of the thesis |
| Risk (independent veto) | Is progression unsafe on concentration, liquidity, leverage, freshness, policy? | A new thesis |
| Principal | Mandate, budget, promotion, paper/live enablement, material approval | Delegable to any desk |
| Paper (when authorised) | Shadow expression with invalidation + max loss | Live execution |
| Future execution (when separately authorised) | Submit only Risk-allowed, Principal-enabled intents | Interpretation or invention of the decision |

## Desk reporting template

Each desk reports **only** the fields below. No repeated status spam, commentary-only snapshots, or duplicated watchlist reports. A desk that has nothing new files **no report**.

| Field | Meaning |
|---|---|
| **New evidence** | Observation ids / source + `as_of_knowledge`. Empty if none. |
| **Artifact completed** | Path of the finished artifact, or none. |
| **Verdict or decision** | Desk-legal vocabulary only (see each charter). Blank if no decision. |
| **Reason** | Short reason or reason code. |
| **Risk / DQ warning** | Freshness, coverage, contradiction, liquidity, or policy warning. |
| **Dependency or blocker** | True blocker only (missing data, failed gate, waiting on Principal). |
| **Next queued item** | The single next item on [improvement-queue.md](improvement-queue.md) for this desk. |

Chief of Staff compiles a daily ops digest from these fields. Escalation to Principal is limited to **true blockers** or **completed PRs** ready for material review.

---

## Principal

**Mandate.** Human CIO. Sole authority for the investment mandate; capital and risk budget; strategy promotion; external capital, legal, and paid-data contracts; enabling paper or live execution; and final approval of material decisions.

**May**

- Lock or change `config/universe.yaml` membership and `in_universe` / `watch_only` partitions.
- Change `config/risk/environments/live.yaml` only via the `principal-review` path.
- Halt (`config/halt.flag` / halt runbook); own treasury (hardware wallet, never on a server).
- Authorise a specific thesis to paper, or separately authorise live later.
- Appoint desk owners; reject or return any desk output.

**Must not**

- Place treasury keys on servers or in git.
- Delegate a Principal-only gate to an agent or desk.

**Artifacts.** Mandate notes; promotion-decision records; halt; labelled live-config PRs.

**Owner.** Human Principal. No agent stands in.

---

## Chief of Staff / Hive Coordinator (Don)

**Mandate.** Own the **operating system**, not investment opinions. Keep one improvement queue, one accountable owner per item, and **one active implementation item** (`IN_PROGRESS`).

**May**

- Assign desks and owners; park or split work; refuse duplicate research.
- Enforce reusable artifacts (templates, queue cards, briefs, provenance records).
- Run DoD / `check-lifecycle`; open research and docs PRs; run `lab migrate` / `lab ingest` / `lab thesis` / `lab skeptic` / `lab backtest` / `lab paper` as Coordinator.
- Compile the daily ops digest from desk reports.
- Escalate only true blockers or completed PRs.

**Must not**

- Hold or inject trading credentials.
- Promote to live; waive Skeptic; invent Quant verdicts; override Principal.
- Let two implementation items sit in `IN_PROGRESS`.
- File commentary-only status in place of a desk report.

**Artifacts.** [improvement-queue.md](improvement-queue.md); daily ops digest; lifecycle check results.

**Owner.** Don.

---

## Data & Market Memory Desk

**Mandate.** Trusted information infrastructure: lawful ingest; raw-payload durability; provenance, timestamps, source quality, dedup, and contradictions; schemas, retrieval, and point-in-time reproducibility; data-quality alerts and source health.

**May**

- Ingest public / ToS-compliant feeds into Market Memory (`hl_info` only for Hyperliquid).
- Write source inventory, schema, and provenance records; flag stale, missing, duplicate, or contradictory observations.
- Own `as_of_knowledge` lockstep with `ingested_at` (never `published_at` / `market_time` as “what we knew”).

**Must not**

- Create theses, rank opportunities, size, or access execution / wallets / signing.
- Scrape in violation of ToS or call user-private info types.
- Silently “fix” history; soft-delete never removes audit rows.

**Artifacts.** Data-quality report; source inventory; schema and provenance records.

**Exists today.** `packages/memory`, `packages/ingest`, `packages/provenance`, `packages/common`, `packages/source_health`, `apps/ingest-worker`, `config/ingest.yaml`, `config/instruments/perps.yaml`, `docs/runbooks/ingest.md`, `docs/runbooks/source-health.md`. PIT query: `lab what-did-we-know`. Source health: `lab data source-health`.

**Gap.** Equity and on-chain feeds are not ingest (equities are briefing/watchlist only); contradiction workflows are schema-level (`observation_link`), not an operating cadence. Standing DQ / source-health generator is IMP-003 (**DONE** #33). Pulse source hardening (Stooq/FRED clients) is IMP-004 (**DONE** #34).

---

## Crypto Desk

**Mandate.** Digital-asset research, initially Hyperliquid market structure: spot/perp structure, funding, open interest, basis, liquidations, flows, on-chain; crypto catalysts and regimes; verified sector/protocol research; source-linked crypto research cards.

**May**

- Author crypto thesis cards from Market Memory evidence and named public sources.
- Contribute crypto context to Market Pulse (facts, not allocation).
- Propose tests and fixture backtests on crypto instruments in the locked universe.

**Must not**

- Call a trade, allocate capital, or access account / wallet / execution endpoints.
- Treat Quant `RESEARCH_PRIORITY` or universe `in_universe` membership as an order.
- Author and Skeptic-approve the same thesis.

**Artifacts.** Crypto thesis card (`templates/crypto-thesis-card.md`; IMP-007 DONE #37); crypto market-pulse contribution.

**Exists today.** HL public `/info` ingest (BTC, ETH, UNI, AAVE perps); generic `templates/thesis.md` + dedicated `templates/crypto-thesis-card.md`; `research/` workspaces; queue cards under `research/queue/` (e.g. QUANT-20260917, UNIVERSE-20260917). UNI/AAVE/ETH are watch-only for thesis-priority membership; BTC remains the crypto in-universe name in `config/universe.yaml` (Principal membership language — not a Quant Board verdict).

**Gap.** No on-chain ingest; no funding/OI/basis desk product with a standing cadence; live HL refresh can be rate-limited (DQ, not a trading signal). Dedicated crypto thesis-card template is IMP-007 (**DONE** #37).

---

## Equities & Post-IPO Desk

**Mandate.** Equity, thematic, and post-IPO research: filings, earnings, guidance, peers, lock-ups, dilution, liquidity, event calendars; post-IPO underperformance and reclaim screens; relative-value; distinguish genuine recovery vs bounce.

**Hard screen rule.** A beaten-down IPO is **not** a candidate just because it is down. A reclaim / relative-value candidate needs a verified catalyst, benchmark-relative context, liquidity review, and a falsifiable invalidation.

**May**

- Author equity thesis cards and post-IPO reclaim screens from named sources.
- Maintain event calendars and peer maps for names in the locked equity watchlist.

**Must not**

- Call a trade or size. Treat a drawdown as a thesis.
- Invent catalysts, skip liquidity, or skip invalidation.
- Access execution. Author and approve the same thesis.

**Artifacts.** Equity thesis card (`templates/equities-thesis-card.md`; IMP-007 DONE #37); post-IPO reclaim screen (`lab equities reclaim-screen`; IMP-006).

**Exists today.** Equity names on `config/universe.yaml` as Phase 3 briefing / future equity-feed watchlist (not Hyperliquid); queue cards (UNIVERSE call cards, WATCHLIST-DD, EXPECTATIONS scorecard); generic thesis template plus dedicated `templates/equities-thesis-card.md`; screen-only Post-IPO / reclaim universe `config/equities/post_ipo_reclaim.yaml` (not membership).

**Gap.** No equity-feed ingest into Market Memory; no filings/earnings pipeline. Dedicated equity thesis-card template is IMP-007 (**DONE** #37). Post-IPO reclaim screen product is IMP-006 (**DONE** #36). Do not confuse yfinance/TV one-off queue scrapes with durable Market Memory.

---

## Macro & Cross-Asset Desk

**Mandate.** Rates, USD, energy, commodities, vol, indices, liquidity; US pre-market / open / close context; event calendars; cross-asset divergences; regimes that reframe crypto and equity signals.

**May**

- Produce the US Market Pulse brief and cross-asset regime notes from memory + configured macro sources.
- Flag divergences and calendar risk that change how other desks should read a signal.

**Must not**

- Turn macro into allocation, a trade, or a size.
- Alert without numeric thresholds (`config/briefing/alerts.yaml`).
- Execute, or treat missing FRED/live keys as a complete regime picture (`data_quality=partial` is a warning).

**Artifacts.** US Market Pulse brief; cross-asset regime note.

**Exists today.** `packages/briefing`, `apps/briefing-worker`, `briefs/` (dated output gitignored), `config/briefing/*`, `config/schedules/market-pulse.yaml`, `docs/runbooks/market-pulse.md`. Macro live fetchers are opt-in and degrade without keys.

**Gap.** No standing cross-asset **regime note** distinct from Pulse (explicitly deferred on IMP-002). US Market Pulse vertical slice is IMP-002 (**DONE** #32): pre-market brief DoD on the existing Phase 3 Pulse substrate. Pulse source hardening is IMP-004 (**DONE** #34).

---

## Quant & Market Structure Desk

**Mandate.** Disciplined reviewer and opportunity triage. Runs the Quant Review Board (IMP-001 **DONE** #31). Reviews structure, benchmarks, peer-relative context, liquidity, and data quality. Screens post-IPO reclaim and relative-value candidates. Distinguishes true executable arbitrage from non-arb divergence. Issues **one verdict + reason code per instrument**.

**Allowed verdicts (only)**

`RESEARCH_PRIORITY` | `MONITOR` | `DEFER` | `REJECT` | `INSUFFICIENT_DATA`

**Forbidden language (desk outputs, board, cards)**

“active call,” “make,” “buy,” “sell,” “high confidence.”

**Language rule.** Label work a **relative-value / reclaim candidate** unless executable-arbitrage criteria are fully met. Universe file `in_universe` / `watch_only` is **Principal membership language**, not a Quant verdict. Do not copy those strings into Quant Board artifacts.

**May**

- Challenge research desks on structure, benchmark, liquidity, and DQ.
- Produce the daily Quant Review Board and instrument-level Quant Cards (`lab quant-review`; IMP-001 DONE).

**Must not**

- Call a trade, size, allocate, or access execution.
- Skip Data → Research → Quant → Skeptic → Risk → Principal.
- Use forbidden language or treat `RESEARCH_PRIORITY` as permission to paper or live.

**Artifacts.** Daily Quant Review Board; instrument-level Quant Cards.

**Exists today.** Ad-hoc queue packs (`research/queue/QUANT-20260917-active-calls.md` — historical filename; membership vocabulary after IMP-005) and builder, universe shortlists, fail-pair / expectations scorecards. Fixture backtest harness (`packages/backtest`) is evaluation infrastructure, not the Board.

**Gap.** Board generator exists (IMP-001 DONE). Locked-membership RESEARCH_PRIORITY pass is IMP-008. Remaining: Quant pack rewrite (templates / pack workflow — still a Gap). Post-IPO reclaim **screen product** is Equities desk IMP-006 (uses Quant closed verdicts; does not rewrite the Board). Dedicated crypto/equity thesis-card templates are IMP-007 (**DONE** #37). Do not treat membership (`in_universe`) as a Quant verdict.

---

## Independent Skeptic

**Mandate.** Invalidate research. Check leakage, false causality, crowding, duplicate beta, stale data, liquidity, and already-priced narratives. Every thesis needs one **observable** invalidation. Approve, reject, or return. This is the independent review office — not a research-authoring desk.

**May**

- Open and record skeptic reviews (`pass` | `revise` | `reject`).
- Fail look-ahead / leakage; demand fixes; keep rejected theses as learning records.
- **FAIL return:** `revise` sends the thesis back to `in_research`.
- **FAIL archive:** `reject` is terminal (`rejected`); workspace stays queryable.

**Must not**

- Author and approve the same thesis (**no self-approve**).
- Approve risk, waive own review, or access live keys.
- Skip invalidation quality.
- Convert a FAIL archive into a silent reopen (new intent required).

**Artifact.** `skeptic-review.md` (template: `templates/skeptic-review.md`).

**Exists today.** `lab skeptic`, `packages/research_kit`, lifecycle checker, queue skeptic reviews (e.g. WATCHLIST-DD personal skeptic, UNIVERSE call-cards skeptic).

**Gap.** Desk independence is a process rule, not a separate deploy unit. Coordinator must not assign the thesis author as sole skeptic of record.

---

## Risk (independent veto)

**Mandate.** Concentration by economic idea, correlation, liquidity, drawdown, leverage, data freshness, scenario risk. Deterministic risk-policy **config**. Blocks unsafe progression. Paper-trade proposals only after research + Skeptic clearance (and only when the Principal has authorised paper). Independent veto: **a BLOCK is terminal** until Principal override (Principal cannot be bypassed by the proposing desk; **no self-approve**).

**May**

- Explain `rule_id` + `config_version` from versioned config.
- Produce risk-review and portfolio-exposure artifacts.
- Veto progression that violates policy, freshness, or concentration.

**Must not**

- Create a thesis; change risk limits autonomously; approve own exceptions.
- Call an LLM at decision time; submit orders; silently edit `live.yaml`.
- Treat config defaults as a running risk **service** (the service is a Phase 0 stub).

**Artifacts.** `risk-review.md`; portfolio exposure report.

**Exists today.** `config/risk/defaults.yaml` and `config/risk/environments/{sim,paper,live}.yaml` (`live_trading_enabled: false`); CODEOWNERS + `risk-config-guard.yml` on live yaml; halt runbook. `packages/risk` and `apps/risk-service` are **stubs**.

**Gap.** No operational risk service; no `risk-review.md` template; no portfolio exposure report; no idea-level concentration engine. Do not implement the risk service in Phase 4.

---

## Execution & Fund Ops — FUTURE ONLY

**Not operational until the Principal separately activates each surface.** Dormant stubs must stay dormant. This is one future-only cell with two sub-functions; neither is a live desk today.

### Execution (future)

Submit only Risk-allowed, Principal-enabled `OrderIntent`s. Maintain order-state, recon, fills, slippage, incidents. Restricted credentials (API/agent wallet in live env only). No treasury-wallet authority. Halt checked before every order.

**Must not (now and later)**

- Invent, interpret, or modify investment decisions.
- Run inside research workers; sign without a Risk id; bypass halt; touch treasury.
- Exist as an enabled path while `live_trading_enabled` is false.

**Exists today (dormant).** `packages/execution`, `apps/execution-service` (Phase 0 stubs — no wallet, signing, or submission). Paper ledger (`packages/paper`) is **not** Execution.

### Fund Ops (future)

**Not operational.** There is no fund, no external capital, and no investor-reporting duty.

**Future mandate (when legal approval exists).** Immutable ledger; P&L and recon; tax; investor reporting only after legal approval; operational incidents.

**Must not (now).** Represent the lab as a managed product; produce investor reports; move capital.

**Exists today.** Nothing. Paper P&L on the shadow ledger is a research record, not fund accounting.

**Gap.** Entire Execution & Fund Ops surface. Do not fill it in a research or docs PR.

---

## Paper Ledger (Tier 7)

**Mandate.** Shadow expression of a thesis that already passed Skeptic and is not Risk-BLOCKED. Invalidation + max loss are mandatory. This is a **lab control**, not Execution.

**May**

- Open/close paper rows via `lab paper` when Principal has authorised paper for that thesis.
- Record fills/marks on the shadow ledger.

**Must not**

- Hold live keys or import `mm_execution`.
- Open without Skeptic `pass`, invalidation, and max loss.
- Treat a Risk BLOCK as allow (terminal without Principal override).
- Skip to live.

**Exists today.** `packages/paper`, `lab paper`. See [docs/runbooks/paper-trade.md](../docs/runbooks/paper-trade.md).

---

## Adjacent cells (not numbered delivery tiers)

| Cell | Status | Notes |
|---|---|---|
| Macro & Cross-Asset / Briefing | Operating Pulse desk | Not in Tier 0–7; still cannot allocate or execute |
| Delivery | Phase 5e; `packages/delivery` skeleton only | No Telegram send, no schedules, no secrets in 5a |
| Unicorn | Later; research-class stub (`packages/unicorn`) | Must not auto-promote to paper/live |
| Dashboard | Later; read-only stub (`apps/dashboard`) | Must not mutate trading state |

---

## Capability map (repo → desk)

| Capability / artifact | Desk | State |
|---|---|---|
| Market Memory (Postgres models, PIT, object pointers) | Data & Market Memory Desk | Exists |
| Ingest worker + `hl_info` (mids, funding, OI, candles, liquidations when public) | Data & Market Memory Desk | Exists (crypto perps in universe) |
| Provenance / claim hash / stale flags | Data & Market Memory Desk | Exists (package); standing DQ report is IMP-003 (`lab data source-health`) |
| `lab data source-health` / `ops/reports/source-health/` | Data & Market Memory Desk | IMP-003 / IMP-004 |
| `config/ingest.yaml`, `config/instruments/perps.yaml` | Data & Market Memory Desk | Exists |
| Equity names on `config/universe.yaml` | Equities & Post-IPO Desk (watchlist) + Data & Market Memory Desk (future feed) | Membership exists; **no equity ingest** |
| `lab equities reclaim-screen` / `config/equities/post_ipo_reclaim.yaml` / `research/screens/post-ipo-reclaim/` | Equities & Post-IPO Desk | IMP-006 DONE (screen-only; not membership) |
| `lab thesis` / `templates/{intent,thesis,crypto-thesis-card,equities-thesis-card,research-plan,evidence-links}` / `research/YYYY/` | Crypto Desk / Equities & Post-IPO Desk / Macro & Cross-Asset Desk | Exists (IMP-007 desk cards + generic spine) |
| `research/queue/` cards | Research desks + Quant & Market Structure Desk (ad-hoc) | Exists; not the Board |
| Market Pulse preopen/close/alert-check | Macro & Cross-Asset Desk | Exists (Phase 3) |
| `config/briefing/macro.yaml`, calendar, divergences, alerts | Macro & Cross-Asset Desk | Exists; live macro opt-in |
| Quant pack builder under `research/queue/quant-20260917/` | Quant & Market Structure Desk | Ad-hoc pack; **not** Quant Review Board |
| `templates/skeptic-review.md`, `lab skeptic`, queue skeptic reviews | Independent Skeptic | Exists |
| `config/risk/*`, live.yaml guard, halt | Risk (independent veto) | Config exists; **service stub** |
| `packages/backtest`, `lab backtest` | Quant / Research evaluation | Exists (fixtures, `params_hash`, `available_at`) |
| `packages/paper`, `lab paper` | Principal-gated paper (lab control) | Exists; not Execution |
| `packages/execution`, `apps/execution-service` | Execution & Fund Ops (Execution) | **Dormant stub — future only** |
| `packages/risk`, `apps/risk-service` | Risk (future service) | **Stub — do not treat as live gate** |
| Fund ledger / tax / investor reporting | Execution & Fund Ops (Fund Ops) | **Absent — future only** |
| `packages/desks` (`mm_desks.crypto` / `mm_desks.equities`) | Crypto Desk / Equities & Post-IPO Desk | **5a skeleton** — no runners, no adapters |
| `packages/quant` | Quant & Market Structure Desk | **5a skeleton** — no factor implementations |
| `packages/delivery` | Delivery (5e) | **5a skeleton** — no Telegram send |
| `packages/unicorn`, `apps/dashboard` | Adjacent / later | Stubs |

### Missing desk boundaries (exists vs gap)

1. **Hive roles ≠ desks.** AGENTS.md names Principal, Coordinator, Intel, Research, Skeptic, Briefing, Risk, Paper, Execution, Unicorn. Phase 5a added numbered tiers 0–7 and import-boundary skeletons (`packages/desks`, `packages/quant`, `packages/delivery`). Phase 5b Polygon + HL structure ingest lives in `mm_ingest`. Full desk runners and Telegram send are **not** this phase.
2. **Quant Board is a named desk product (IMP-001 DONE).** Queue packs remain historical evidence, not the Board. Forbidden language stays in force for Quant artifacts. Principal membership keys are `in_universe` / `watch_only` (IMP-005); do not treat membership as a recommendation.
3. **Skeptic and Risk independence is procedural.** Same repo, no separate credential domain for Skeptic. Risk veto is config + future service, not an implemented gate on paper open beyond lifecycle DoD.
4. **Paper ≠ Execution.** Shadow ledger is live in Phase 4; Execution remains future-only.
5. **Data desk does not cover equities or on-chain.** Those are research/watchlist gaps, not silent ingest.
6. **No Execution & Fund Ops surface.** Do not imply AUM, investors, a management company, or an order path.
7. **Single-threaded implementation.** Chief of Staff owns that rule; desks must not start parallel implementation items.

## Related documents

- Permissions / tiers: [AGENTS.md](../AGENTS.md)
- Desk boundaries runbook: [docs/runbooks/desks.md](../docs/runbooks/desks.md)
- Desk/delivery ADR: [ADR/0002-desk-delivery-architecture.md](../ADR/0002-desk-delivery-architecture.md)
- Philosophy and hive roles: [docs/founding-brief.md](../docs/founding-brief.md)
- Artifact DoD: [docs/research-lifecycle.md](../docs/research-lifecycle.md)
- Security / halt / live.yaml: [docs/security-model.md](../docs/security-model.md)
- Decision rights: [decision-rights.md](decision-rights.md)
- Improvement queue: [improvement-queue.md](improvement-queue.md)
- Post-IPO / reclaim screen: [docs/runbooks/post-ipo-reclaim.md](../docs/runbooks/post-ipo-reclaim.md)
