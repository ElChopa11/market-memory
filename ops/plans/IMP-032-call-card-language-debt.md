# PLAN — IMP-032 Call-card language vs Quant SoT

**Report status:** DONE (#57).  
**Owner:** Ops (queue hygiene) / Quant (SoT vocabulary)  
**Scope:** Align `research/queue/UNIVERSE-20260917-call-cards.md` field-1 priority language with the locked-membership Quant Review Board 2026-09-18 (IMP-008 / #38). Quarantine stale HL dayNtl/OI stamps as appendix-only / **DO NOT SIZE**. No new names. No universe promotion. Paper only.

## Why

Lunch Money Research L2: UNIVERSE/call-cards still read as post-#11 revise / “conditional” packs. Quant Board 2026-09-18 is source of truth.

Mismatches:

| Names | Call-card (pre-IMP-032) | Quant SoT (#38) |
|---|---|---|
| BTC, NVDA, JPM | conditional / watch-only+conditional / earnings-watch | **DEFER** |
| AVGO, MSFT, META, XOM | conditional / earnings-gated / crude-gated | **INSUFFICIENT_DATA** |
| ETH, UNI | BTC-beta watch / deferred governance | **MONITOR** |
| AAVE, SMH, XLF | deferred / monitor-only appendix | **DEFER** (not Quant MONITOR) |

BTC body still treated HL dayNtl/OI as live-looking liquidity color. QUANT pack already quarantines those stamps; cards must too.

## Canonical vocabulary

Quant closed set only (IMP-001 / IMP-008): `RESEARCH_PRIORITY | MONITOR | DEFER | REJECT | INSUFFICIENT_DATA`.

Membership keys stay IMP-005: `in_universe` / `watch_only`. Theme roles (primary / satellite / appendix) are not Quant verdicts.

Forbidden as priority language: “conditional,” “active call,” buy, sell, MAKE, high confidence, sizing / order instruction. Historical pack **filename** `UNIVERSE-20260917-call-cards.md` is retained as an evidence id.

## Outcome

- Queue: IMP-031 DONE (#56). IMP-032 this thread. OPEN incidents untouched (SCHED-001, BRIEF-TAG-20260918, SRC-STOOQ-404, SRC-FRED-MISSING-ENV).
- Call-card field 1 matches Quant SoT per locked name. Zero RESEARCH_PRIORITY. Locked 12 names only.
- Stale HL dayNtl/OI live only in an appendix labelled **DO NOT SIZE** / DO NOT TREAT AS LIVE. Card bodies point at the appendix.
- Tests lock the mapping + HL quarantine + language gate subset + queue hygiene.
- `live.yaml` untouched. No signing, wallets, Redis, paid deps, universe promotion.

## Tests

- `tests/unit/test_imp032_call_card_language.py`
- Existing `tests/unit/test_phase6f_queue.py` / `test_phase6e_queue.py` updated so IMP-031 is DONE (#56)

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. Paper only. Ask before network/keys/order deps.

## Non-goals

Inventing new calls. Rewriting the Quant Board. Universe ticker expansion. `live.yaml`. Signing. Redis. Paid data. Closing OPEN incidents. Reopening IMP-005 membership keys. Execution. Pulse/Stooq scrape.

## Rollback

Revert this PR. Call-cards return to post-#11 / #23 prose. Quant Board 2026-09-18 stays on main. No live path exists to unwind.
