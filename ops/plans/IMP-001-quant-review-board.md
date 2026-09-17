# PLAN — IMP-001 Quant Review Board

**Report status:** PR READY  
**Owner:** Don/cloud  
**Scope:** read-only research artifacts + `lab quant-review`. No orders, wallets, live keys, or strategy promotion.

## Why

Watchlist review was collapsing into call generation. The Principal wants a **decision board**: what is unusual, what is missing, what would have to change before a thesis pack. Not MAKE, not sizing, not ARBITRAGE-by-metaphor.

## Reuse (do not invent a trading stack)

- Artifact write path: `mm_research_kit` (git is human-review source).
- Data-quality vocabulary: `ok | partial | stale | contradicted | rejected` (same as briefing/memory).
- Knowledge clock: `as_of_knowledge` lockstep with ingest/read time; never gate on `published_at` / `market_time`.
- Optional overlay: QUANT-20260917 CSVs for names that overlap the review universe (BTC, ETH, NVDA).
- Optional memory overlay: `what_did_we_know` for locked HL perps (BTC, ETH, UNI, AAVE) — evidence links only.
- Optional `research_run` (`kind=scan`) index when DB is on; `--no-db` always works.

## Universe

Locked ingest/thesis membership stays in `config/universe.yaml` (unchanged).

Review-board input is `config/quant_review_universe.yaml`, transcribed from the Principal-approved TradingView screenshots (crypto `USDC.P` list + cross-asset/US list). No popularity adds. Symbol normalization is explicit in that file.

## Engine

`lab quant-review --fixture … --no-db`

1. Load universe + snapshot (fixture and/or overlays).
2. Apply tracks that are relevant per name (A structure, B relative-value, C post-IPO, D executable arb).
3. Write one Quant Card per name and the dated board markdown.
4. Language gate on all rendered output.
5. Cap `RESEARCH_PRIORITY` at 3.

## Promotion (MONITOR → RESEARCH_PRIORITY)

All required: fresh attributable data; defined benchmark/peers; specific anomaly; overlooked reason; catalyst/trigger; single falsifiable invalidation; acceptable liquidity; no unaddressed duplicate-beta/DQ warning; Independent Skeptic review **required** (checklist field = pending, never a faked pass).

`RESEARCH_PRIORITY` = queue a deeper thesis pack. Never paper/live.

## Language

- Relative-value ≠ arbitrage. Word `ARBITRAGE` only if Track D is complete (two venues, same/convertible exposure, gross spread, all costs, fill size/liquidity, latency/ops risk, positive net). Else `UNEXECUTABLE_ARB` or `RELATIVE_VALUE`.
- Reclaim ≠ one-day bounce.
- Forbidden in output: MAKE, active-call language, confidence-as-verdict, trade sizing, order language.

## Tests

See `tests/unit/test_quant_review.py` and `tests/unit/test_quant_review_cli.py`.

## Non-goals

IMP-002 (US Market Pulse), QUANT pack rewrite (IMP-003), ingest-universe expansion, Unicorn auto-score, risk/execution services.
