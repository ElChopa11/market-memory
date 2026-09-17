# Ops

Desk operating model for Market Memory as a **private research lab**. This tree is documentation and the single improvement queue. It is not live logic, not a fund offering, and not an execution path.

| Path | What it is |
|---|---|
| [desk-charters.md](desk-charters.md) | Desk mandates, forbidden actions, artifacts, pipeline, reporting template, capability map |
| [decision-rights.md](decision-rights.md) | Who proposes / challenges / vetoes / approves; Principal-only gates |
| [improvement-queue.md](improvement-queue.md) | Single continuous-improvement queue; every item has a desk and one accountable owner |

Hard constraints (same as [AGENTS.md](../AGENTS.md)):

- No trading credentials, signing, wallets, or `hl_trade` / `mm_execution` usage from this tree.
- Do not edit `config/risk/environments/live.yaml` from ops docs work.
- Quant Review Board (IMP-001) is **DONE** (#31). Do not rewrite the board in a Pulse PR.
- US Market Pulse vertical slice (IMP-002) is the active implementation item. Read-only; no execution.
- Execution & Fund Ops is **future-only** until the Principal separately activates it.
