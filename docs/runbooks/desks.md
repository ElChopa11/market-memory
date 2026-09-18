# Desk boundaries (Phase 5a)

Private research lab control plane. **Boundaries only.** This runbook does not enable ingest vendors, desk runners, Telegram, or live trading.

Canonical names and charters: [ops/desk-charters.md](../../ops/desk-charters.md). Permissions: [AGENTS.md](../../AGENTS.md). Architecture: [ADR/0002-desk-delivery-architecture.md](../../ADR/0002-desk-delivery-architecture.md). Decision rights: [ops/decision-rights.md](../../ops/decision-rights.md).

## Tiers

| Tier | Cell | May | Must not |
|---|---|---|---|
| 0 | Principal | Mandate, budget, promotion, halt, `live.yaml`, Risk-BLOCK override | Keys on servers; delegate Principal-only gates |
| 1 | Ops / CoS | Queue, DoD, `lab *`, PRs | Trading credentials; waive Skeptic; self-approve |
| 2 | Intel | Public ingest into Memory (`hl_info` + Polygon) | Opine (theses/verdicts); import `mm_research_kit` / `mm_desks` / `mm_quant` / `mm_delivery`; sign |
| 3a | Crypto | Crypto artifacts from Memory + named sources | Orders, sizing, `mm_execution`, self-Skeptic/Risk |
| 3b | Equities | Equity / post-IPO artifacts | Same as 3a; drawdown-as-thesis; Polygon client lives in `mm_ingest` |
| 4 | Quant | Closed verdict + reason code | Calls, sizing, skip pipeline |
| 5 | Skeptic | `pass` / FAIL return (`revise`) / FAIL archive (`reject`) | Author and approve the same thesis |
| 6 | Risk | Allow / **BLOCK** from versioned config | LLM at decision time; self-clear BLOCK; edit `live.yaml` silently |
| 7 | Paper Ledger | Shadow open/close with invalidation + max loss | Live keys; open on Risk BLOCK; Execution |

Macro Pulse, Unicorn, Execution & Fund Ops, and Delivery/Telegram are **not** numbered 5a tiers. Delivery send is **Phase 5e**.

## Escalation

```text
Intel → 3a|3b → Quant → Skeptic → Risk → Principal → Paper
```

| Event | Result |
|---|---|
| Skeptic FAIL return | `in_research` — fix and re-review |
| Skeptic FAIL archive | `rejected` — learning record; new intent to revive |
| Risk BLOCK | **Terminal** unless Principal override |
| Self-approve | Gate fail |

No desk overrides the Principal. No skipped gates.

## Import walls (CI)

`scripts/check_import_boundaries.py` (also a job in `.github/workflows/test.yml`):

- `packages/research_kit`, `packages/desks`, `packages/quant`, `packages/delivery` must not import `mm_execution` / `mm_execution_service` or signing / live-trade surfaces (`sign_l1_action`, `hl_trade`, `submit_order`, `private_key`).
- Intel `packages/ingest` must not import opine packages: `mm_research_kit`, `mm_desks`, `mm_quant`, `mm_delivery`.

## Skeletons (not runners)

| Path | Meaning in 5a |
|---|---|
| `packages/desks` | Crypto / Equities import wall only |
| `packages/quant` | Quant import wall; empty factor registry |
| `packages/delivery` | No-send stub; Telegram is 5e |
| `templates/output-contract.md` | Principal briefing contract |

Do **not** add factor math or a Telegram client in Phase 5b. Polygon + HL structure ingest: [polygon-hl-structure.md](polygon-hl-structure.md).

## Output contract

Principal-facing desk product copy uses [templates/output-contract.md](../../templates/output-contract.md). Trade ideas are **intent-only**. Writer hard rules are on that template.

## Gates kept

`live_trading_enabled: false`. `risk-config-guard`. `promote-gate`. Point-in-time law. Degrade-never-invent. No secrets in git.
