# Decision rights

Who may **propose**, **challenge**, **veto**, and **approve**. This is the control plane for Market Memory as a private research lab. It does not create a fund, enable execution, or let any desk override the Principal.

Desk mandates: [desk-charters.md](desk-charters.md). Queue: [improvement-queue.md](improvement-queue.md). Permissions constitution: [AGENTS.md](../AGENTS.md).

## Hard rule — Principal-only gates

Only the human Principal / CIO may **approve** (or enable) the following. No agent, desk, or Coordinator vote substitutes:

| Gate | Includes |
|---|---|
| Investment mandate | What the lab may research; universe membership lock; strategy family in/out |
| Capital and risk budget | Size caps, max loss policy, environment budgets; `live.yaml` contents |
| Strategy promotion | Thesis → paper authorisation; paper → live (later); playbook promotion into templates/config |
| External capital / legal / paid-data | Raising, counsel, vendor contracts, paid feeds, commercial terms |
| Enable paper trading | Turning paper on for a thesis (shadow ledger open is still subject to Skeptic + invalidation + max loss) |
| Enable live execution | Separately from paper; includes any path that submits orders or installs trading credentials |
| Final approval of material decisions | Anything that changes mandate, risk, universe lock, desk model, or live gates |

**No desk may override Principal.** A Quant verdict, Skeptic `pass`, or Risk allow is never a trade and never a mandate change.

## How to read the table

| Column | Meaning |
|---|---|
| **Propose** | May draft the change or request |
| **Challenge** | May object with a recorded reason (Skeptic, Quant, Risk, Data DQ) |
| **Veto** | May **block progression** on that gate (independent veto stands until Principal handles it) |
| **Approve** | Binding yes. Empty or “Principal only” means the Principal is the only approver |

RACI shorthand on the same rows: **R** does the work, **A** is accountable (matches Approve unless noted), **C** is consulted, **I** is informed.

---

## Decision table

### Mandate, capital, legal

| Decision | Propose | Challenge | Veto | Approve | Notes |
|---|---|---|---|---|---|
| Investment mandate | Principal; Chief of Staff may table a question | Any desk (recorded) | Principal | **Principal only** | Encoded in universe lock + these ops docs |
| Capital & risk budget | Principal; Risk may draft options | Risk; Skeptic (research implications) | Principal; Risk (unsafe draft) | **Principal only** | Risk cannot raise limits on its own |
| External capital / legal entity / investors | Principal | Chief of Staff (ops burden) | Principal | **Principal only** | Execution & Fund Ops is future-only; default is **no** |
| Paid data / vendor contracts | Data desk; research desks (need) | Data (ToS, quality, cost); Risk | Principal | **Principal only** | No paid feed lands without Principal; lawful/ToS still required |
| Halt / resume new orders (when execution exists) | Principal; Coordinator under halt runbook | Risk | Principal | **Principal only** | `config/halt.flag`; Execution must stop new orders |

### Data

| Decision | Propose | Challenge | Veto | Approve | Notes |
|---|---|---|---|---|---|
| New public / ToS-compliant source | Data & Market Memory | Skeptic (leakage); research desks (fitness) | Data (unlawful/ToS); Principal (paid or material) | Data for public ingest in existing class; **Principal** if paid, private, or mandate-expanding | Intel/ingest: `hl_info` only for Hyperliquid |
| Schema / provenance / PIT contract change | Data | Quant; Skeptic | Data (breaks PIT); Principal if material | Data (non-material); **Principal** if it changes what “we knew at T” means | `as_of_knowledge` stays lockstep with `ingested_at` |
| DQ incident (stale, gap, contradiction) | Data | Consuming desk | Data may halt **use** of the bad slice | Data owns the DQ record; Principal if it blocks a promotion | Warnings appear in the desk report field |

### Research and promotion

| Decision | Propose | Challenge | Veto | Approve | Notes |
|---|---|---|---|---|---|
| New thesis / research card | Crypto / Equities / Macro (as applicable) | Quant; Skeptic; Data (if evidence is unfit) | Skeptic (`reject` / `revise`); Risk (unsafe expression) | Desk owner for **draft**; promotion is later gates | Cannot skip Data evidence rules |
| Quant verdict (per instrument) | Quant & Market Structure | Research desk (facts); Data (DQ) | Quant may `REJECT` / `DEFER` / `INSUFFICIENT_DATA` | Quant (verdict only) | Verdicts: `RESEARCH_PRIORITY` \| `MONITOR` \| `DEFER` \| `REJECT` \| `INSUFFICIENT_DATA`. Not a trade |
| Skeptic review | Chief of Staff assigns independent reviewer | Authoring desk (on `revise` items) | Skeptic | Skeptic (`pass` / `revise` / `reject`) | Author ≠ sole skeptic of record |
| Research promotion (artifact stage: in_research → in_skeptic → …) | Authoring desk; Coordinator (DoD) | Skeptic; Quant; Risk | Lifecycle checker; Skeptic; Risk | Coordinator for mechanical DoD; **Principal** for paper/live enablement | `scripts/check-lifecycle.sh` is not waivable |
| Playbook / template / strategy family into default config | Research desk; Quant; Coordinator | Skeptic; Risk | Risk; Principal | **Principal only** (material) | No hot-patch of live logic |

### Risk, paper, live

| Decision | Propose | Challenge | Veto | Approve | Notes |
|---|---|---|---|---|---|
| Risk-policy config (non-live) | Risk | Quant; research desks | Risk (unsafe); Principal | Principal for material; Risk drafts | Deterministic config; no LLM at decision time |
| Risk exception | Proposing desk | Risk; Skeptic | **Risk** | **Principal only** | Risk **never approves its own exception** |
| `config/risk/environments/live.yaml` | Principal | Risk | Principal | **Principal only** + `principal-review` label | CODEOWNERS `@ElChopa11`; agents must not edit |
| Paper enablement (thesis may open on shadow ledger) | Authoring desk (after Skeptic `pass`) | Risk; Quant | Risk; Skeptic (if `pass` withdrawn) | **Principal only** | Still requires invalidation + max loss (`lab paper open`) |
| Live execution enablement | Principal | Risk; Coordinator (ops) | Risk; Principal | **Principal only**, **separate** from paper | Execution desk is future-only until this fires |
| Order submission (future) | Execution (from Risk-allowed intent) | Risk (pre-trade) | Halt; Risk; Principal | Risk allow **and** Principal promotion record | Execution cannot invent/modify the decision |

### Operating system

| Decision | Propose | Challenge | Veto | Approve | Notes |
|---|---|---|---|---|---|
| Improvement-queue intake / desk assignment | Any desk; Chief of Staff | Owning desk | Chief of Staff (duplicate, out of scope, second `IN_PROGRESS`) | Chief of Staff (assignment); Principal if mandate-level | One accountable owner per item |
| Which item is `IN_PROGRESS` | Chief of Staff | Owning desk | Chief of Staff | Chief of Staff | **Single-threaded implementation** |
| Merge to `main` — ordinary research/docs | Author; Coordinator | Reviewer; Skeptic (research) | CI; lifecycle checker; CODEOWNERS | Coordinator (ordinary); **Principal** if material | Material = mandate, risk, universe lock, desk model, live gates, paid data |
| Merge to `main` — material / live.yaml / universe lock | Coordinator prepares PR | Risk; Skeptic; Data | Principal; CI guards | **Principal only** | Do not merge this class without Principal |
| Desk charter / decision-rights change | Chief of Staff | Any desk | Principal | **Principal only** | This file and `desk-charters.md` |
| Daily ops digest | Chief of Staff compiles | Desks (corrections of fact) | — | Chief of Staff publishes | Escalates only true blockers or completed PRs |

---

## Pipeline vs rights

```text
Data → Research desk → Quant → Skeptic → Risk → Principal
```

Research desk = Crypto / Equities & Post-IPO / Macro & Cross-Asset as applicable. Data proposes facts; Quant issues a verdict + reason code (not a trade); Independent Skeptic is `pass` | `revise` | `reject`; Risk holds independent veto (no autonomous limit change). After Principal: paper only if authorised; Execution & Fund Ops only if separately authorised (future-only).

**Research priority ≠ trading decision.** `RESEARCH_PRIORITY` does not authorise paper or live.

## Forbidden substitutions

| Anti-pattern | Rule |
|---|---|
| Desk ships a “call” or “buy/sell” | Quant forbidden language; research may not call a trade |
| Author skeptic-reviews own thesis as sole reviewer | Skeptic charter |
| Coordinator waives Skeptic or lifecycle | AGENTS.md; this table |
| Risk raises its own limits or approves its own exception | Principal-only |
| Agent enables paper or live “to test a fill” | Principal-only; live remains hard-gated |
| Execution interprets or rewrites an intent | Future Execution charter |
| Second item moved to `IN_PROGRESS` | Chief of Staff operating rule |
| Ops docs treated as live logic | [ops/README.md](README.md) |

## Role ↔ desk (quick map)

| AGENTS.md role | Desk in this model |
|---|---|
| Principal | Principal (Tier 0) |
| Coordinator | Chief of Staff / Hive Coordinator (Don) (Tier 1) |
| Intel / ingest | Data & Market Memory Desk (Tier 2) |
| Research | Crypto Desk (3a); Equities & Post-IPO Desk (3b); Macro & Cross-Asset Desk (not numbered) |
| Quant | Quant & Market Structure Desk (Tier 4) |
| Skeptic | Independent Skeptic (Tier 5) |
| Briefing | Macro & Cross-Asset Desk (Pulse) |
| Risk | Risk (independent veto) (Tier 6) |
| Paper | Lab control under Principal — Paper Ledger (Tier 7) |
| Execution | Execution & Fund Ops (**future only**) |
| Unicorn | Adjacent later cell; not a desk here |

## Tiers, FAIL, BLOCK, no self-approve

Canonical delivery tiers (Phase 5a): **0 Principal · 1 Ops/CoS · 2 Intel · 3a Crypto · 3b Equities · 4 Quant · 5 Skeptic · 6 Risk · 7 Paper Ledger**. See [desk-charters.md](desk-charters.md) and [AGENTS.md](../AGENTS.md).

| Event | Binding rule |
|---|---|
| Skeptic FAIL **return** (`revise`) | Thesis → `in_research`. Independent re-review. No self-approve. |
| Skeptic FAIL **archive** (`reject`) | Thesis → `rejected` (terminal learning record). New intent to revive. |
| Risk **BLOCK** | **Terminal.** No paper/live. Only Principal override. Proposing desk cannot lift it. |
| Self-approve | Fail the gate. Author ≠ Skeptic ≠ Risk allow ≠ Principal override |

Delivery (Telegram / schedules) is **Phase 5e**, not a 5a approve path.
