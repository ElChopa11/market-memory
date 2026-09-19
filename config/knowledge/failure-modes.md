# Failure modes

Principal lock. Measurement failures, not strategy advice. Each mode: what it looks like, which test (or gate) catches it, and a slot for a worked example from *our* history once one exists.

A filled example needs **date + `run_id`** (or artifact path + `content_hash`) and should also land in [house-lessons.md](house-lessons.md). Until then the example line stays the placeholder.

---

## Look-ahead (centred pivots / revised / settlement)

**What it looks like.** A signal or label uses information that was not knowable at the bar’s `available_at` or the observation’s `as_of_knowledge` (`ingested_at`; never `published_at` / `market_time`). Typical shapes: centred pivots (a swing confirmed with future bars without a delay `K`); revised prints overwritten in place (FRED/ALFRED vintage collapse); settlement/close used before the close is available; intra-bar high/low treated as known mid-bar.

**Which test catches it.** `tests/adversarial/test_lookahead.py` and `mm_backtest.leakage` refuse `future_close` / early `available_at`. Phase PIT tests (`tests/adversarial/test_phase5b_point_in_time.py` and later `test_phase6*_point_in_time.py`, `test_imp039_point_in_time.py`, `test_imp024_edgar_point_in_time.py`). Lifecycle: backtests key off `available_at`; Memory queries key off `as_of_knowledge`. Skeptic checklist: look-ahead / leakage.

**Worked example (our history).** *(none yet — fill from a dated post-mortem + run_id)*

---

## Survivorship

**What it looks like.** The study panel drops names that halted, delisted, or left the book, so average R is computed only on survivors. Or the panel is “whoever is in the universe today” read backward.

**Which test catches it.** Candidate cards must state `survivorship_uncontrolled` until IMP-029 (delisted tape) exists. `config/quant/base_rates.yaml` pins `survivorship_tag`. Intake rule 7: delisted/absent names stay in the panel or the study is tagged. There is no silent drop-test that reconstructs a delisted tape yet — the catch is the required tag + Skeptic, not a green assertion of survivorship-safety.

**Worked example (our history).** *(none yet — fill from a dated post-mortem + run_id)*

---

## Multiple testing

**What it looks like.** Many windows, thresholds, or indicator stacks tried; one “works”; that one is published as *the* result. Silent param edits after seeing the test split.

**Which test catches it.** IMP-039 rule 10: `N,X,Y,Z,M` and horizons committed in `config/candidates/<id>.yaml` *before* any result. Post-hoc change = `C-00x.v2` and sample reset. `params_hash` must be stable on a fixture re-run (`tests/unit/test_backtest_repro.py`, study acceptance). Scorecards refuse like-for-like compare when anchors differ (IMP-030 / BRIEF-TAG-20260918).

**Worked example (our history).** *(none yet — fill from a dated post-mortem + run_id)*

---

## Regime-fitting

**What it looks like.** A rule is tuned on one vol / rates / trend regime and reported as unconditional. Or two packs are scored as like-for-like when session anchors differ.

**Which test catches it.** Regime tags come from versioned YAML (`config/macro/regimes.yaml`, `config/quant/regime.yaml`), not a hand-fit story. IMP-030 like-for-like keys: `product` / `schedule_anchor` / `universe`; else `NOT_COMPARABLE` (no invented completeness_delta). Decay-watch will not invent a scorecard number to paper over a tagged mismatch.

**Worked example (our history).** *(none yet — fill from a dated post-mortem + run_id)*

---

## Cost omission

**What it looks like.** Gross R or a mid-to-mid excursion reported as edge. Fees, slippage, and funding over the hold are left out. A cost clip is misread as a position.

**Which test catches it.** `mm_quant.trade_math.compute_trade_math` is the only R calculator. Expectancy is after `taker_fee*2 + est_slippage(clip) + funding_rate * expected_hold`. `prior(judgement)` is excluded from expectancy and sizing. `default_clip` is a cost clip only — **DO NOT SIZE**. Candidate cards restate that formula. Hash mismatch → `error_class=math_mismatch`, failed run.

**Worked example (our history).** *(none yet — fill from a dated post-mortem + run_id)*

---

## Overlap

**What it looks like.** Two or three “different” ideas fire on the same name, same direction, inside a few bars (dip-in-uptrend twins). Cluster YAML nets economic themes; it does **not** catch same-instrument same-direction overlap.

**Which test catches it.** IMP-039 rule 8: pairwise signal-overlap % within `overlap_n_bars=5` on the same instrument and direction, plus a correlation matrix, *before* any promotion. Overlap `> overlap_threshold_pct=40` → collapse to one candidate (simplest definition). Nothing is computed at intake; the catch is the mandatory report, not a silent net.

**Worked example (our history).** *(none yet — fill from a dated post-mortem + run_id)*

---

## Sample manufacture

**What it looks like.** `n` is grown by loosening the detector, dropping blow-throughs, stitching windows, or counting non-triggers. A study with `n < 20` still states expectancy.

**Which test catches it.** `n_min: 20` in `config/quant/base_rates.yaml`. Intake: `n < 20` → `INSUFFICIENT SAMPLE` / `INSUFFICIENT_DATA` — no edge claim. Playbook: `n < min_sample` → desk states it; `size_pct = 0`. Acceptance: every instance counted, including blow-throughs; reconcile study `n` vs raw detector count.

**Worked example (our history).** *(none yet — fill from a dated post-mortem + run_id)*

---

## Metric substitution

**What it looks like.** A weaker metric is swapped in after the strong one fails: relative-value simple-diff sold as α; membership (`in_universe`) sold as a Quant verdict; YTD post-selection path sold as lock justification; pack completeness sold as conviction; a `NOT_COMPARABLE` pair given invented deltas.

**Which test catches it.** Language gate (`mm_research_kit.quant_review.language`; IMP-001 / IMP-005 / IMP-032): no active-call / buy / sell / high-confidence / make. Closed Quant set only. `rel ≠ α` (INVALIDATION-20260917 pack). Scorecards: no invented numeric compare on tagged incomparable packs. Thesis cards: watchlist tier stated; monitor ideas UNSIZED.

**Worked example (our history).** *(none yet — fill from a dated post-mortem + run_id)*

---

## Narrative fit

**What it looks like.** A story is chosen because it reads well (institutions “left orders,” “already priced,” “must defend the zone”) and the tape is searched for confirmation. Missing feeds are backfilled from general knowledge.

**Which test catches it.** Skeptic: already-priced / crowding / false causality; FAIL return or archive. Grounding locks (IMP-016 / 6c-0): NUMERIC LOCK, NO BACKFILL (FRED unavailable → no rates figure; `rates` in gaps), HEARSAY (`source X reported Y at T`), CLAIM TAGS — inference cannot trigger or size. Candidate rule 4: unfalsifiable slogan → REJECT.

**Worked example (our history).** *(none yet — fill from a dated post-mortem + run_id)*
