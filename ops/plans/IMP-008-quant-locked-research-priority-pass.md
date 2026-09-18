# PLAN — IMP-008 Quant RESEARCH_PRIORITY pass (locked universe only)

**Report status:** DONE (#38)  
**Owner:** Don/Quant (Quant & Market Structure Desk)  
**As-of:** 2026-09-18 (Australia/Sydney, AEST)  
**Scope:** desk re-score of **locked membership** in `config/universe.yaml`. Screenshot/TV board (IMP-001) is not rewritten. No orders, wallets, live keys, paid data, universe expansion, or execution.

## Why

IMP-001 produced a Quant Review Board for a Principal-approved **screenshot/TV watchlist** (36 names). That board is not a RESEARCH_PRIORITY pass on the **locked ingest/thesis membership**. Principal asked Don to run a fresh Quant pass on the locked set only (as-of 2026-09-18 Sydney) and to close IMP-007 hygiene after thesis-card templates merged as #37.

Membership ≠ Quant verdict. in_universe names are not automatically RESEARCH_PRIORITY.

## Path choice

| Role | Path |
|---|---|
| Membership source of truth | `config/universe.yaml` (unchanged ticker set) |
| Locked review universe | `config/quant_review_locked_universe.yaml` (in_universe ∪ watch_only only) |
| Screenshot/TV universe | `config/quant_review_universe.yaml` (IMP-001; not this pass) |
| Desk re-score | `mm_research_kit.quant_review.locked_membership` |
| Command | `lab quant-review --locked-membership --no-db` |
| Artifact | `research/quant/2026-09-18/quant-review-board.md` + `cards/` |
| Prior board (start-from, do not rubber-stamp) | `research/quant/2026-09-17/` |

Do **not** promote `deferred_must_cut` names onto the board.

## Locked names (12)

- **in_universe:** BTC, NVDA, AVGO, MSFT, META, JPM, XOM
- **watch_only:** ETH, UNI, AAVE, SMH, XLF
- **excluded:** HYPE, SOL, XRP, ARB, NEAR, LINK, GLD, LLY

## Method

1. Start from the 2026-09-17 screenshot board for overlap names (BTC, ETH, NVDA) and **re-score**.
2. Factor Skeptic artifacts on main: expectations scorecard (PR #22), FAIL patches (PR #23), WATCHLIST-DD cut-review, call cards.
3. Factor source-health 2026-09-17: Stooq/FRED degraded; no equity ingest. Prefer `INSUFFICIENT_DATA` over invented conviction when tape is thin.
4. Factor SEC PR 2026-90 (2026-09-17, Innovation Exemption / tokenized NMS / permissioned AMM). UNI and AAVE may move to MONITOR or RESEARCH_PRIORITY **only if** a falsifiable desk hypothesis exists. No narrative auto-upgrade.
5. Every RESEARCH_PRIORITY name would need: falsifiable claim, invalidation, evidence refs, data-quality caveat. Prefer **zero** RESEARCH_PRIORITY over fake ones.
6. Language gate: no buy/sell/make/active call/high confidence/sizing/allocation/order intent.
7. Cap RESEARCH_PRIORITY at 3 (IMP-001). Independent Skeptic remains pending (never a faked pass).

This pass does **not** use screenshot-engine overlay `rel_short ≥ 8pp` as auto-MONITOR. QUANT rel is simple-diff, not alpha (Skeptic / QUANT honesty).

## Verdicts this pass

| Verdict | Count | Names |
|---|---:|---|
| RESEARCH_PRIORITY | 0 | none |
| MONITOR | 2 | ETH (BTC-beta watch), UNI (SEC PR 2026-90 mapping test) |
| DEFER | 6 | BTC, NVDA, JPM, AAVE, SMH, XLF |
| REJECT | 0 | none |
| INSUFFICIENT_DATA | 4 | AVGO, MSFT, META, XOM |

UNI MONITOR is a dated public-law event plus a falsifiable TSV/Uniswap citation test. It is **not** a fee-switch thesis and **not** a bounce thesis. AAVE stays DEFER: the LP dealer exemption does not fill a utilization baseline.

## Residual data gaps

- No equity-feed ingest; Stooq unavailable; FRED missing_env.
- QUANT pack overlays are 2026-09-16 (equities; META lag 2026-09-15) / 2026-09-17 (crypto) — cited as dated evidence, not 2026-09-18 prints.
- HL fundingHistory continuity, ETF flow series, Azure/ad extracts, NII gap test, crude strip, SMH holdings overlap %, Aave utilization baseline: still empty.
- Postgres / object store were unavailable on the last source-health report.

## Non-goals

Pulse / Stooq scrape workarounds. Paid data. Committing `FRED_API_KEY`. Universe expansion. Screenshot-board rewrite. Thesis-card template reopen (IMP-007 DONE #37). MAKE / investment-call recommendations. Sizing. Execution. `live.yaml`. Secrets. Telegram. Replacing `thesis.md`.

## Tests

See `tests/unit/test_imp008_locked_quant_pass.py` and CLI smoke in `tests/unit/test_quant_review_cli.py`.
