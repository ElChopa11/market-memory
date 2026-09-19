# PLAN — IMP-039 Candidate strategy intake + Quant validation studies

**Report status:** READY (validation studies parked; this PR lands the intake specs only). Evening append 2026-09-19: rules 8–12 + `INTAKE_ONLY` param lock.
**Owner:** Quant  
**Scope:** Principal 2026-09-19 candidate shelf under `research/candidates/`. Owner QUANT. Status `INTAKE_ONLY` / HYPOTHESIS. No sizing. No scan-gate. Quant validation studies stay READY — not `IN_PROGRESS`. IMP-024 keeps the implementation slot.

## Why

Retail video / Substack / Reddit slogans arrived as strategy “ideas” without sample, window, instrument set, cost model, or split. The lab had no shelf that is *not* a thesis, *not* a Quant Board, and *not* a watchlist scan-gate. IMP-033 locked the review list; it must not become the promotion path. #60 already used **IMP-034** for KRX ticker resolutions + `licence_verdict`; this shelf is **IMP-039**.

## Outcome

- Queue: IMP-034 DONE (#60). IMP-022 DONE (#62). IMP-024 stays `IN_PROGRESS`. IMP-039 **READY** (studies not started). OPEN incidents (SCHED-001, BRIEF-TAG, SRC-STOOQ-404) untouched. `IN_PROGRESS` count **1** (EDGAR).
- `research/candidates/` with intake rules 1–12, C-001 / C-002 / C-003 (md + yaml), `failures/` archive, `research/studies/` deliverable path (empty).
- `config/candidates/{C-001,C-002,C-003,desk}.yaml` — proposed params committed; `status: INTAKE_ONLY`; `results: []`.
- Each card restates the claim or REJECT the slogan. Params `N,X,Y,Z,M` ATR locked. Payoff shape explicit. Provenance `n=unknown` hypothesis weight.
- Paper / fixture harness stubs (`packages/backtest` `buy_hold` / `threshold`) cited; **no** candidate strategy implemented.
- No `live.yaml` / signing / wallets / Redis / universe or watchlist edits / PLAYBOOK idea emission.
- FRED / licence / KRX work from #60/#62 is unchanged.

## Tests

- `tests/unit/test_imp039_candidates.py`
- Existing #62 queue tests left intact (IMP-024 single `IN_PROGRESS`)

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. Paper only. Ask before network/keys/order deps.

## Non-goals

Executing the validation studies in this PR. Live trading. Sizing. Scan-gate promotion. Closing OPEN incidents. Auto-merge. Gate waiver. Implementing C-001/C-002/C-003 as harness strategies. Taking the IMP-024 slot.

## Rollback

Revert this PR. `research/candidates/` disappears. IMP-034 (#60), IMP-022 DONE (#62), and IMP-024 IN_PROGRESS remain on main. No live path exists to unwind.
