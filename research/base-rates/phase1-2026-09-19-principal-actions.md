# Principal actions on Phase-1 base rates — 2026-09-19

Standing record of Principal (Debo) actions on the Phase-1 instrument dump.
**Not** a Memory `run_id`. **Not** a desk product. **Not** a Telegram send. Paper only.
Do not invent `run_id`. Cite file paths.

This cloud VM does **not** have `POLYGON_API_KEY`. Equity bars were not fetched here.
Crypto tables live in [`phase1-2026-09-19.md`](phase1-2026-09-19.md) (13 names computed).
Continuity check is in `scripts/research/base_rates_phase1.py`.
Re-run **on the box** (free-tier pace, **no** `--no-sleep`; monitor.yaml only — **no overlay fetch**):

```text
export POLYGON_API_KEY=...          # box env only; never commit
uv run python scripts/research/base_rates_phase1.py
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
| **Verdict** | **VOID** `suspected_ticker_reuse`. Exclude from pooled stats. Do not trim and keep. |
| **Code** | `mm_ingest.equities.continuity` (listing date **or** N=8 robust-sigma, `sigma = 1.4826 * MAD`); `PolygonEquitiesAdapter.continuity_check` |

House lesson: resolving a ticker to an identifier does **not** prove the returned series belongs to one entity. See `config/knowledge/house-lessons.md`.

**Pooled 1R:2R without SPCX.** This VM cannot recompute the equity-inclusive pool (no Polygon key). The crypto-only pool in [`phase1-2026-09-19.md`](phase1-2026-09-19.md) never included SPCX: gross **32.4%** (5315 targets / 11113 stops); net **31.8%**. On-box re-run after continuity void must publish the new **equity+crypto** pooled gross/net with SPCX out. Do not invent that number here.

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

This undercuts the shared premise of C-001 / C-002 / C-003 (dip entries gated on a confirmed uptrend) **in this sample**. Do **not** conclude the strategies fail. Conclude the **permission filter does not carry edge on its own**. Any candidate that relies on it must beat **that instrument's own trend-up** bracket rate, not the pooled ~33.3% coin-flip.

Cards stay `INTAKE_ONLY` / HYPOTHESIS. Notes landed on:

- `research/candidates/C-001-supply-demand-zone.md` (+ yaml)
- `research/candidates/C-002-triple-rsi-mr.md` (+ yaml)
- `research/candidates/C-003-second-entry-pullback.md` (+ yaml)
- `config/candidates/C-00x.yaml`

Not a promotion. Not a reject. **DO NOT SIZE**.

---

## BMNR audit

Principal-cited: **449 bars**, 1-bar mean **2.141%** vs median **-0.405%**.

No `listed_on` in `config/research/ticker_continuity.yaml` (not a dated IPO splice like SPCX / CBRS). This VM did not fetch the tape, so the N-sigma check did not run.

**Do not silently keep BMNR in pools if the box continuity check flags `suspected_ticker_reuse`.** Until that re-run: treat the mean/median gap as **unresolved** (fat right tail on one entity, **or** a splice). Not cleared. Not voided here. Not a call.

---

## 4. Universe overlay — DROPPED this pass

Do **not** run or implement AVGO/MSFT/META/JPM/XOM/SMH/XLF overlay. Do not fetch those
tickers. Rationale: mixes non-universe names into a report under correction, and
burns free-tier Polygon quota needed for SPCX/BMNR re-run.

Question for Don (queue Gaps only; not resolved here): desks have been reporting
AVGO/MSFT/META/JPM/XOM while those names are absent from `monitor.yaml`. Either
they belong in universe via Principal PR, or desks must stop reporting them.
Do **not** widen the base-rate run to answer that.
