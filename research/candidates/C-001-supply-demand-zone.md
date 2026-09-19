# C-001 — Supply / demand zone

| Field | Value |
|---|---|
| **Id** | C-001 |
| **Owner** | QUANT |
| **Desk** | Quant |
| **Status** | INTAKE_ONLY (claim class HYPOTHESIS) |
| **Intake** | Principal 2026-09-19 |
| **Sizing** | no — **DO NOT SIZE** |
| **Scan gate** | no — does not promote into watchlist / universe / PLAYBOOK |
| **Live** | no |

Machine params: [`C-001-supply-demand-zone.yaml`](C-001-supply-demand-zone.yaml).

## Provenance

Retail video / Substack / Reddit zone folklore (Seiden-style rally-base-rally / drop-base-rally screenshots). **`n=unknown`. Hypothesis weight only.** Not a sample. Not evidence.

## Source slogan — REJECT

> “Institutions left unfilled orders in the zone, so price must defend it.”

**REJECT.** Unfalsifiable intent. No sample, window, instrument set, cost model, or split. Causal “must defend” does not survive rule 4. The mechanical restatement below is the only claim that may stay at HYPOTHESIS.

## Claim restated (falsifiable)

On the **instrument set** below, over the **window** below, after a zone is confirmed under params `N,X,Y,Z,M` (ATR), the first return to that zone has mean R **after the named cost model** that is strictly greater than 0 on the embargoed **test** split, using invalidation `M`·ATR through the far edge and a time-stop of `H=10` daily bars.

If Quant records `n < 20` triggers in the test split, the study verdict is `INSUFFICIENT_DATA` (no expectancy claim). Intake invents no R.

### Sample

Trigger events (first confirmed-zone returns) whose trigger bar `available_at` lies inside the named split. `n` is unknown until Quant runs. `n < 20` → no edge claim.

### Window

Daily **completed** bars. Train `2022-01-01`–`2024-12-31`. Embargo `2025-01-01`–`2025-01-31`. Test `2025-02-01`–`2026-09-18`. Knowledge clock is `available_at`, never `market_time`.

### Instrument set

Primary tape only unless a PIT daily series exists:

| Symbol | Membership | Watchlist tier |
|---|---|---|
| BTC | `in_universe` | `universe` |
| NVDA | `in_universe` | `universe` |

Extended (only with PIT daily): ETH (`watch_only` / `monitor`); AVGO, MSFT, META, JPM, XOM (`in_universe` / `monitor`). Excluded: `deferred_must_cut`, blocked names (CASHCAT, PONSUSD), KRX:005930 / KRX:KQ11 (resolved #60; not `in_universe`). **No membership edits.**

### Cost model

`taker_fee*2 + slippage_bps/1e4*2 + funding_rate*(expected_hold_hours/24)`.

- `taker_fee = 0.00045` from `config/quant/trade_math.yaml`
- `slippage_bps = 5` unless a flow `est_slippage(clip)` exists for the cost clip
- `expected_hold_hours = 24`
- `funding_rate = 0` on equities
- `default_clip = 10000` is a **cost clip only** — **DO NOT SIZE**

### Split method

Calendar embargo (one-month purge). No random shuffle. Params locked in the sibling YAML **before** the test split is scored. Walk-forward is allowed later only as a pre-registered amendment.

## Params (`N`, `X`, `Y`, `Z`, `M` ATR)

| Token | Role | Locked value |
|---|---|---|
| `N` | Min completed bars in the base | 5 |
| `X` | Min departure from the base, in ATR | 2.0 |
| `Y` | Max base height, in ATR | 0.8 |
| `Z` | Touch tolerance from the near edge, in ATR | 0.25 |
| `M` | Invalidation beyond the far edge, in ATR | 0.5 |
| ATR period | Wilder-style ATR on completed bars | 14 |
| `H` | Time-stop (daily bars) | 10 |

**Zone confirm (PIT).** A demand zone exists only after a base of ≥ `N` bars with height ≤ `Y`·ATR is followed by a completed departure of ≥ `X`·ATR away from the base. Confirm clock = that departure bar’s `available_at`. A supply zone is the mirror.

**Trigger.** First later bar whose available range intersects the zone within `Z`·ATR of the near edge.

**Invalidation.** Close through the far edge by `M`·ATR, or `H` bars elapse, whichever first.

## Payoff shape

Fade-the-return-to-base (mean-reversion after an impulse). Many small opposing excursions if the first touch holds. Fat **left** tail when the zone fails through `M`·ATR (impulse continuation). Time-stop `H` caps the right tail. Not a breakout shape. Not a trend-follow shape.

## Look-ahead notes

- Labeling a base as a zone with a departure that has not completed is look-ahead.
- Intra-bar touch using a high/low not yet available is look-ahead.
- ATR at `t` must not include `t+1`.
- `published_at` / `market_time` are not knowledge clocks.

## Survivorship notes

`survivorship_uncontrolled`. Locked membership only. Delisted or halted names are absent. IMP-029 (delisted 5y tape) is BACKLOG. Do not claim a survivorship-safe multi-year edge on this panel.

## Study harness (not implemented)

`packages/backtest` fixture replay exists. Stubs today: `buy_hold`, `threshold`. **C-001 is not implemented as a strategy.** Quant may add a study-only name later. Command shape: `uv run lab backtest run --fixture PATH --no-db`. Do not bind a thesis. Do not inherit PLAYBOOK sizing.

## Non-goals

Live path. Sizing. Scan-gate / universe / watchlist promotion. Invented expectancy. Telegram as a signal. **No computation on this card.**

## Evening append (rules 8–12)

8. **Cross-candidate correlation.** C-001 is a dip-in-uptrend variant with C-002 and C-003. Before any promotion: pairwise overlap % within 5 bars, same instrument + direction, plus a correlation matrix next to individual results. Overlap > 40% → keep **one** (simplest). Cluster netting will not catch this. **Not computed at intake.**

9. **Order of work.** Phase 1 unconditional base rates in Memory first. 6e scorecards must auto-track instances. Until both land: **INTAKE_ONLY** — params proposed, NOTHING computed.

10. **Params before first run.** Locked in [`config/candidates/C-001.yaml`](../../config/candidates/C-001.yaml) (`N=5`, `X=2.0`, `Y=0.8`, `Z=0.25`, `M=0.5`, ATR 14, horizon `H=10`). Post-hoc change = `C-001.v2` and sample reset.

11. **Passing.** `PASS` ≠ scan. Moves to PAPER-ELIGIBLE, UNSIZED, via scorecard, until live forward instances match the backtest interval. Principal decides sizing later. Separate gates.

12. **Stop.** Close when sample 80 is reached, the window is exhausted, or instances < 20. Verdict `PASS` \| `FAIL` \| `INSUFFICIENT SAMPLE`. No keep-tuning.

## Deliverable / acceptance

When unblocked: `research/studies/C-001/<date>.md` + combined `research/studies/signal-correlation/<date>.md`. Each states coded definition, params+commit ref, sample, window, split, cost model, benchmark, haircut, results per regime, verdict, what would render it spurious. Base rates in Memory, not only the write-up.

Acceptance: no future bars; pivots `K=2` bars later; zones without hindsight; same-fixture `params_hash`; every instance including blow-throughs; reconcile vs raw detector count; Weekly Investment Review `PASS` or `FAIL`.

## Permission-filter note (Phase-1 instrument base rates, 2026-09-19)

Status remains **INTAKE_ONLY** / HYPOTHESIS. Not a promotion. Not a reject. **DO NOT SIZE**. NOTHING computed on this card.

Phase-1 instrument dump [`research/base-rates/phase1-2026-09-19.md`](../base-rates/phase1-2026-09-19.md): trend-up conditioning (close above SMA200 and SMA50 rising) does **not** raise the 1R:2R bracket hit rate on that sample; for several names it falls. The **permission filter** (confirmed uptrend as a gate) does not carry edge on its own.

Any later study of C-001 must beat **that instrument's own unconditional** 1R:2R bracket rate (and, if it uses a trend-up permission filter, **that instrument's own trend-up** bracket). The pooled ~33% is a **descriptive mixture only**, not a strategy hurdle. IC Gate 1 remains **FAIL** as the methodology-build gate for strategies. VVVUSD is recorded on the same artifact as an interpretable outlier (dedicated look later; not a scan-gate).

