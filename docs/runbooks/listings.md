# Listings / IPO screen (Phase 6d / IMP-017)

Research (Investment Research) screen of upcoming IPOs / direct listings, a **separate** index add/delete/rebalance stream, post-listing tracking, and own-history base rates. **Not a sixth desk. Not a call. Not universe promotion.** Ops publishes the Telegram cut. Coord orchestrates and is **not** the publisher. IC/Risk gates still apply; listings cannot self-approve or open paper.

Naming: [`config/desks/naming.yaml`](../../config/desks/naming.yaml) sleeve `listings`. Publishing desk is still `research`. Desks: [desks.md](desks.md). Telegram: [telegram.md](telegram.md). Post-IPO reclaim (different product): [post-ipo-reclaim.md](post-ipo-reclaim.md).

## What operators can do

```bash
uv run lab listings scan --fixture tests/fixtures/phase6d/listing_day.json --no-send --out /tmp/listings
uv run lab listings scan --fixture tests/fixtures/phase6d/no_listing.json --no-send --repo-root .

# Ops-owned Telegram fan-out of that artifact (inherit content_hash; default --no-send)
uv run lab deliver listings --fixture tests/fixtures/phase6d/listing_day.json --no-send --out /tmp/listings
```

`--no-send` is the default. Same fixture twice → identical `content_hash`. Fixture path makes **zero LLM calls**. Pytest never hits live Telegram.

Writes under `--out` `research/listings/YYYY-MM-DD/`:

| File | Contents |
|---|---|
| `listings.md` | Human screen (deals, warning block, post-listing path, index events, provenance) |
| `listings.json` | Canonical run |
| `listings.sha256` | `content_hash` |

`lab deliver listings --out` also writes `briefs/YYYY-MM-DD/telegram-payload.json` (env **names** only; no token).

## Knowledge clock

`as_of_knowledge` lockstep with `ingested_at`. Future deals, filings, index events, and bars stay invisible. Missing pricing / float / borrow / depth stays **unavailable** (never invented). A missing listings feed degrades the run.

Base rates use our own Market Memory listing history. `n < n_min` (config `20`) → **no base-rate claim**.

## Quant / IC / PLAYBOOK

Closed Quant verdicts only (`RESEARCH_PRIORITY | MONITOR | DEFER | REJECT | INSUFFICIENT_DATA`). Listings **inherits** `trade_math_hash` when Quant/PLAYBOOK already computed it and does not invent R or size. `UNTRADEABLE_AT_SIZE` is observation only; Risk still blocks by `rule_id`. Skeptic + Risk remain required. Paper stays closed on this path.

Index events are a separate stream from IPO deals. Post-IPO reclaim screen remains `lab equities reclaim-screen`.

NEW_LISTING names on [`config/watchlist/monitor.yaml`](../../config/watchlist/monitor.yaml) (CBRS, SPCX as of 2026-09-19) route here, not through the general equities scan. Standing feed: [`config/listings/watchlist_new_listings.yaml`](../../config/listings/watchlist_new_listings.yaml). Ideas use the post-IPO framework (offer, day-1 VWAP, reclaim, listing base rates) — **not SMA200**. SMA200 renders `n/a (insufficient history: <n> bars)` when bars `<200`. Mandatory warning: days of history, float %, lockup proximity, borrow flag, spread/depth. `UNTRADEABLE_AT_SIZE` is observation only; Risk blocks by `rule_id`.

EDGAR lockups are confirmed formulas from a stored 424B4 (IMP-024), **not** a flat 180 days. Resolvable ids: `edgar-CBRS-424b4-20260513`, `edgar-SPCX-424b4-20260611`. Lockup inside horizon = Skeptic (gate 5) blackout. See [edgar.md](edgar.md).

## Not this phase

Scorecards (6e) live on `lab scorecard compare`. Decay-watch (6f). Universe promotion. Live/signing. Redis. Paid data. Live LLM HTTP. Closing OPEN incidents.
