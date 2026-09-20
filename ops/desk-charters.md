# Desk charters

Market Memory is a **private research lab**, not a managed fund and not an autonomous trading system. These charters encode a hedge-fund-style desk model for how work is owned **today** (Phase 5a: desk boundaries over Phase 4 backtest + paper/shadow ledger). They do not raise external capital, enable live trading, or authorise any desk to place orders.

**Canonical desk names (Principal lock, Phase 6c-1 + 6c-2)** — use `mm_common.naming` / [`config/desks/naming.yaml`](../config/desks/naming.yaml). Exactly **five** publishing desks:

| Desk | Slug | Notes |
|---|---|---|
| Intel (Market Intelligence) | `intel` | Ingest + flow + macro + Pulse sleeves |
| Research (Investment Research) | `research` | Crypto + equities + chart sleeves (retired 3a/3b desks). Chart sleeve is librarian, not renderer, not retriever. |
| Quant | `quant` | Closed verdict set; not a call |
| IC/Risk (Investment Committee & Risk) | `ic_risk` | Two **gates** (Skeptic + Risk), not two desks |
| Ops | `ops` | Queue, pack assemble, delivery. Don/Coord orchestrates — not a sixth desk |

Principal, Paper Ledger, and Execution & Fund Ops remain cells / gates, not publishing desks.

### Delivery tiers (gates 0–7) vs desks

Principal lock for permissions. Publishing roster is the five desks above. Runbook: [docs/runbooks/desks.md](../docs/runbooks/desks.md). ADR: [ADR/0002-desk-delivery-architecture.md](../ADR/0002-desk-delivery-architecture.md), [ADR/0007-phase6c1-desk-roster.md](../ADR/0007-phase6c1-desk-roster.md).

| Tier | Cell | Desk / sleeve | Package |
|---|---|---|---|
| 0 | Principal | Principal (human; no package) | — |
| 1 | Ops | Ops (`mm_desks.ops`); Coord/Don is orchestration only | `apps/lab-cli` |
| 2 | Intel | Intel (Market Intelligence) | `packages/ingest` + `mm_desks.intel` (flow/macro sleeves) |
| 3a | Crypto sleeve | Research (not a desk) | `mm_desks.crypto` helper |
| 3b | Equities sleeve | Research (not a desk) | `mm_desks.equities` helper |
| 4 | Quant | Quant | `packages/quant` |
| 5 | Skeptic gate | IC/Risk | `mm_desks.skeptic` helper |
| 6 | Risk gate | IC/Risk | `packages/risk` + `mm_desks.risk` helper |
| 7 | Paper Ledger | Lab control (not a publishing desk) | `packages/paper` |

**Not a numbered tier in 5a:** Macro & Cross-Asset (Pulse still operates), Unicorn, Execution & Fund Ops (future-only), Delivery/Telegram (`packages/delivery` skeleton; **send is 5e**).

**Hard rules**

- **No self-approve.** Authoring desk ≠ Skeptic of record ≠ Risk allow ≠ Principal override for the same thesis.
- **Skeptic FAIL return:** verdict `revise` → status `in_research`. Authoring desk fixes; independent Skeptic re-reviews.
- **Skeptic FAIL archive:** verdict `reject` → status `rejected` (terminal learning record). Revival requires a **new intent**.
- **Risk BLOCK is terminal** without Principal override. The proposing desk cannot lift a BLOCK.
- Pipeline is not skippable: `Intel → 3a/3b → Quant → Skeptic → Risk → Principal → Paper`.

Hive roles in [AGENTS.md](../AGENTS.md) remain the permission constitution. This file maps those roles onto desks, names artifacts, and forbids skipped gates. Decision tables live in [decision-rights.md](decision-rights.md). Work is queued in [improvement-queue.md](improvement-queue.md). **Read before a round:** Principal-locked knowledge base [`config/knowledge/README.md`](../config/knowledge/README.md) (priors / failure modes / house lessons). A prior never triggers or sizes.

**No agent or desk may override the Principal.** Research priority is not a trading decision.

## Status of the lab

| Today | Not today |
|---|---|
| Lawful public ingest into Market Memory | Managed-fund operations or investor reporting |
| Thesis / skeptic / backtest / paper-ledger research | Autonomous order generation |
| US Market Pulse briefs (read-only) | Live execution, wallets, signing |
| Versioned risk **config** (live hard-gated off) | Deterministic risk *service* as an operational gate |
| Coordinator-run improvement queue | Multi-desk concurrent implementation |
| Phase 5a desk-tier boundaries (docs + CI + skeletons) | (historical row; 5d/5e landed later) |
| Phase 5b Polygon + HL structure ingest (IMP-010) | Paid data beyond Polygon env key; order endpoints |
| Phase 5c quant factor library (IMP-011) | live path |
| Phase 5d desk runners (IMP-012) | live path; risk/execution *services* |
| Phase 5e Telegram delivery (IMP-013) | Phase 6 mesh; live path |
| Phase 6a PG NOTIFY mesh (IMP-014) | Redis; live path |
| Phase 6b flow/macro/regime (IMP-015) | live path |
| Phase 6c per-desk Telegram + PLAYBOOK (IMP-016 DONE #47) | live path; live LLM HTTP |
| Phase 6c-1 five-desk roster (IMP-018 DONE #49) | live path |
| Phase 6c-2 naming layer (IMP-019 DONE #51) | live path |
| Phase 6c-4 watchlist monitor (IMP-020 DONE #52) | live path |
| Principal review list `config/watchlist/monitor.yaml` (IMP-033) | universe promotion; guessing unresolved tickers |
| Phase 6c-5 Ops-owned delivery expansion (IMP-021 DONE #53) | live path |
| Phase 6d listings / IPO screen (IMP-017 DONE #54) | live path; 6f decay-watch |
| Phase 6e pack scorecards + queue hygiene (IMP-030 DONE #55) | live path; auto-merge |
| Phase 6f prompt-hash decay watch (IMP-031) | live path; auto-disable; gate waiver |

Paper trading exists as a **shadow ledger bound to theses**. It is not Execution. Opening paper still requires Skeptic pass, invalidation, and max loss. Enabling paper for a thesis, or enabling live later, is a Principal act.

## Mandatory decision pipeline

No skipped gates. A Quant `RESEARCH_PRIORITY` verdict is triage, not permission to trade.

```text
Intel → Research → Quant → IC/Risk (Skeptic gate then Risk gate) → Ops pack
```

Research desk owns crypto / equities / chart sleeves. Chart files TV snapshot references + structured levels from markup; it does not render, retrieve, or publish. Intel owns flow / macro / Pulse sleeves. No skipped gates. After Principal: paper trading only when authorised; constrained Execution & Fund Ops only when separately authorised (future-only).

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

## Research sleeves (crypto / equities / chart) — not publishing desks

As of Phase 6c-1 these are **Research** sleeves. Historical "Crypto Desk" / "Equities & Post-IPO Desk" titles are retired.

### Crypto sleeve

**Mandate.** Digital-asset research, initially Hyperliquid market structure: spot/perp structure, funding, open interest, basis, liquidations, flows, on-chain; crypto catalysts and regimes; verified sector/protocol research; source-linked crypto research cards.

**May**

- Author crypto thesis cards from Market Memory evidence and named public sources.
- Contribute crypto context to Market Pulse (facts, not allocation).
- Propose tests and fixture backtests on crypto instruments in the locked universe.

**Must not**

- Call a trade, allocate capital, or access account / wallet / execution endpoints.
- Treat Quant `RESEARCH_PRIORITY` or universe `in_universe` membership as an order.
- Author and Skeptic-approve the same thesis.
- Publish an idea without stating watchlist tier (`universe` / `monitor` / `blocked`). Monitor-tier ideas are UNSIZED. Blocked / unresolved names are never ideas.

**Artifacts.** Crypto thesis card (`templates/crypto-thesis-card.md`; IMP-007 DONE #37); crypto market-pulse contribution.

**Exists today.** HL public `/info` ingest (BTC, ETH, UNI, AAVE perps); generic `templates/thesis.md` + dedicated `templates/crypto-thesis-card.md`; `research/` workspaces; queue cards under `research/queue/` (e.g. QUANT-20260917, UNIVERSE-20260917). UNI/AAVE/ETH are watch-only for thesis-priority membership; BTC remains the crypto in-universe name in `config/universe.yaml` (Principal membership language — not a Quant Board verdict).

**Gap.** No on-chain ingest; no funding/OI/basis desk product with a standing cadence; live HL refresh can be rate-limited (DQ, not a trading signal). Dedicated crypto thesis-card template is IMP-007 (**DONE** #37).

---

### Equities sleeve

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

### Chart sleeve (librarian — not renderer, not retriever)

**Mandate.** File Principal TradingView snapshot references and structured levels. Chart is a **librarian**, not a renderer, not a retriever. Not a sixth publishing desk. Principal 2026-09-20 FINAL is **OPTION A** (IMP-056 BACKLOG behind Monday 2026-09-21 unattended Sydney Morning). `render_png` retires in that later PR; this charter is the scope now.

**Who does what**

- **Principal** marks the chart in TradingView (entry/SL/TP via position tool; levels; measured moves) and snapshots (camera/Alt+S) → hosted TV URL.
- **Chart** receives the snapshot reference + structured levels and files them. Chart does **not** retrieve, browse, log in, or capture.
- **Ops** delivers via `lab deliver`. Chart never publishes.

**May**

- File a `CHART_ARTIFACT` under `briefs/` with: `tv_snapshot_url` (as given, never constructed); `instrument` (exchange-qualified: `HL:ZEC`, `HL:XMR`, `HL:ETH`…); `timeframe` (as in the chart header); `as_of` (snapshot timestamp from the header); levels as **structured fields not pixels** (entry, stop, target(s), horizontals); `linked_thesis_id` (if Quant marked; else null); `content_hash`.
- Transcribe levels **from markup only** — what the snapshot shows.
- Record `"ambiguous"` and ask when markup is unclear.
- File a BLOCKED-tier snapshot (e.g. CASHCAT) for **reference only**.
- State watchlist tier (`universe` / `monitor` / `blocked`) on **every** artifact. Watchlists = `config/watchlist/monitor.yaml` only.

**Must not**

- Retrieve, browse, log in to, or capture TradingView. No automated / signed-in TV. No browser automation. No screen capture.
- Render (no `render_png` replacement, no mplfinance, no server-side PNG). Implementation of the retirement stays IMP-056 after Monday fire — do not start it while that item is BACKLOG.
- Read price action, infer, add, or adjust levels. Never estimate. Ambiguous → `"ambiguous"` and ask.
- Hold Telegram credentials, webhooks, or publish (direct or otherwise). Hand to Ops.
- Carry a trade view, direction, sizing, or commentary.
- Carry an idea or size on a BLOCKED name (CASHCAT is tier BLOCKED: snapshot may be filed for reference but never carries an idea/size).
- Construct `tv_snapshot_url`. Widen the watchlist. Promote membership. Occupy `IN_PROGRESS`.

**Artifacts.** `CHART_ARTIFACT` under `briefs/` (snapshot URL + structured levels + `content_hash`). Ops-owned delivery.

**Exists today.** PLAYBOOK `CHART_ARTIFACT` + `render_png` on main via IMP-016 (#47) — **historical path**. OPTION A supersedes retrieval framing and option B. Retirement of `render_png` is IMP-056 BACKLOG (not this charter PR's code).

**Gap.** Bind `CHART_ARTIFACT` to OPTION A fields and retire `render_png` after Monday 2026-09-21 unattended Sydney Morning (IMP-056). Paper only. No Telegram. No C-00x.

---

## Intel sleeves (flow / macro / Pulse) — not publishing desks

As of Phase 6c-1 these are **Intel** sleeves. Historical "Macro & Cross-Asset Desk" as a publishing desk is retired.

### Watchlist resolution + lockup watch (Intel-owned)

**Mandate.** Own `config/watchlist/monitor.yaml` ticker resolution and the EDGAR lockup stub. The file is the Principal-locked complete review list (2026-09-19). Research runs `lab watchlist scan`; Intel does not author theses.

**May**

- Resolve exchange-qualified ids into the monitor table.
- Record EDGAR-confirmed lockup formulas (do **not** assume a flat 180 days). IMP-024 persists those formulas as Memory observations (`as_of_knowledge` + 424B4 provenance).
- Mark Ambiguous names `unresolved` until Principal resolves them. IMP-034 resolved SAMSUN→`KRX:005930` and KOSDA→`KRX:KQ11`. Do not invent a CHIPI listing; CHIPIUSD display is Principal-confirmed as `HL:CHIP`.

**Must not**

- Guess an unresolved ticker.
- Promote a monitor name into `config/universe.yaml` `in_universe`.
- Author a thesis or Quant verdict.

**Artifacts.** `config/watchlist/monitor.yaml`; `config/listings/watchlist_new_listings.yaml` (NEW_LISTING / lockup feed).

## Macro & Cross-Asset (Intel sleeve)

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

## IC/Risk gates (Skeptic + Risk) — not two desks

Skeptic and Risk remain **independent gates** inside `ic_risk`. They are not publishing desks.

## Independent Skeptic (gate)

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

## Risk (gate; independent veto)

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
| Delivery | Phase 5e Telegram (`lab deliver`) | Secrets env-only; no Phase 6 mesh |
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
| `CHART_ARTIFACT` (TV snapshot URL + structured levels) | Research chart sleeve (librarian, not renderer, not retriever) | Scope locked IMP-056 BACKLOG; `render_png` retirement not until after Monday 2026-09-21 unattended Sydney Morning |
| `packages/desks` (`mm_desks` runners) | Crypto / Equities / Intel assemble / Skeptic / Risk / Coord | **5d runners** — fixture `--no-send`; Coord pack |
| `packages/quant` | Quant & Market Structure Desk | **IMP-011 factor library**; 5d Quant desk calls it |
| `packages/delivery` | Delivery (5e) | **Telegram Bot API** — dry-run default; live send operator-gated |
| `packages/risk` (`mm_risk.evaluate`) | Risk (independent veto) | **5d library allow/block** — `apps/risk-service` stays stub |
| `packages/unicorn`, `apps/dashboard` | Adjacent / later | Stubs |

### Missing desk boundaries (exists vs gap)

1. **Hive roles ≠ desks.** AGENTS.md names Principal, Coordinator, Intel, Research, Skeptic, Briefing, Risk, Paper, Execution, Unicorn. Phase 5a added numbered tiers 0–7 and import-boundary skeletons. Phase 5b Polygon + HL structure ingest lives in `mm_ingest`. Phase 5c factor math lives in `mm_quant`. Phase 5d desk runners live in `mm_desks`. Telegram send is **Phase 5e** (`mm_delivery`). Multi-channel mesh is **Phase 6a**. PLAYBOOK + per-desk fan-out is **Phase 6c**.
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
- Desk knowledge base (read before a round): [config/knowledge/README.md](../config/knowledge/README.md)
- Post-IPO / reclaim screen: [docs/runbooks/post-ipo-reclaim.md](../docs/runbooks/post-ipo-reclaim.md)
