# ADR 0016 — SEC EDGAR adapter (IMP-024)

- **Status:** Accepted
- **Date:** 2026-09-19
- **Phase:** IMP-024 free-source #2 after FRED. No live trading. No signing. No API key.

## Context

Intel already recorded CBRS / SPCX lockup formulas on `config/watchlist/monitor.yaml` from 424B4 prospectuses. Those dates were config-only. Principal FREE SOURCE PRIORITY put EDGAR next after FRED. SEC `data.sec.gov` is free, official, and requires a declared User-Agent with a 10 rps fair-access cap. 15 U.S.C. § 78ll permits lawfully obtained EDGAR information to be used, resold, or redisseminated without restriction. The standing licence closed set already has `ok_gov` as the accurate chip (`redistributable_official` is an alias).

## Decision

| Piece | Rule |
|---|---|
| Hosts | `data.sec.gov` submissions JSON + `www.sec.gov/Archives/edgar/` URLs only |
| Auth | None. Declared User-Agent. No key. |
| Rate | Config budget well under 10 rps |
| Lockup | Persist Intel-confirmed prospectus **formulas**. Never a flat 180d. Refuse `assume_180d: true` |
| PIT | `as_of_knowledge = ingested_at`. `file_date` / `published_at` are not knowledge clocks |
| Closure | `--no-db` = ELIGIBLE only. CLOSED needs Postgres persist + cited `run_id` |
| Not adopted | `api.nasdaq.com`, Yahoo RSS, Street consensus |

## Consequences

- CBRS fail-closed blackout bound `2026-11-09` and SPCX `2027-06-12` become Memory observations with 424B4 provenance.
- Source-health lists `edgar` as optional; filing text is not copied into health reports.
- Treasury.gov remains IMP-035.

## Not this ADR

Paid filings vendors. Earnings-estimate calendars. Closing SRC-STOOQ-404. Auto-closing incidents (`--no-db` never CLOSED).
