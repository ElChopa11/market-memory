# IC Gate 1 — attack review: Phase-1 base-rates methodology (2026-09-19)

| Field | Value |
|---|---|
| **Reviewer** | Gate 1 — Investment Committee (adversarial) |
| **Artifact** | `research/base-rates/phase1-2026-09-19.md` |
| **Continuity / Principal actions** | `research/base-rates/phase1-2026-09-19-principal-actions.md` · folder `README.md` |
| **Date** | 2026-09-19 (Australia/Sydney) |
| **Scope** | Written attack review **before anything is built** on this methodology. Document only. No code. No PR against `scripts/research/`, `packages/mm_delivery`, or `config/schedules`. |
| **Standing** | PAPER. No authoring, sizing, or entry suggestion. Gate 2 Risk code not invoked / not argued. |

## Verdict: **FAIL**

Do **not** treat this dump as a finished methodology foundation for strategy build, candidate promotion, or a desk null. A pass with no stated attack would be a failed review. Attacks below are specific; evidence that would change each is named.

This is **not** a claim that the tables are fabricated. Honesty about the Polygon 2-year cap, SPCX void, and “not a call” labels is real. Honesty does not clear the failure modes.

---

## Attack 1 — Two-year window and single-regime fitting

**Failure mode:** The equity path is explicitly **one year of usable signals after SMA200 warmup inside a vendor 2-year cap** (principal-actions §2; phase1 banner). Building “Phase-1 methodology” while equities are **offline on this artifact** (n_bars=0 for NVDA and the entire base list) means the finished claim is **crypto-only**. Crypto series (2020–2026) span COVID, boom, bear, and hike regimes, but the **pooled coin-flip null** is fit on the full path as if one stationary process. Unconditional forward **means** are mostly positive (secular drift) — that is not a pure no-edge null; it is a sample with bullish drift baked in. Late listings (HYPE from 2024-12, VVV from 2025-01, PURR from 2024-11) contribute regime buckets that barely clear n≥100 and are still single-cycle.

**Evidence that would change this:** Multi-regime walk-forward of the same bracket (pre-registered folds); equity tables on-box with voided SPCX and labeled PROVISIONAL until history ≫ 2y; null defined as **demean**ed or sign-randomized paths, not raw long bias.

---

## Attack 2 — Survivorship in `monitor.yaml`

**Failure mode:** The study set is **whoever is on `config/watchlist/monitor.yaml` today** with ≥200 bars. Names that died, delisted, or never reached 200 bars are absent or excluded (CASHCAT 71, PONS 20, CHIPI 151). The computed pool (13 crypto) is a **survivor set of liquid, long-lived HL coins** plus late high-vol names that made the cut. Pooling them as “instruments we might trade” overstates how representative the ~33% null is for future monitor adds / listings / blocked memes. Governance survivors (SOL/HYPE/NEAR/ARB still on monitor as archive decisions) are not the same as market survivorship, but they still enter the **pooled** stop/target counts.

**Evidence that would change this:** Explicit deceased/delisted panel or point-in-time monitor snapshots; pool weights or separate brackets by tier (`universe` vs `monitor` vs blocked); report that pooled null is **conditional on current monitor membership**.

---

## Attack 3 — Same-bar stop-and-target tie handling

**Failure mode:** Spec: “same-bar stop+target = tie; else timeout.” Hit rate is defined as **targets / (targets + stops)** — e.g. pooled gross **5315 / (5315+11113) = 32.4%**. **Ties and timeouts are excluded from the denominator.** A “fair 1:2 coin-flip ~33.3%” assumes every path resolves to stop or target. Excluding unresolved paths makes the comparison to 33.3% **ill-posed**. Same-bar ties are economically ambiguous (path dependence / fill assumptions); dropping them is a silent choice. No sensitivity table (tie→stop, tie→target, 50/50, timeout→flat).

**Evidence that would change this:** Pre-registered tie rule matching execution assumptions; hit rate with timeouts as a third outcome (or mark-to-market at horizon); sensitivity appendix showing pooled hit under alternate tie treatments.

---

## Attack 4 — R = 1×ATR20 as cross-instrument normaliser

**Failure mode:** ATR20 scales with local volatility, so R is locally vol-adjusted — necessary but not sufficient. Last vol20 in-sample spans roughly **~42% (BTC) to ~248% (ARB)** annualised (phase1 unconditional sample stats). The same “1R” is not the same **portfolio risk** or the same **cost-as-fraction-of-R** when a flat bps cost model is applied (Attack 6). High-ATR names also show different timeout mass; the 10-bar horizon interacts with ATR width (wide stops → more timeouts → more paths dropped from the hit-rate denominator — Attack 3 compounds). Claiming a single ATR multiple is “the” normaliser across that vol span is an assertion, not a demonstrated invariance.

**Evidence that would change this:** Show hit rate / expectancy stable when R is set by vol-target or dollar-risk instead of 1×ATR20; report cost/R by ticker; stratified results by vol quintile.

---

## Attack 5 — Pooled bracket vs per-instrument hit spread ~25.5%–40.1%

**Failure mode:** Long gross hit rates in-sample run from **ARB 25.3%** and **HYPE short 25.5%** up to **VVV long 43.3%** (and short 17.2%). That is not noise around 33%; it is **heterogeneous instruments**. A pooled 32.4% is a **mixture weight** dominated by long-history names (BTC/ETH/SOL/LTC/DOGE n≈2200), not a universal null. The file already says trend-up strategies must beat **instrument-own** trend-up rates — the same logic **kills the pooled unconditional coin-flip as a build baseline**. VVV’s 47.3% trend-up hit (n=200) is flagged as an outlier; without a multiple-testing correction across 13 names × regimes × sides, that “dedicated look” is cherry risk.

**Evidence that would change this:** Drop pooled headline as a strategy hurdle; publish per-ticker nulls only; pre-register which instruments enter any pool; FDR/HOLM across the table before calling outliers.

---

## Attack 6 — Cost model realism at our clip

**Failure mode:** Flat perps RT **29 bps** (taker 4.5 bps/side + slip 5 bps/side + funding 1 bp/day × 10 days). Labeled pessimistic / not a live schedule — still used to shift stops/targets for “net” hit rates. Attacks: (1) **same bps for BTC and PURR/VVV/ARB** ignores ADV/depth at intended clip; (2) funding 1 bp/day is not stress for HL funding extremes; (3) **path-shifting** stop/target for costs ≠ subtracting costs from R-multiple expectancy — it changes which barrier is touched first; (4) equities cost line (19 bps) is specified while **zero equity bars** appear in this file’s pools. “Net of flat cost” hit rates (31.8% pooled) inherit all of the above.

**Evidence that would change this:** Clip-specific spread/depth/ADV from Intel at as_of_knowledge; funding distribution (not a point); expectancy after costs in R-space without barrier shifting; separate crypto vs equity cost tables only when both panels exist.

---

## Additional attacks (required — review must not be thin)

### A7 — Dual always-long and always-short on every bar
Both sides are evaluated on the same signal bars. Sample paths are **negatively dependent**. Treating long+short counts as independent trials toward a pooled null overstates precision.

**Change with:** Report long-only and short-only nulls separately; block bootstrap by date.

### A8 — Mean forward returns as “edge” language
Summary line 1 cites **mean** 1-bar/10-bar returns while many **medians are ≤0** (SOL, NEAR, UNI, VVV, DOGE, PURR at 1-bar). Right-tail dominated means are not a robust unconditional edge. Risk of later desks quoting means as permission to long.

**Change with:** Lead with median/IQR; ban mean-only headlines for fat-tailed coins.

### A9 — Incomplete Phase-1 (equities absent)
Principal-actions admit no `POLYGON_API_KEY` on the VM that wrote the crypto tables; equities are offline exclusions. Calling the methodology “finished” for build while the equity half is empty is **scope fraud by packaging**. Continuity lessons (SPCX void, BMNR unresolved) are important but not a substitute for a completed equity panel.

**Change with:** On-box equity re-run with SPCX voided, BMNR continuity resolved, PROVISIONAL banner retained; or rename artifact to **crypto-only Phase-1a**.

### A10 — Permission-filter note vs candidate cards
Honest finding that trend-up permission does not raise hit rates undercuts C-001/C-002/C-003 premises. Cards stay INTAKE_ONLY — good. Attack: queue language “do not reject on this evidence alone” must not become a soft PASS into build. Gate 1 will FAIL any candidate that uses SMA200 permission as edge without beating **instrument-own** trend-up bracket **and** a pre-registered costed null.

---

## What would flip FAIL → REVISE (not PASS)

All of:
1. Rename / scope: crypto-only explicit, or equities completed under PROVISIONAL.
2. Replace pooled coin-flip hurdle with **per-instrument** costed nulls; pre-register pool membership if any pool remains.
3. Tie/timeout policy documented with sensitivity; hit-rate definition aligned to a fair-coin claim or the claim dropped.
4. Cost model tied to clip liquidity + funding distribution; no barrier-shift without showing equivalence to R-space costs.
5. Survivorship / monitor point-in-time statement on the coverage table.
6. Mean/median honesty in the three-line summary.

PASS requires the above **plus** a second independent Gate 1 pass with no open attack — not this review.

---

## Explicit non-actions

- No code changes. No edits to `scripts/research/`, `packages/mm_delivery`, `config/schedules`.
- No sizing, no entries, no Telegram, no Gate 2 invoke/override.
- No promotion or reject of C-001/C-002/C-003 beyond Gate 1 methodology FAIL for building on this null.

**Signed:** Gate 1 IC · 2026-09-19 · **FAIL** — do not build on Phase-1 methodology until attacks addressed
