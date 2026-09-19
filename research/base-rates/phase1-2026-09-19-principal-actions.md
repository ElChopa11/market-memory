# Principal actions on Phase-1 base rates — 2026-09-19

Standing record of Principal (Debo) actions on the Phase-1 instrument dump.
**Not** a Memory `run_id`. **Not** a desk product. **Not** a Telegram send. Paper only.
Do not invent `run_id`. Cite file paths.

This cloud VM does **not** have `POLYGON_API_KEY`. Equity bars were not fetched here.
Crypto tables live in [`phase1-2026-09-19.md`](phase1-2026-09-19.md) (13 names computed).
Continuity check is in `scripts/research/base_rates_phase1.py` (rules A/B VOID, C FLAG).
Re-run **on the box** (free-tier pace, **no** `--no-sleep`; monitor.yaml only — **no overlay fetch**;
`--refresh` so Polygon cache is `adjusted=true`):

```text
export POLYGON_API_KEY=...          # box env only; never commit
uv run python scripts/research/base_rates_phase1.py --refresh
# writes research/base-rates/phase1-<Sydney-date>.md
```

Monitor coverage stays authoritative. Do not fetch AVGO/MSFT/META/JPM/XOM/SMH/XLF
in this pass (quota reserved for SPCX/BMNR re-run).

---

## 1. VOID SPCX — ticker reuse / entity splice

| Field | Value |
|---|---|
| **Ticker** | SPCX (`NASDAQ:SPCX`) |
| **Intended entity** | Space Exploration Technologies Corp (SpaceX) |
| **Prior entity** | The SPAC and New Issue ETF (~$7M AUM, avg vol ~1.67K) |
| **Identity start** | `listed_on: 2026-06-11` (EDGAR 424B4 expected_pricing_date / prospectus_date; `config/listings/watchlist_new_listings.yaml`, `config/research/ticker_continuity.yaml`) |
| **Principal-cited tape** | 454 daily bars from 2024-09-19 (Polygon ticker-string splice) |
| **Principal-cited prints** | median 1-bar **exactly 0.000%**; vol **120.9%**; max 1-bar **+29.8%**; max 10-bar **+101.8%**; chop 10-bar max **+624%** |
| **Verdict** | **VOID** `suspected_ticker_reuse` under **rule A** (first bar 2024-09-19 precedes `listed_on` 2026-06-11). Likely also **rule B** (ETF ~$22 → SpaceX ~$150 sustained). Exclude from the void-excluded pool. Do not trim and keep. **Not** an N-sigma void. |
| **Code** | `mm_ingest.equities.continuity` (A listing-date **or** B 20/20 level-shift); `PolygonEquitiesAdapter.continuity_check`; daily aggs pin `adjusted=true` |

House lesson: resolving a ticker to an identifier does **not** prove the returned series belongs to one entity. See `config/knowledge/house-lessons.md`.

**Pooled 1R:2R without SPCX.** This VM cannot recompute the equity-inclusive pool (no Polygon key). The crypto-only pool in [`phase1-2026-09-19.md`](phase1-2026-09-19.md) never included SPCX: gross **32.4%** (5315 targets / 11113 stops); net **31.8%**. On-box re-run after A/B continuity must publish **both** pools (full vs void-excluded). Do not invent that number here.

**Robustness (headline, not a footnote).** Prior numbers: voids barely moved the headline (~32.9%→32.8% gross, ~32.4%→32.3% net). **The descriptive mixture holds regardless of how the continuity question resolves.** That is a strength of the continuity test; it is **not** a strategy hurdle.

---

## 2. LABEL THE 501-BAR CAP — Polygon 2-year free-tier history limit

This **IS** Polygon's **2-year free-tier history limit** (2024-09-19 → 2026-09-18 inclusive on the 2026-09-19 equity run). Not "looks like a window cap."

Consequences (also at the **top** of [`phase1-2026-09-19.md`](phase1-2026-09-19.md)):

- SMA200 needs 200 bars → equity regime signals start **~2025-07-09**.
- Equity base rates cover roughly **one year of usable signals in a single regime**.
- Every equity base rate is **PROVISIONAL** until more history exists.

**Do-not-interpret counts** on Principal's equity-inclusive run (29 computed names, **including** SPCX before void): trend-down **13/29**; chop **17/29**. Verify against regime tables on the box re-run (voiding SPCX changes the denominator). This VM's crypto-only included set: trend-down **1/13**; chop **1/13** (see the generated trend-filter section).

---

## 3. TREND-FILTER FINDING — permission filter; candidate queue

Trend-up conditioning does **not** raise the 1R:2R bracket hit rate; for several names it falls. Principal-cited equity drops (from the on-box Polygon run; not recomputed here):

| ticker | uncond long hit | trend-up long hit |
|---|---|---|
| NVDA | 35.2% | 27.2% |
| TSLA | 34.8% | 23.5% |
| HOOD | 40.1% | 23.7% |
| MSTR | 30.8% | 10.5% |

Crypto-only sample (this VM, generated tables): several trend-up 1-bar means are negative (UNIUSD, LTCUSD, PURR). VVVUSD trend-up long gross hit **47.3%** (n=200) is the interpretable outlier.

This undercuts the shared premise of C-001 / C-002 / C-003 (dip entries gated on a confirmed uptrend) **in this sample**. Do **not** conclude the strategies fail. Conclude the **permission filter does not carry edge on its own**. Any candidate that relies on it must beat **that instrument's own unconditional** 1R:2R bracket (and, if it uses a trend-up permission filter, **that instrument's own trend-up** bracket). The pooled ~33% is a **descriptive mixture only**, not a strategy hurdle.

Cards stay `INTAKE_ONLY` / HYPOTHESIS. Notes landed on:

- `research/candidates/C-001-supply-demand-zone.md` (+ yaml)
- `research/candidates/C-002-triple-rsi-mr.md` (+ yaml)
- `research/candidates/C-003-second-entry-pullback.md` (+ yaml)
- `config/candidates/C-00x.yaml`

Not a promotion. Not a reject. **DO NOT SIZE**.

---

## BMNR / STRC audit — BMNR VOID cause is business transformation (not ticker reuse)

Principal-cited BMNR: **449 bars**, 1-bar mean **2.141%** vs median **-0.405%**; one bar ~695%.
STRC: huge robust-sigma on a ~12% bar (#77 N=8 run); **cleared A/B** on the #81 `adjusted=true` `--refresh` (stays in both pools).

No `listed_on` (not a dated IPO splice like SPCX / CBRS). **Do not VOID on the single bar (rule C FLAG only).**

**Polygon adjustment check (2026-09-19):** `PolygonEquitiesAdapter._ohlcv` did **not** send `adjusted=`. Polygon /v2/aggs vendor default is true — that is **not** an explicit pin. Code now pins `adjusted=true`. #81 box `--refresh` re-fetched; then **rule B only**.

**BMNR stays VOID** (excluded from the void-excluded pool). **Do not change void status.**

| Field | Value |
|---|---|
| **Ticker** | BMNR (`NASDAQ:BMNR`) |
| **Issuer** | BitMine Immersion Technologies (CIK `0001829311`) — **same issuer throughout** |
| **Rule B suspect bar** | `2025-06-30` (20/20 median ratio 7.9139 on #81 `adjusted=true` tape) |
| **Finding (Principal asked; Intel confirmed)** | **Business transformation, not ticker reuse.** That day: ~$250M PIPE @ $4.50 for ETH treasury + Tom Lee named Chairman (8-K `0001683168-25-004802`). Separate May 15–16 2025 1-for-20 reverse split (Polygon + EDGAR). Identifier continuous; character break = strategy/governance pivot. |
| **Verdict** | **VOID** under **rule B**. Same exclusion outcome as ticker reuse; **different cause**. The void must state this finding, not only “rule B fired.” Contrast SPCX (true ticker reuse / entity splice under rule A). **Not** an N-sigma void. |

QQQ, NVDA, BB, MRNA: **restore** to the compute pool (legitimate fat tails). Losing QQQ/NVDA costs more than the false N-sigma void protects.

House lesson: a sustained 20/20 level-shift can flag ticker reuse **or** a continuous-identifier business transformation — record which. See `config/knowledge/house-lessons.md`.

---

## 4. Universe overlay — DROPPED this pass

Do **not** run or implement AVGO/MSFT/META/JPM/XOM/SMH/XLF overlay. Do not fetch those
tickers. Rationale: mixes non-universe names into a report under correction, and
burns free-tier Polygon quota needed for SPCX/BMNR re-run.

Question for Don (queue Gaps only; not resolved here): desks have been reporting
AVGO/MSFT/META/JPM/XOM while those names are absent from `monitor.yaml`. Either
they belong in universe via Principal PR, or desks must stop reporting them.
Do **not** widen the base-rate run to answer that.

---

## IC Gate 1 — verdict distinction (quoted; FAIL intact)

IC attack review: [`phase1-2026-09-19-ic-attack.md`](phase1-2026-09-19-ic-attack.md) (#79). Follow-up: [`phase1-2026-09-19-ic-follow-up.md`](phase1-2026-09-19-ic-follow-up.md).

IC Gate 1 remains **FAIL** as the methodology-build gate for strategies. Do not soften FAIL.

Tables are usable as a **descriptive coin-flip mixture** under **PROVISIONAL** equity history.

The pooled ~33% is **NOT** a strategy hurdle.

**Attack A9 CLOSED stale** vs [#81](https://github.com/ElChopa11/market-memory/pull/81) on-box equity panel (this committed report includes QQQ/NVDA/TSLA and the rest of the monitor equity names with n≥200; SPCX/BMNR voided). Equity rates stay **PROVISIONAL**. The opening note that *this* cloud VM has no `POLYGON_API_KEY` still describes how the crypto-only draft was written; it does not reopen A9.

