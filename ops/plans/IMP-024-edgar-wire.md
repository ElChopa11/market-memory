# PLAN — IMP-024 SEC EDGAR wire (CBRS + SPCX lockup)

**Report status:** IN_PROGRESS (this PR).  
**Owner:** Intel (adapter + store) / Research (filings use)  
**Scope:** Free official EDGAR adapter. Persist Intel-confirmed CBRS/SPCX lockup formulas as observations. `--no-db` = ELIGIBLE only. Paper only.

## Why

Principal FREE SOURCE PRIORITY #2 after FRED. Intel already recorded prospectus dates on `config/watchlist/monitor.yaml`. There was no adapter or Memory row. Do **not** assume a flat 180 days.

## Outcome

- Queue: IMP-022 DONE (run_id `fred-fullstack-20260919-101938-aest`). This item the only implementation thread. SRC-STOOQ-404 stays OPEN. SRC-FRED-MISSING-ENV is CLOSED (`--no-db` remains ELIGIBLE only).
- Adapter `mm_ingest.edgar` on `data.sec.gov` submissions + Archives URLs. Declared User-Agent. Budget well under 10 rps. No API key.
- `licence_verdict: ok_gov` (accurate closed-set). Alias `redistributable_official` → `ok_gov` per 15 U.S.C. § 78ll.
- CBRS + SPCX lockup observations: `as_of_knowledge = ingested_at`; `file_date` is not the knowledge clock; provenance is the 424B4 URL; `assume_180d: false`.
- `lab ingest --fixture tests/fixtures/edgar/cbrs_spcx_lockup.json --no-db` → `edgar_stack.closure=ELIGIBLE`. Postgres `run_edgar_stack(..., session=...)` persists via `persist_envelopes`. Never auto-CLOSED.
- Missing feed → unavailable. Flat-180d payload refused. No `api.nasdaq.com`. No Yahoo. Treasury.gov is IMP-035.

## Tests

- `tests/unit/test_imp024_edgar.py`
- `tests/unit/test_imp024_queue.py`
- `tests/adversarial/test_imp024_edgar_point_in_time.py`
- Optional Postgres persist via existing `ingest_from_fixture` / `run_edgar_stack`

## Gates kept

`live_trading_enabled: false`. No signing. No paid deps. No secrets in git.

## Non-goals

Closing SRC-STOOQ-404. Street consensus. 8-K 2.02 earnings product (path exists on submissions; not a calendar). Treasury/CB calendars (IMP-035). `live.yaml`. `--no-db` never CLOSED.

## Rollback

Revert this PR. Monitor.yaml lockup_watch stays on main. No live path to unwind.
