# ADR 0015 — licence_verdict next to each adapter

- **Status:** Accepted
- **Date:** 2026-09-19
- **Phase:** IMP-034 schema + IMP-022 FRED path. No live trading. No signing.

## Context

Source evaluation 2026-09-18 scored licences in a report. Principal 2026-09-19 locked a standing rule: sources whose terms prohibit redistribution may be used for internal computation but values must never appear in published artifacts. A doc-only verdict is not enough — operators need the chip next to the adapter.

## Decision

| Piece | Rule |
|---|---|
| Location | `config/ingest.yaml` `licence:` + `adapters.<id>.licence_verdict` (also mirrored on nested adapter blocks) |
| Closed set | `ok_gov` \| `ok_attr` \| `restricted` \| `prohibited` \| `pending_terms` \| `missing` |
| Publish | Only `ok_gov` and `ok_attr` may place a value in a published artifact |
| Restricted / prohibited / pending | Internal compute OK (if used at all); published value is redacted |
| Missing | Fail closed — treat as do-not-publish |
| Incident close | `OPEN` → `ELIGIBLE` → `CLOSED(cite run_id)` \| `RETIRED`. `--no-db` = ELIGIBLE only |

## Consequences

- CoinGecko stays `restricted` (no raw redistrib). FRED is `ok_gov`. Yahoo is `prohibited`. Finnhub is `pending_terms`.
- `mm_ingest.licence.filter_published_values` strips forbidden values before an artifact is written.
- Queue helper accepts `ELIGIBLE` / `CLOSED` / `RETIRED` for incidents. `CLOSED` without a cited `run_id` fails hygiene.

## Not this ADR

Paid SKUs. Closing SRC-STOOQ-404. Wiring EDGAR/Treasury/Tiingo/Finnhub adapters. Universe promotion.
