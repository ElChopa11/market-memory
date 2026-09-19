# Candidate strategy intake

Principal intake **2026-09-19**. This tree is a Quant **HYPOTHESIS** shelf, not a thesis workspace, not a Quant Board, not a PLAYBOOK idea list, and not a scan-gate.

Owner is **QUANT**. Status starts at **HYPOTHESIS**. **No sizing. No scan-gate promotion.** Paper / fixture study specs only. Live trading remains hard-gated.

`research/queue/` stays pack evidence. `research/YYYY/THESIS-*` stays the lifecycle spine. Candidates do not become theses by sitting here.

## Intake rules (1–7)

1. **Owner QUANT. Status HYPOTHESIS.** A candidate is not a thesis, not a Quant Board verdict, not a call, and not a paper position. The accountable owner is Quant. Status starts at `HYPOTHESIS` and stays there until a Quant validation study records a closed desk verdict (`RESEARCH_PRIORITY` \| `MONITOR` \| `DEFER` \| `REJECT` \| `INSUFFICIENT_DATA`) on the *study*, not on an instrument. Intake never authors a trade.

2. **No sizing.** Candidates must not compute, recommend, or inherit a size, `size_pct`, clip-as-position, or leverage. PLAYBOOK trade-math sizing stays unused. Cost clips in `config/quant/trade_math.yaml` are for a cost model only. Cards say **DO NOT SIZE**.

3. **No scan-gate promotion.** Intake does not add names to `config/watchlist/monitor.yaml`, `config/universe.yaml`, PLAYBOOK ideas, or `EDGE_SCAN`. A named instrument must state its watchlist tier (`universe` / `monitor` / `blocked`) when known. Membership sets stay locked. Monitor ideas remain UNSIZED.

4. **Restate the claim falsifiably, or REJECT.** Every card must name **sample**, **window**, **instrument set**, **cost model**, and **split method**. If the source slogan cannot be restated with those five fields, status is `REJECT` and the card moves to [`failures/`](failures/README.md). Causal stories about “institutions” or “always snaps back” are rejected as claims; only the mechanical restatement may remain at HYPOTHESIS.

5. **Payoff shape must be explicit.** Mean-reversion, trend-continuation, breakout, or mixed — plus hold horizon, invalidation geometry, and the asymmetry (many small excursions vs a fat left tail). A slogan is not a shape. R is computed only after a study exists; intake does not invent expectancy.

6. **Provenance weight.** Retail video / Substack / Reddit / Twitter / Discord / discretionary price-action blogs = `n=unknown` hypothesis weight. That is not a sample. It is not evidence. It does not raise prior above HYPOTHESIS.

7. **Look-ahead and survivorship notes are required.** Signals use bar `available_at` and observation `as_of_knowledge` (`ingested_at`; never `published_at` / `market_time`). A zone or swing labeled with a future departure is look-ahead. Survivorship: delisted or absent names stay in the study panel or the study is tagged `survivorship_uncontrolled`. Failures archive under [`failures/`](failures/README.md); do not delete; revival needs new evidence, not a silent reopen.

## Seeded intake (2026-09-19)

| Id | Slug | Status | Owner | Sizing | Scan gate |
|---|---|---|---|---|---|
| C-001 | [supply-demand-zone](C-001-supply-demand-zone.md) | HYPOTHESIS | QUANT | no | no |
| C-002 | [triple-rsi-mr](C-002-triple-rsi-mr.md) | HYPOTHESIS | QUANT | no | no |
| C-003 | [second-entry-pullback](C-003-second-entry-pullback.md) | HYPOTHESIS | QUANT | no | no |

Machine params live in the sibling `.yaml`. Prose restates the claim. YAML is the Quant execution spec.

## What Quant may do later (not this intake)

- Execute a fixture / paper **study** from these specs (`lab backtest run --fixture --no-db` harness exists; only `buy_hold` / `threshold` stubs today).
- Record `n`, window realized, and a closed study verdict.
- Move a failed claim to `failures/` with the lesson.

## What this tree must not do

- Live trading, signing, wallets, `hl_trade`, `mm_execution`.
- Sizing, PLAYBOOK idea emission, watchlist or universe promotion.
- Skip Skeptic / Risk / Principal gates by calling a candidate a thesis.
- Auto-merge, auto-waive, or close OPEN incidents.

Validation studies are queued as **IMP-039 READY** (not `IN_PROGRESS`). IMP-024 holds the implementation slot (SEC EDGAR). IMP-022 is DONE (#62). IMP-034 on main is ticker/licence (#60), not this shelf. Single-thread hygiene: do not start these studies while another IMP occupies the slot.
