# C-002 — Triple RSI mean-reversion

| Field | Value |
|---|---|
| **Id** | C-002 |
| **Owner** | QUANT |
| **Desk** | Quant |
| **Status** | INTAKE_ONLY (claim class HYPOTHESIS) |
| **Intake** | Principal 2026-09-19 |
| **Sizing** | no — **DO NOT SIZE** |
| **Scan gate** | no — does not promote into watchlist / universe / PLAYBOOK |
| **Live** | no |

Machine params: [`C-002-triple-rsi-mr.yaml`](C-002-triple-rsi-mr.yaml).

## Provenance

Retail video / Substack / Reddit oscillator stacks (triple RSI or multi-timeframe RSI “oversold bounce”). **`n=unknown`. Hypothesis weight only.** Not a sample. Not evidence.

## Source slogan — REJECT

> “When three RSIs are oversold, price always snaps back.”

**REJECT.** “Always” is unfalsifiable. No sample, window, instrument set, cost model, or split. Multi-timeframe versions that read an unclosed higher-TF bar are look-ahead (rule 7) and stay REJECT unless restated on completed bars. The same-TF mechanical restatement below is the only claim that may stay at HYPOTHESIS.

## Claim restated (falsifiable)

On the **instrument set** below, over the **window** below, when Wilder RSI lengths `N`, `X`, and `Y` are all ≤ `Z` on the same completed daily bar, the subsequent hold through `rsi_exit=50` on the fast RSI or `hold_bars=5` (whichever first), with invalidation `M`·ATR from the trigger close, has mean R **after the named cost model** that is strictly greater than 0 on the embargoed **test** split.

The mirror (all three RSI ≥ `100-Z`) is a separate short-side hypothesis with the same costs, split, and `n` rule. Intake does not pick a side as a call.

If Quant records `n < 20` triggers in the test split, the study verdict is `INSUFFICIENT_DATA`. Intake invents no R.

### Sample

Trigger events (first bar where all three RSIs cross into ≤ `Z`, or ≥ `100-Z` for the mirror) whose `available_at` lies inside the named split. `n` unknown until Quant runs. `n < 20` → no edge claim.

### Window

Daily **completed** bars. **Same TF** for `N`, `X`, `Y`. Train `2022-01-01`–`2024-12-31`. Embargo `2025-01-01`–`2025-01-31`. Test `2025-02-01`–`2026-09-18`. Knowledge clock is `available_at`.

### Instrument set

| Symbol | Membership | Watchlist tier |
|---|---|---|
| BTC | `in_universe` | `universe` |
| NVDA | `in_universe` | `universe` |

Extended only with PIT daily: ETH (`watch_only` / `monitor`); AVGO, MSFT, META, JPM, XOM (`in_universe` / `monitor`). Excluded: `deferred_must_cut`, blocked names, KRX:005930 / KRX:KQ11 (resolved #60; not `in_universe`). Multi-TF stacks excluded until each higher-TF bar is closed. **No membership edits.**

### Cost model

`taker_fee*2 + slippage_bps/1e4*2 + funding_rate*(expected_hold_hours/24)`.

- `taker_fee = 0.00045` from `config/quant/trade_math.yaml`
- `slippage_bps = 5` unless a flow `est_slippage(clip)` exists for the cost clip
- `expected_hold_hours = 24`
- `funding_rate = 0` on equities
- `default_clip = 10000` is a **cost clip only** — **DO NOT SIZE**

### Split method

Calendar embargo (one-month purge). No random shuffle. Params locked in the sibling YAML **before** the test split is scored.

## Params (`N`, `X`, `Y`, `Z`, `M` ATR)

| Token | Role | Locked value |
|---|---|---|
| `N` | Fast RSI length (Wilder) | 2 |
| `X` | Mid RSI length | 7 |
| `Y` | Slow RSI length | 14 |
| `Z` | Oversold threshold (overbought = `100-Z`) | 20 |
| `M` | Invalidation from trigger close, in ATR | 1.5 |
| ATR period | Completed-bar ATR | 14 |
| `hold_bars` | Time-stop | 5 |
| `rsi_exit` | Fast-RSI flatten level | 50 |

**Trigger (PIT).** All three RSIs, computed on closes with `available_at` ≤ `t`, are ≤ `Z` (or all ≥ `100-Z` for the mirror) on daily bar `t`, and were not all through that threshold on `t-1`.

**Invalidation.** Close `M`·ATR through the trigger close against the hypothesis, or `hold_bars` elapse, or fast RSI crosses `rsi_exit`, whichever first.

## Payoff shape

Short-horizon mean-reversion. Many small opposing excursions when the fast RSI exits `Z` toward `rsi_exit`. Fat **left** tail on trend days that stay through `M`·ATR. Time-stop `hold_bars=5` caps the right tail. Not a breakout shape. Not a second-entry continuation shape.

## Look-ahead notes

- RSI at `t` using a close that is not yet available is look-ahead.
- Multi-TF RSI that reads an unclosed higher-TF bar is look-ahead → REJECT that variant.
- Wilder seeding must not include future bars.
- `published_at` / `market_time` are not knowledge clocks.

## Survivorship notes

`survivorship_uncontrolled`. Locked membership only. IMP-029 is BACKLOG. Do not claim a survivorship-safe multi-year edge on this panel.

## Study harness (not implemented)

`packages/backtest` fixture replay exists. Stubs today: `buy_hold`, `threshold`. **C-002 is not implemented as a strategy.** Command shape: `uv run lab backtest run --fixture PATH --no-db`. Do not bind a thesis. Do not inherit PLAYBOOK sizing.

## Non-goals

Live path. Sizing. Scan-gate / universe / watchlist promotion. Invented expectancy. Implementing multi-TF RSI without a closed-bar rule. **No computation on this card.**

## Evening append (rules 8–12)

8. **Cross-candidate correlation.** C-002 is a dip-in-uptrend variant with C-001 and C-003. Before any promotion: pairwise overlap % within 5 bars, same instrument + direction, plus a correlation matrix next to individual results. Overlap > 40% → keep **one** (simplest). Cluster netting will not catch this. **Not computed at intake.**

9. **Order of work.** Phase 1 unconditional base rates in Memory first. 6e scorecards must auto-track instances. Until both land: **INTAKE_ONLY** — params proposed, NOTHING computed.

10. **Params before first run.** Locked in [`config/candidates/C-002.yaml`](../../config/candidates/C-002.yaml) (`N=2`, `X=7`, `Y=14`, `Z=20`, `M=1.5`, ATR 14, horizon `hold_bars=5`, `rsi_exit=50`). Post-hoc change = `C-002.v2` and sample reset.

11. **Passing.** `PASS` ≠ scan. Moves to PAPER-ELIGIBLE, UNSIZED, via scorecard, until live forward instances match the backtest interval. Principal decides sizing later. Separate gates.

12. **Stop.** Close when sample 80 is reached, the window is exhausted, or instances < 20. Verdict `PASS` \| `FAIL` \| `INSUFFICIENT SAMPLE`. No keep-tuning.

## Deliverable / acceptance

When unblocked: `research/studies/C-002/<date>.md` + combined `research/studies/signal-correlation/<date>.md`. Each states coded definition, params+commit ref, sample, window, split, cost model, benchmark, haircut, results per regime, verdict, what would render it spurious. Base rates in Memory, not only the write-up.

Acceptance: no future bars; pivots `K=2` bars later; oscillator turns use completed bars only; same-fixture `params_hash`; every instance including blow-throughs; reconcile vs raw detector count; Weekly Investment Review `PASS` or `FAIL`.

## Permission-filter note (Phase-1 instrument base rates, 2026-09-19)

Status remains **INTAKE_ONLY** / HYPOTHESIS. Not a promotion. Not a reject. **DO NOT SIZE**. NOTHING computed on this card.

Phase-1 instrument dump [`research/base-rates/phase1-2026-09-19.md`](../base-rates/phase1-2026-09-19.md): trend-up conditioning (close above SMA200 and SMA50 rising) does **not** raise the 1R:2R bracket hit rate on that sample; for several names it falls. The **permission filter** (confirmed uptrend as a gate) does not carry edge on its own.

Any later study of C-002 must beat **that instrument's own trend-up** bracket rate, not the pooled ~33.3% coin-flip. VVVUSD is recorded on the same artifact as an interpretable outlier (dedicated look later; not a scan-gate).

