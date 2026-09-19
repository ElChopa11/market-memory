# PLAN — IMP-022 FRED full-stack close

**Report status:** DONE (#60). SRC-FRED-MISSING-ENV stays OPEN until a cited persist run_id.  
**Owner:** Intel (ingest) / Ops (env)  
**Scope:** Path toward closing `SRC-FRED-MISSING-ENV`: persist + provenance + published value. `--no-db` = ELIGIBLE only. Paper only.

## Why

The FRED adapter and Pulse slot already exist. The incident stays OPEN because `--no-db` and `missing_env` never landed rows in Postgres or a published artifact with provenance. Principal 2026-09-19 made this the first free-source item.

## Outcome

- Queue: IMP-033 DONE (#59). IMP-034 licence schema done. This item the only implementation thread.
- `licence_verdict: ok_gov` on the FRED adapter. Standing redistribution rule in config.
- `lab ingest --fixture tests/fixtures/phase5b/fred_series.json --no-db` emits `fred_stack.closure=ELIGIBLE` with value + `claim_hash` provenance. Never `CLOSED`.
- `run_fred_stack(..., session=...)` persists via existing `persist_envelopes` when Postgres is attached. Operator cites `run_id` to close the incident.
- `SRC-FRED-MISSING-ENV` stays OPEN until that cited run. Key never in git.

## Tests

- `tests/unit/test_imp034_watchlist_licence.py` (licence + FRED stack ELIGIBLE)
- Existing `test_fred_and_calendar_fixtures` / `test_lab_ingest_no_db_dry_run`

## Gates kept

`live_trading_enabled: false`. No signing. No secrets in git. No auto-close.

## Non-goals

Closing the incident on `--no-db`. ALFRED vintages (later). CBOE/S&P pre-approval series. Stooq scrape. Paid data. `live.yaml`.

## Rollback

Revert this PR. FRED adapter on main still degrades `missing_env`. Incident stays OPEN.
