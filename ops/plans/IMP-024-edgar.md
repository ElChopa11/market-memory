# PLAN — IMP-024 Wire SEC EDGAR (filings / IPO / lockups; CBRS+SPCX)

**Report status:** IN_PROGRESS (this PR).  
**Owner:** Intel (adapter + store) / Research (filings use)  
**Scope:** `data.sec.gov` + Archives adapter, typed filing/lockup/8-K 2.02 observations, CBRS+SPCX from stored 424B4. Paper only. Treasury.gov is IMP-035.

## Why

`config/watchlist/monitor.yaml` already records Intel-confirmed CBRS/SPCX lockup formulas. There was no EDGAR adapter or store, so filings stayed config-only.

## Outcome

- Queue: IMP-022 DONE (#60). This item the only implementation thread. OPEN incidents untouched.
- `licence_verdict: ok_gov` on `edgar` (free, no key). Declared User-Agent. ≤10 rps.
- Typed observations: `edgar_filing`, `lockup_extract`, `confirmed_earnings` (8-K item 2.02). `file_date` is not the knowledge clock.
- CBRS + SPCX lockup confirmed from stored prospectus text (staged; not flat 180d). `observation_id` `edgar-CBRS-424b4-20260513` / `edgar-SPCX-424b4-20260611` + `claim_hash`.
- Missing / 403 → `unavailable` + `error_class`. No `api.nasdaq.com`. No Yahoo RSS. No invented filing text.
- CLI: `lab ingest --fixture tests/fixtures/edgar/cbrs-spcx-lockup.json --no-db` and `lab data edgar --fixture PATH --no-db`. `--no-db` = ELIGIBLE only.

## Tests

- `tests/unit/test_imp024_edgar.py`
- `tests/unit/test_imp024_queue.py`

## Gates kept

`live_trading_enabled: false`. No signing. No secrets. No Treasury.gov. No IMP-023/025/035.

## Rollback

Revert this PR. Lockup formulas remain in `monitor.yaml`. No live path to unwind.
