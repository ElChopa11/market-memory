# PLAN — IMP-022 FRED full-stack close

**Report status:** DONE (operator persist run_id `fred-fullstack-20260919-101938-aest`, 2026-09-19).
**Owner:** Intel (ingest) / Ops (env)  
**Scope:** Close `SRC-FRED-MISSING-ENV` with persist + provenance + published value. `--no-db` = ELIGIBLE only. Paper only.

## Why

The FRED adapter and Pulse slot already exist. The incident stayed OPEN until a persist `run_id` landed rows in Postgres and a published artifact with provenance. Principal 2026-09-19 made this the first free-source item.

## Outcome

- Queue: IMP-033 DONE (#59). IMP-034 licence schema DONE (#60). IMP-022 DONE. Next thread is IMP-024.
- `licence_verdict: ok_gov` on the FRED adapter. Standing redistribution rule in config.
- `lab ingest --fixture tests/fixtures/phase5b/fred_series.json --no-db` emits `fred_stack.closure=ELIGIBLE` with value + `claim_hash` provenance. Never `CLOSED`.
- Operator persist run_id `fred-fullstack-20260919-101938-aest`: postgres_attached=true, no_db=false, created_rows=5, Pulse US10Y=4.94, source-health fred=ok.
- `SRC-FRED-MISSING-ENV` is CLOSED on that cited run. Key never in git. Pack: `ops/reports/incident-closures/20260919-101938-aest-fred-fullstack-close.json`.

## Tests

- `tests/unit/test_imp034_watchlist_licence.py` (licence + FRED stack ELIGIBLE)
- `tests/unit/test_src_fred_queue_close.py` (CLOSED + IMP-024 single thread)
- Existing `test_fred_and_calendar_fixtures` / `test_lab_ingest_no_db_dry_run`

## Gates kept

`live_trading_enabled: false`. No signing. No secrets in git. No auto-close.

## Non-goals

Closing the incident on `--no-db`. ALFRED vintages (later). CBOE/S&P pre-approval series. Stooq scrape. Paid data. `live.yaml`.

## Rollback

Revert the queue close. `--no-db` remains ELIGIBLE only. Incident would return to OPEN until another persist `run_id`.