# IC Gate 1 follow-up — Principal FIX ORDER (2026-09-19)

| Field | Value |
|---|---|
| **Artifact** | `research/base-rates/phase1-2026-09-19.md` |
| **IC review** | [`phase1-2026-09-19-ic-attack.md`](phase1-2026-09-19-ic-attack.md) (#79) |
| **Standing** | PAPER. No Telegram. No group send. No universe promotion. No C-00x compute. |

## IC verdict distinction (quoted; do not soften FAIL)

IC Gate 1 (2026-09-19) remains **FAIL** as the methodology-build gate for strategies. Do not soften FAIL.

Tables are usable as a **descriptive coin-flip mixture** under **PROVISIONAL** equity history.

The pooled ~33% is **NOT** a strategy hurdle.

FIX 1 and FIX 2 do **not** flip FAIL → REVISE or PASS. Remaining attacks stay open or queued.

## Disposition

| Attack | This PR | Notes |
|---|---|---|
| **5** (pooled vs per-instrument) | **FIX 1** | Every candidate measured against **its own** instrument's unconditional 1R:2R bracket (and later trend-up if used). Pooled figure labelled **descriptive mixture only** everywhere it appears. |
| **A8** (mean headlines) | **FIX 2** | Three-line summary and unconditional forward-return headlines lead with **median**, mean alongside. Regenerating the report prints medians first. |
| **A9** (equities absent) | **CLOSED stale** | On-box equity panel landed in [#81](https://github.com/ElChopa11/market-memory/pull/81). Equity rates stay **PROVISIONAL** (2-year cap). Attack 1 (walk-forward / single-regime) is a different item and stays deferred. |
| **3** (tie/timeout denominator) | queued | After Sunday dry run unless the dry run changes priority. `IMP-052`. |
| **2** (survivorship label) | queued | After dry run; report-level first. PIT universe = Intel; queue not block. `IMP-053`. |
| **6** (clip/funding) | **DEFER** | Needs Intel depth (ADV/spread/funding distribution at clip). Cost: Intel research, not a report relabel. `IMP-054`. |
| **1** (walk-forward / demeaned null) | **DEFER** | Research sprint. Cost: multi-regime folds + null redesign; not a banner fix. `IMP-055`. |
| **4, A7, A10** | not this order | Principal ordered cheapest/most consequential first (5 + A8). |

Cards C-001 / C-002 / C-003 stay `INTAKE_ONLY` / HYPOTHESIS. **DO NOT SIZE.**
