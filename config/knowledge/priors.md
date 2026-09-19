# Priors

Principal lock. Literature / academic regularities only. **Not a trigger. Not a size. Not a scan-gate.**

A prior is a starting weight on a *class of claim*. It is not evidence that the claim holds on our tape, in our window, after our costs.

## Standing rule

| Class | What it does | What it still requires |
|---|---|---|
| **Strong** | Raises prior probability of that claim class | **Our** base rates (`as_of_knowledge`, instrument set, window, cost model, split). A strong prior without our rates is still unmeasured. |
| **Moderate** | Weak raise. Sensitive to costs, sample, and regime | Same measurement bar. Do not treat “often cited” as “works here.” |
| **No comparable evidence** | **Needs MORE evidence, not less.** Hypothesis weight only (`n=unknown` until a study exists) | Falsifiable restatement + sample/window/instrument set/cost model/split. Slogan REJECT. |

Citing a prior on a card or brief must use one of those three labels plus the prior name. See [README.md](README.md).

House lessons in [house-lessons.md](house-lessons.md) override a prior when annotated with date + `run_id`.

---

## Strong

These classes have a large, repeatedly documented empirical literature. That raises prior probability. It does **not** skip Phase 1 unconditional base rates, Skeptic, or costs.

| Prior | Claim class (not a rule) | Notes for our desks |
|---|---|---|
| **Momentum** | Cross-sectional and time-series continuation over intermediate horizons | Factor math exists in `mm_quant` (research only). Continuation is a class, not a signal. Needs our window, costs, and `available_at`. |
| **PEAD** | Post-earnings-announcement drift: signed residual after a confirmed print | Confirmed earnings only (e.g. 8-K 2.02). Street estimates stay unavailable until a licensed path exists. Not a same-day print fade. |
| **Index inclusion / deletion** | Mechanical demand around announced reconstitution | Licensed index files are not on the free stack. Event must be dated and knowable at `as_of_knowledge`. Announcement ≠ effective date. |
| **IPO lockup** | Documented supply around an EDGAR-confirmed lockup formula | Intel owns lockup text. **Not** a flat 180 days. Lockup inside horizon = Skeptic blackout (gate 5). Monitor-tier names stay UNSIZED. |
| **Short-term reversal** | Short-horizon return reversal after a completed excursion | Opposite class to intermediate momentum. Horizon must be declared. Intra-bar labels are look-ahead. |
| **Carry** | Compensation for holding a funded / basis / rate differential | `funding_carry` / `basis_carry` are research factors. Missing side → `unavailable`, never invented. Carry is not a reason to size. |
| **Value / quality** | Cheap vs expensive; profitability / quality vs junk, on a named definition | Definition + rebalance calendar + costs required. Drawdown is not value. Membership (`in_universe`) is not a quality score. |

---

## Moderate

Documented, weaker or more fragile than the strong set. Cost, sample, and regime usually dominate the headline effect.

| Prior | Claim class (not a rule) | Notes for our desks |
|---|---|---|
| **Vol clustering** | Large moves cluster; realised vol is autocorrelated | Regime inputs may use vol; vol is not a direction. Missing VIX/feed → `unavailable`. |
| **Seasonality** | Calendar-timed average effects (session, month, turn-of-period) | Needs a pre-registered window and a multiple-testing note. One holiday print is not a season. |
| **Overnight / intraday** | Open-to-open vs session-open-to-close return split | Session clocks are DST-aware in Pulse. Do not mix NY session stats into a Sydney-only sample without saying so. |

---

## No comparable evidence

Retail / discretionary pattern languages and indicator stacks. **Hypothesis only.** They require *more* evidence than a strong prior: coded definition, locked params before the first run, `n` vs raw detector count, costs, and a closed study verdict.

| Prior | Claim class | Lab status |
|---|---|---|
| **FVG / order block / sweeps / SFP / ICT** | Discretionary imbalance / liquidity-pool narratives | No comparable sample. Zone or swing labeled with a future departure is look-ahead. |
| **Supply–demand zones** | Seiden-style base-and-departure folklore | C-001 is `INTAKE_ONLY` / HYPOTHESIS, provenance `n=unknown`. Not a thesis. **DO NOT SIZE.** |
| **Indicator combos** | Multi-oscillator / multi-MA stacks sold as a system | C-002 (triple RSI) is the same shelf. Combo count is not robustness. Post-hoc threshold change = new version + sample reset. |

Retail video / Substack / Reddit / Twitter / Discord provenance stays `n=unknown` hypothesis weight. It does not raise a no-evidence prior into moderate or strong.

---

## Must not

- Infer a trigger, invalidation, or size from any row above.
- Substitute a literature citation for our base rates.
- Promote a no-evidence prior by stacking slogans.
- Edit this file except via Principal PR.
