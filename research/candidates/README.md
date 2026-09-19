# Candidate strategy intake

Principal intake **2026-09-19**. This tree is a Quant **HYPOTHESIS** shelf, not a thesis workspace, not a Quant Board, not a PLAYBOOK idea list, and not a scan-gate.

Owner is **QUANT**. Status starts at **HYPOTHESIS**. **No sizing. No scan-gate promotion.** Paper / fixture study specs only. Live trading remains hard-gated.

`research/queue/` stays pack evidence. `research/YYYY/THESIS-*` stays the lifecycle spine. Candidates do not become theses by sitting here.

## Intake rules (1–12)

1. **Owner QUANT. Status HYPOTHESIS.** A candidate is not a thesis, not a Quant Board verdict, not a call, and not a paper position. The accountable owner is Quant. Status starts at `HYPOTHESIS` and stays there until a Quant validation study records a closed desk verdict (`RESEARCH_PRIORITY` \| `MONITOR` \| `DEFER` \| `REJECT` \| `INSUFFICIENT_DATA`) on the *study*, not on an instrument. Intake never authors a trade.

2. **No sizing.** Candidates must not compute, recommend, or inherit a size, `size_pct`, clip-as-position, or leverage. PLAYBOOK trade-math sizing stays unused. Cost clips in `config/quant/trade_math.yaml` are for a cost model only. Cards say **DO NOT SIZE**.

3. **No scan-gate promotion.** Intake does not add names to `config/watchlist/monitor.yaml`, `config/universe.yaml`, PLAYBOOK ideas, or `EDGE_SCAN`. A named instrument must state its watchlist tier (`universe` / `monitor` / `blocked`) when known. Membership sets stay locked. Monitor ideas remain UNSIZED.

4. **Restate the claim falsifiably, or REJECT.** Every card must name **sample**, **window**, **instrument set**, **cost model**, and **split method**. If the source slogan cannot be restated with those five fields, status is `REJECT` and the card moves to [`failures/`](failures/README.md). Causal stories about “institutions” or “always snaps back” are rejected as claims; only the mechanical restatement may remain at HYPOTHESIS.

5. **Payoff shape must be explicit.** Mean-reversion, trend-continuation, breakout, or mixed — plus hold horizon, invalidation geometry, and the asymmetry (many small excursions vs a fat left tail). A slogan is not a shape. R is computed only after a study exists; intake does not invent expectancy.

6. **Provenance weight.** Retail video / Substack / Reddit / Twitter / Discord / discretionary price-action blogs = `n=unknown` hypothesis weight. That is not a sample. It is not evidence. It does not raise prior above HYPOTHESIS.

7. **Look-ahead and survivorship notes are required.** Signals use bar `available_at` and observation `as_of_knowledge` (`ingested_at`; never `published_at` / `market_time`). A zone or swing labeled with a future departure is look-ahead. Survivorship: delisted or absent names stay in the study panel or the study is tagged `survivorship_uncontrolled`. Failures archive under [`failures/`](failures/README.md); do not delete; revival needs new evidence, not a silent reopen.

8. **Cross-candidate correlation — mandatory before any promotion.** C-001, C-002, and C-003 are all **dip-in-uptrend** variants. Before any card leaves this shelf, Quant must publish pairwise signal-overlap % within `overlap_n_bars` on the same instrument and the same direction, plus a correlation matrix next to the individual study results. If any pair exceeds `overlap_threshold_pct`, they collapse to **one** candidate; promote **at most one**, and take the simplest definition. Cluster netting (`config/risk/clusters.yaml`) will not catch same-name same-direction overlap. Declared now: `overlap_n_bars=5`, `overlap_threshold_pct=40`. **Nothing is computed at intake.**

9. **Order of work — do not start out of order.** Phase 1 **unconditional base rates** must exist in Market Memory first. Phase 6e scorecards must exist **and** auto-track candidate instances. Until **both** land: **intake only** — definitions + params proposed, **NOTHING computed**. 6e pack-compare (#55) is not instance auto-track. Status on every card and on `config/candidates/<id>.yaml` is `INTAKE_ONLY`.

10. **Parameters declared before the first run.** `N`, `X`, `Y`, `Z`, `M`, thresholds, and horizons live in `config/candidates/<id>.yaml` and must be committed **before** any result. A post-hoc param change is a new version `C-00x.v2` with the sample reset. No silent tuning.

11. **What passing means.** `PASS` is not a scan-gate and not a size. A `PASS` study moves to **PAPER-ELIGIBLE** only: UNSIZED ideas, via scorecard, until live forward instances match the backtest interval. **Then** the Principal decides whether any sizing exists. Separate gates: study `PASS` ≠ paper open ≠ Principal size.

12. **Stop condition.** A study closes when the declared sample is reached, the window is exhausted, or instances are insufficient. Close with exactly one of `PASS` \| `FAIL` \| `INSUFFICIENT SAMPLE`. No keep-tuning. Reopen needs new data or a new hypothesis (`C-00x.v2`), not a silent reopen of `v1`.

## Deliverable (when computation is unblocked)

`research/studies/<candidate-id>/<date>.md` for each id, **plus** one combined `research/studies/signal-correlation/<date>.md`. Each study file states: coded definition; params + commit ref of `config/candidates/<id>.yaml`; sample; window; split; cost model; benchmark; haircut; results per regime; verdict; what would render the result spurious. Base rates live in Market Memory, not only in the write-up. **No dated candidate-compute study files exist yet** (`C-001/` / `C-002/` / `C-003/` / `signal-correlation/`). Methodology studies (e.g. `research/studies/trend-permission-filter/`) are analysis-only and do not unpark these cards. Status is `INTAKE_ONLY`.

## Acceptance (when a study is allowed to run)

- Adversarial detector tests: no future bars; pivots confirmed only `K` bars later; zones have no hindsight label.
- Deterministic re-run of the same fixture (`params_hash` unchanged).
- Every instance counted, including blow-throughs.
- Reconcile study `n` vs the raw detector count.
- Verdicts go to the Weekly Investment Review as `PASS` or `FAIL` (or `INSUFFICIENT SAMPLE`). Not a scan. Not a size.

## Seeded intake (2026-09-19, evening append)

| Id | Slug | Status | Owner | Sizing | Scan gate | Computation |
|---|---|---|---|---|---|---|
| C-001 | [supply-demand-zone](C-001-supply-demand-zone.md) | INTAKE_ONLY / HYPOTHESIS | QUANT | no | no | blocked |
| C-002 | [triple-rsi-mr](C-002-triple-rsi-mr.md) | INTAKE_ONLY / HYPOTHESIS | QUANT | no | no | blocked |
| C-003 | [second-entry-pullback](C-003-second-entry-pullback.md) | INTAKE_ONLY / HYPOTHESIS | QUANT | no | no | blocked |

Locked params: `config/candidates/C-00x.yaml` (committed **before** any result). Prose cards restated the claim. Research sibling `.yaml` mirrors the card. **NOTHING computed.**

## What Quant may do later (not this intake)

- After Phase 1 unconditional base rates exist in Memory **and** 6e scorecards auto-track instances: execute a fixture / paper **study** from these specs (`lab backtest run --fixture --no-db` harness exists; only `buy_hold` / `threshold` stubs today).
- Write `research/studies/<id>/<date>.md` + the combined correlation report.
- Record `n`, window realized, and a closed study verdict (`PASS` \| `FAIL` \| `INSUFFICIENT SAMPLE`).
- Move a failed claim to `failures/` with the lesson.

## What this tree must not do

- Live trading, signing, wallets, `hl_trade`, `mm_execution`.
- Sizing, PLAYBOOK idea emission, watchlist or universe promotion.
- Skip Skeptic / Risk / Principal gates by calling a candidate a thesis.
- Auto-merge, auto-waive, or close OPEN incidents.

Validation studies are queued as **IMP-039 READY** (not `IN_PROGRESS`). IMP-024 holds the implementation slot (SEC EDGAR). IMP-022 is DONE (#62). IMP-034 on main is ticker/licence (#60), not this shelf. Single-thread hygiene: do not start these studies while another IMP occupies the slot.
