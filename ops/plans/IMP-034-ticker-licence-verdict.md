# PLAN — IMP-034 Principal ticker resolutions + licence_verdict schema

**Report status:** DONE (this PR; FRED full-stack is IMP-022).  
**Owner:** Intel (tickers) / Ops (queue + licence schema)  
**Scope:** Apply Principal 2026-09-19 ticker resolutions. Record `licence_verdict` next to each adapter. Intake FREE SOURCE PRIORITY. Paper only.

## Why

IMP-033 (#59) locked `config/watchlist/monitor.yaml` with SAMSUN/KOSDA unresolved. Principal then resolved those two and locked a free-source order plus a standing redistribution rule that must live in config, not only docs.

## Outcome

- Queue: IMP-033 DONE (#59). IMP-034 done here. IMP-022 is the single IN_PROGRESS.
- SAMSUN → `KRX:005930` (Samsung Electronics, KRW). KOSDA → `KRX:KQ11` (KOSDAQ Composite, KRW).
- Unresolved set empty. HL:CHIP / HL:VVV / HL:PURR and NASDAQ:SPCX / NASDAQ:CBRS unchanged.
- `config/ingest.yaml` `licence.standing_rule` + `adapters.*.licence_verdict` closed set.
- FREE SOURCE PRIORITY ordered: FRED (022) → EDGAR (024) → treasury.gov (035) → Binance vision AU (023) → Yahoo retire (036) → Tiingo (037) → Finnhub terms (038).
- SRC-STOOQ-404 stays OPEN. SRC-FRED-MISSING-ENV stays OPEN (`--no-db` = ELIGIBLE only).

## Tests

- `tests/unit/test_imp034_watchlist_licence.py`
- `tests/unit/test_imp034_queue.py`
- Existing IMP-033 monitor tests updated for the two resolutions

## Gates kept

`live_trading_enabled: false`. No signing. No wallet. `--no-send`. No paid deps.

## Non-goals

Universe promotion. Closing OPEN incidents. Guessing other tickers. Live/signing/Redis.

## Rollback

Revert this PR. IMP-033 monitor file stays on main with SAMSUN/KOSDA unresolved. No live path exists to unwind.
