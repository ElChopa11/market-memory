# C-003 — Second-entry pullback

| Field | Value |
|---|---|
| **Id** | C-003 |
| **Owner** | QUANT |
| **Desk** | Quant |
| **Status** | INTAKE_ONLY (claim class HYPOTHESIS) |
| **Intake** | Principal 2026-09-19 |
| **Sizing** | no — **DO NOT SIZE** |
| **Scan gate** | no — does not promote into watchlist / universe / PLAYBOOK |
| **Live** | no |

Machine params: [`C-003-second-entry-pullback.yaml`](C-003-second-entry-pullback.yaml).

## Provenance

Retail video / Substack / Reddit price-action folklore (Al Brooks-style “second entry” after a breakout). **`n=unknown`. Hypothesis weight only.** Not a sample. Not evidence.

## Source slogan — REJECT

> “The second entry is the high-probability continuation; always take it.”

**REJECT.** “Always” / “high-probability” without `n` is unfalsifiable. No sample, window, instrument set, cost model, or split. Labeling a pullback as “first” only because a second one later appears is look-ahead (rule 7). The mechanical restatement below is the only claim that may stay at HYPOTHESIS.

## Claim restated (falsifiable)

On the **instrument set** below, over the **window** below, after a completed `N`-bar extreme breakout, a first pullback of ≥ `X`·ATR that does **not** take out the breakout extreme, then a second pullback of ≥ `Y`·ATR, the trigger close back through the second-pullback extreme by `Z`·ATR has mean R **after the named cost model** that is strictly greater than 0 on the embargoed **test** split, using invalidation `M`·ATR beyond that second-pullback extreme and a time-stop of `H=15` daily bars.

The short-side mirror (break of the `N`-bar low, two rallies, trigger through the second-rally extreme) is a separate hypothesis with the same costs, split, and `n` rule. Intake does not pick a side as a call.

If Quant records `n < 20` triggers in the test split, the study verdict is `INSUFFICIENT_DATA`. Intake invents no R.

### Sample

Trigger events (second-entry trigger bars) whose `available_at` lies inside the named split. First pullbacks that never receive a second pullback are **not** triggers and are **not** labeled from the future. `n` unknown until Quant runs. `n < 20` → no edge claim.

### Window

Daily **completed** bars. Train `2022-01-01`–`2024-12-31`. Embargo `2025-01-01`–`2025-01-31`. Test `2025-02-01`–`2026-09-18`. Knowledge clock is `available_at`.

### Instrument set

| Symbol | Membership | Watchlist tier |
|---|---|---|
| BTC | `in_universe` | `universe` |
| NVDA | `in_universe` | `universe` |

Extended only with PIT daily: ETH (`watch_only` / `monitor`); AVGO, MSFT, META, JPM, XOM (`in_universe` / `monitor`). Excluded: `deferred_must_cut`, blocked names, KRX:005930 / KRX:KQ11 (resolved #60; not `in_universe`). **No membership edits.**

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
| `N` | Breakout lookback (`N`-bar extreme) | 20 |
| `X` | Min first-pullback depth, in ATR | 0.5 |
| `Y` | Min second-pullback depth, in ATR | 0.4 |
| `Z` | Trigger: close back through the second-pullback extreme, in ATR | 0.1 |
| `M` | Invalidation beyond the second-pullback extreme, in ATR | 0.3 |
| ATR period | Completed-bar ATR | 14 |
| `H` | Time-stop (daily bars) | 15 |

**Breakout (PIT).** Close beyond the prior `N`-bar extreme using only bars with `available_at` ≤ that close. The breakout bar is not inside its own lookback.

**First pullback.** Subsequent retrace ≥ `X`·ATR that does not take out the breakout extreme, identified from bars ≤ its own `available_at`, **without** requiring that a second pullback exist.

**Second pullback + trigger.** A later retrace ≥ `Y`·ATR, then a completed close back through that second-pullback extreme by `Z`·ATR. Signal clock = that trigger bar’s `available_at`.

**Invalidation.** Close `M`·ATR beyond the second-pullback extreme against the hypothesis, or `H` bars elapse, whichever first.

## Payoff shape

Trend-continuation after a **second** pullback. First pullbacks are skipped by construction (they are not triggers). Right tail if the impulse extends. Fat **left** tail if the second entry is a reversal through `M`·ATR. Time-stop `H=15` caps the hold. Not a fade-the-base shape. Not a triple-RSI oscillator shape.

## Look-ahead notes

- Labeling a pullback as “first” because a second one later appears uses the future.
- An `N`-bar extreme that includes the decision bar is look-ahead.
- Intra-bar trigger before `available_at` is look-ahead.
- `published_at` / `market_time` are not knowledge clocks.

## Survivorship notes

`survivorship_uncontrolled`. Locked membership only. IMP-029 is BACKLOG. Do not claim a survivorship-safe multi-year edge on this panel.

## Study harness (not implemented)

`packages/backtest` fixture replay exists. Stubs today: `buy_hold`, `threshold`. **C-003 is not implemented as a strategy.** Command shape: `uv run lab backtest run --fixture PATH --no-db`. Do not bind a thesis. Do not inherit PLAYBOOK sizing.

## Non-goals

Live path. Sizing. Scan-gate / universe / watchlist promotion. Invented expectancy. Treating a skipped first pullback as a labeled failure from the future. **No computation on this card.**

## Evening append (rules 8–12)

8. **Cross-candidate correlation.** C-003 is a dip-in-uptrend variant with C-001 and C-002. Before any promotion: pairwise overlap % within 5 bars, same instrument + direction, plus a correlation matrix next to individual results. Overlap > 40% → keep **one** (simplest). Cluster netting will not catch this. **Not computed at intake.**

9. **Order of work.** Phase 1 unconditional base rates in Memory first. 6e scorecards must auto-track instances. Until both land: **INTAKE_ONLY** — params proposed, NOTHING computed.

10. **Params before first run.** Locked in [`config/candidates/C-003.yaml`](../../config/candidates/C-003.yaml) (`N=20`, `X=0.5`, `Y=0.4`, `Z=0.1`, `M=0.3`, ATR 14, horizon `H=15`). Post-hoc change = `C-003.v2` and sample reset.

11. **Passing.** `PASS` ≠ scan. Moves to PAPER-ELIGIBLE, UNSIZED, via scorecard, until live forward instances match the backtest interval. Principal decides sizing later. Separate gates.

12. **Stop.** Close when sample 80 is reached, the window is exhausted, or instances < 20. Verdict `PASS` \| `FAIL` \| `INSUFFICIENT SAMPLE`. No keep-tuning.

## Deliverable / acceptance

When unblocked: `research/studies/C-003/<date>.md` + combined `research/studies/signal-correlation/<date>.md`. Each states coded definition, params+commit ref, sample, window, split, cost model, benchmark, haircut, results per regime, verdict, what would make it spurious. Base rates in Memory, not only the write-up.

Acceptance: no future bars; pivots `K=2` bars later (second-pullback extreme confirmed after `K` completed bars); same-fixture `params_hash`; every instance including blow-throughs; reconcile vs raw detector count; Weekly Investment Review `PASS` or `FAIL`.
