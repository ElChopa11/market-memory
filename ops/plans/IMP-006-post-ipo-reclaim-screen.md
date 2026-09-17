# PLAN — IMP-006 Post-IPO reclaim screen product

**Report status:** PR READY  
**Owner:** Don/Equities (Equities & Post-IPO Desk)  
**Scope:** read-only Post-IPO / reclaim **research triage screen** + `lab equities reclaim-screen`. No orders, wallets, live keys, Pulse/Stooq/FRED work, Principal membership expansion, or strategy promotion.

## Why

Desk charters name a post-IPO reclaim screen as an Equities artifact. Quant language rules (IMP-001) and membership vocabulary (IMP-005) are done. The Quant Board has a one-line Track C list; it is not a standing Equities desk product with provenance, freshness, and honest unavailable metrics. A beaten-down IPO is not a candidate just because it is down.

## Path choice

| Role | Path |
|---|---|
| DoD / canonical artifact | `research/screens/post-ipo-reclaim/YYYY-MM-DD.md` |
| Screen-only universe | `config/equities/post_ipo_reclaim.yaml` (`kind=post_ipo_reclaim_screen`, `status=screen_only`) |
| Engine | `packages/research_kit` → `mm_research_kit.post_ipo_reclaim` |
| Command | `lab equities reclaim-screen` |
| Template | `templates/post-ipo-reclaim-screen.md` |
| Runbook | `docs/runbooks/post-ipo-reclaim.md` |

This is **not** `config/universe.yaml` membership. Screen config is separate from `in_universe` / `watch_only`. Do not copy screen names into locked ingest/thesis membership.

Filename date is the screen date (`--screen-date` or snapshot `as_of_knowledge` UTC date).

## Universe (start small)

Seed candidates from names **already** on the Principal-approved Quant Review TV watchlist with a post-IPO / reclaim-relevant flag:

- `CRCL` — Quant Board Track C `post_ipo: true`
- `HOOD` — Quant-review TV equity used as CRCL peer

Context-only (relative-value denominators, not reclaim candidates): `QQQ`, `SPX`, `GLXY`.

Principal `in_universe` equities (`NVDA`, `AVGO`, `MSFT`, `META`, `JPM`, `XOM`) are **not** post-IPO reclaim candidates on this screen. Membership ticker sets stay unchanged.

## Engine

`lab equities reclaim-screen --fixture … --no-db`

1. Load screen-only universe + snapshot (same print/overlay schema as Quant Review; empty snapshot is honest `unavailable`).
2. Optional QUANT pack overlay for names that exist in the pack — never invent missing tickers.
3. Score each **candidate** only.
4. Write dated markdown + `.meta.json`.
5. Language gate on all rendered output (`mm_research_kit.quant_review.language`).

### Row contract

Each candidate row includes:

- instrument, as-of (`as_of_knowledge`)
- reclaim / relative metrics with **source + freshness**
- data quality: `fresh | stale | partial | unavailable`
- Quant verdict + reason code from the closed set  
  `RESEARCH_PRIORITY | MONITOR | DEFER | REJECT | INSUFFICIENT_DATA`  
  reason codes from IMP-001 `QuantReasonCode`

Missing last/chg/MDD/listing date → `unavailable` (not fabricated).

### Hard screen rule (charter)

Post-IPO underperformance without catalyst **and** a single invalidation → `DEFER` with `NO_CATALYST` / `THESIS_NOT_FALSIFIABLE`. Reclaim needs prior breakdown level, reclaim of that level, and hold ≥ 2 sessions. Cap `RESEARCH_PRIORITY` at 3. Independent Skeptic is required before any thesis pack (never claimed as pass).

### Footer

Informational / not a trading decision. Principal gate still required for anything beyond research.

## Reuse (do not fork a trading stack)

- Snapshot parser, overlays, reclaim observables: `mm_research_kit.quant_review`
- Language gate + closed verdicts/reason codes: IMP-001
- Artifact write: `mm_research_kit.artifacts.write_text`
- Knowledge clock: `as_of_knowledge` lockstep with fixture/read time; never `published_at` / `market_time`

## Tests

See `tests/unit/test_post_ipo_reclaim.py` and `tests/unit/test_post_ipo_reclaim_cli.py`.

Committed sample is a fixture run of the IMP-001 screenshot **subset** (same prints). No live paid data. No invented market prints.

## Non-goals

IMP-004 Pulse source hardening (#34 PARKED — do not continue). Stooq/FRED. Universe expansion. Quant Board rewrite. MAKE/buy/sell recommendations. Sizing. Execution. `live.yaml`. Secrets. Paid data. Telegram. ToS-violating scrapes. Filings/earnings ingest (still a Data-desk gap).

## Limitations

- No equity-feed ingest into Market Memory; prints are watchlist/fixture overlays.
- Listing/issuance dates are not in Memory → issuance context is `unavailable`.
- QUANT pack overlays cover Principal membership names, not CRCL/HOOD; drawdown vs reference high is `unavailable` on the committed sample.
- No lawful filings, lock-up, or dilution tape; `DILUTION_OR_LOCKUP_RISK` is a reason-code warning when the name is down, not a verified event.
