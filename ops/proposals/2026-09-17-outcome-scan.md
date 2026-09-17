# Ops outcome scan — 2026-09-17

**Cell:** Ops (Coordinator-class). **Audience:** Principal / Don.  
**Status:** PROPOSED ONLY. Not for live until reviewed. Do not merge as a live-logic change.

**Base:** `main` @ `c09ce72` (Phase 4 backtest harness + paper ledger).  
**Not based on:** PR #6 (`cursor/hardening-raw-store-provenance-8bcb`) — open, Principal review, Phase 1 hardening. This scan does not edit ingest, object store, `as_of_knowledge`, or any file on that PR.  
**Not touched:** `config/risk/environments/live.yaml`, credentials, signing, `mm_execution`, `config/briefing/alerts.yaml`, other risk env YAML.

---

## How this scan was done (and what it is not)

There are **zero** closed paper or live trades in git `research/`. The research tree is empty except `research/README.md`. `lab paper list` against this checkout has nothing to list. Preferring rejection of weak claims: this document does **not** invent a P&L series, does **not** treat unit-test ULIDs as production trade ids, and does **not** treat fixture `THESIS-0001` as a real workspace.

“Recent outcomes” for this lab, on this date, are therefore:

| Outcome class | Where it lives | What we can actually cite |
|---|---|---|
| Production paper/live closes | `research/**/paper/*.json`, `paper_trade` rows | **None.** Gap in itself: the learning loop has never run on real closes. |
| Harness closes (unit/CLI) | `tests/unit/test_paper_gates.py`, `tests/unit/test_paper_cli.py` | Operator-supplied `--exit-reason` / `--pnl`; no post-mortem. |
| Harness opens (integration) | `tests/integration/test_phase4_backtest_paper.py` | Opens and inserts `paper_trade`; **never closes**. |
| Frozen Market Pulse day | `tests/fixtures/briefing/frozen_day.json` + `frozen_close.md` | Session **2026-03-10**, as-of **2026-03-10T20:15:00Z**. Fixture theses `THESIS-0001` (paper, short BTC) and `THESIS-0002` (in_research, long ETH). |
| Backtest fixture replay | `tests/fixtures/backtest/clean_bars.json` | Reproducible `params_hash`; not bound to a paper trade. |

Claims below are only those that follow from those paths.

---

## Inventory (question 1–2)

### Where outcomes are recorded today

| Fact | Store | Writer | Notes |
|---|---|---|---|
| Open/close paper | Git `research/.../paper/<ulid>.md` + `.json` | `packages/paper/src/mm_paper/artifacts.py` `write_paper_artifacts` | Human-review source. |
| Open/close paper | Postgres `paper_trade` (Alembic `0004_phase4`) | `packages/memory/src/mm_memory/paper_repository.py` via `apps/lab-cli/src/mm_lab_cli/paper.py` | Skipped with `--no-db`. |
| Fills | `paper_trade.fills_json` + git JSON | open/close ledger | Optional; open does not require a fill. |
| Marks | Git JSON `marks` only | `mm_paper.ledger` | **No `marks_json` column** on `paper_trade`. |
| P&L | `paper_trade.pnl` nullable | `close_paper_trade(..., pnl=)` | Operator string; not computed from fills. |
| Slippage | single `slippage_bps` | computed at open if fill+mark; on close only if still `None` | Exit slippage is dropped when entry slippage exists. |
| Invalidation / max loss | required text + `max_loss_amount > 0` | `mm_paper.gates.require_open_fields` + DB checks | Presence only; never evaluated at close. |
| Expected path | `expected_path` JSON list | `--checkpoint` on open | Optional. |
| Realised path | `realised_path` | close appends `exit:{reason}@{iso}` only | No checkpoint comparison. |
| Exit reason | required on close | `close_paper_trade` | Free text (`"invalidation hit"`, `"time stop"`). |
| Entry thesis hash | `entry_thesis_snapshot_hash` | artifact content hash at open | Not a `what_did_we_know` snapshot. |
| Backtest metrics | `research_run.result_summary` + `params_hash` | `mm_backtest.harness` / `ResearchRunRepository` | Unlinked to `paper_trade`. |
| Risk allow/block | — | `packages/risk/src/mm_risk/__init__.py` is a Phase 0 stub (`LIVE_TRADING_ENABLED = False`) | **No `risk_decision` table.** Paper does not record `rule_id` / `config_version`. |
| Briefs | `briefs/YYYY/MM/DD/*.md` (gitignored) + `brief` index | `mm_briefing.store` | Close brief has “lab right/wrong” hooks; alerts only if thresholds fire. |
| Post-mortem | `templates/post-mortem.md` | **no writer** | Lifecycle only errors if a post-mortem exists *without* paper. |

### Existing playbooks, alerts, data-quality, post-mortem

| Kind | Path | In force? |
|---|---|---|
| Lifecycle / DoD | `docs/research-lifecycle.md`, `packages/research_kit/src/mm_research_kit/lifecycle.py`, `scripts/check-lifecycle.sh` | Yes, for artifact predecessors. |
| Paper runbook | `docs/runbooks/paper-trade.md` | Yes. |
| Promote runbook | `docs/runbooks/promote-paper-to-live.md` | Documented; live still hard-gated. |
| Market Pulse runbook | `docs/runbooks/market-pulse.md` | Yes. |
| Halt / credentials | `docs/runbooks/halt.md`, `docs/runbooks/credential-rotation.md` | Yes; not outcome review. |
| Post-mortem template | `templates/post-mortem.md` | Template only. |
| Skeptic invalidation quality | `templates/skeptic-review.md` § Invalidation quality | Checklist; not machine-checked. |
| Alerts | `config/briefing/alerts.yaml` + `packages/briefing/src/mm_briefing/alerts.py` | Two types: `liquidation_spike`, `funding_oi_divergence`. Fail-closed without numeric thresholds. |
| Data quality | `packages/provenance/src/mm_provenance/quality.py` | `ok` / `partial` / `stale` / `rejected` / `contradicted`. |
| Watchlist no-trade | `config/briefing/watchlist.yaml` | Rendered on pre-open; **not an alert**. |
| Ops playbooks | *(none before this PR)* | This PR adds `ops/` as proposal/draft only. |

---

## Ranked proposals

Severity: **P1** = learning or risk-of-record is already lying in the harness we will use for the first real close. **P2** = first real paper day will miss a signal we already have in the frozen fixture. **P3** = provenance / test coverage that will make P1–P2 hard to audit.

Every proposal below is **not for live until reviewed**. None of them should be copied into `live.yaml` or hot-patched into `config/briefing/alerts.yaml` from this PR.

---

### P1 — Closed paper does not require a post-mortem

**Gap.** Founding brief and lifecycle say the learning record is `post-mortem.md` (expected vs actual path, P&L/slippage, signal quality, risk decision quality, invalidation performance, unknowns at entry, proposed changes — not auto-applied). The close path does not create it, and the checker does not require it.

**Evidence.**

- Template exists: `templates/post-mortem.md`.
- Lifecycle DoD (docs): `docs/research-lifecycle.md` §8 — “Closed paper/live thesis requires post-mortem **before any size increase** (Phase 7)”.
- Founding brief: `docs/founding-brief.md` artifact chain `→ post-mortem (required before size increase)`.
- Checker only: `packages/research_kit/src/mm_research_kit/lifecycle.py` `check_workspace` — errors if `post-mortem.md` exists **without** paper/promotion; **never** errors if paper exists (open or closed) without post-mortem.
- Close writer: `packages/paper/src/mm_paper/ledger.py` `close_paper_trade` — sets `status=closed`, `exit_reason`, optional `pnl`; does not copy `templates/post-mortem.md`.
- CLI: `apps/lab-cli/src/mm_lab_cli/paper.py` `cmd_paper_close` — no post-mortem step.
- Outcome (harness close): `tests/unit/test_paper_gates.py` `test_open_and_close_writes_paper_artifacts` — close with `exit_reason="invalidation hit"`, `pnl="-120"`; asserts status/pnl; **does not** assert a post-mortem file.
- Outcome (CLI close): `tests/unit/test_paper_cli.py` `test_lab_paper_open_close_list` — close with `exit_reason="time stop"`, `pnl="25"`; lists the trade; **no** post-mortem.
- Outcome (integration): `tests/integration/test_phase4_backtest_paper.py` `test_research_run_and_paper_trade_persist` — paper **open** only (`status == "open"`); `PaperRepository.close` is never called.
- Production: `research/` has no `THESIS-*` workspace and no `post-mortem.md`.

**Proposed playbook / test / alert / data change.**

- Playbook: adopt `ops/drafts/playbook-paper-close-review.md` as the Coordinator close checklist (still human, still not auto-applied).
- Test (when promoted): lifecycle fails a workspace that has `paper/*.json` with `status=closed` and no filled `post-mortem.md`. CLI `lab paper close` may warn in Phase 4; a hard gate belongs with the lifecycle checker so `--no-db` cannot skip it.
- Data: optional `paper_trade` column or artifact path `post_mortem_git_path` once the gate exists — schema later, not in this PR.
- Alert: none. This is a process gate, not a Market Pulse push.

**Why it matters.** Without this, the first real close will look like the harness: a ULID, an operator sentence, and optional P&L in Notes. The post-mortem sections the Principal is supposed to read will not exist. Size-increase and promotion runbooks already assume a “results summary” (`docs/runbooks/promote-paper-to-live.md`) that close does not produce.

**How to test (when promoted).**

1. Replay `test_open_and_close_writes_paper_artifacts` and assert **today** there is no `post-mortem.md` (characterise the hole).
2. After the gate: close a fixture thesis; `check_workspace` returns non-zero until `post-mortem.md` has non-placeholder sections; `lab paper close` still does not talk to live or risk.

**Risk of not doing it.** Every closed paper is an incomplete learning record. Promotion and size-up have nothing durable to review except operator `--pnl`.

**Not for live until reviewed.** Do not implement a close-time network call, do not touch `live.yaml`, do not auto-apply “Proposed changes” from a post-mortem into alerts or risk.

---

### P1 — Invalidation is a non-empty string; “invalidation hit” is operator theater

**Gap.** Paper cannot open without invalidation text, and Skeptic has an “Invalidation quality” section, but nothing evaluates the condition against marks, session close, or fills. Close will accept `exit_reason="invalidation hit"` whether or not price ever traded through the stated level. Briefing will call a paper thesis “lab wrong (so far)” without checking invalidation at all.

**Evidence.**

- Gate is presence/placeholder only: `packages/paper/src/mm_paper/gates.py` `require_invalidation` — rejects `tbd` / empty; accepts `"Close < 60000 on the daily"` with no parser.
- DB: `packages/memory/src/mm_memory/migrations/versions/0004_phase4_backtest_paper.py` `paper_trade_invalidation_check` = `length(btrim(invalidation)) > 0`.
- Close: `packages/paper/src/mm_paper/ledger.py` — no comparison of `fill_price` / `mark_price` to `record.invalidation`.
- Harness outcome: `tests/unit/test_paper_gates.py` `test_open_and_close_writes_paper_artifacts`
  - invalidation `"Close < 60000 on the daily"`
  - entry fill `65000` / mark `64980`
  - close fill `59900` / mark `60000`
  - `exit_reason="invalidation hit"`
  - No assertion that 59900 vs 60000 vs “daily close < 60000” was evaluated. A daily-close rule cannot be proven from a single mark of `60000` anyway.
- Frozen briefing outcome (not a git thesis; fixture only):
  - `tests/fixtures/briefing/frozen_day.json` theses[0]: slug `THESIS-0001`, status `paper`, instrument `BTC`, `expected_direction` `short`, `invalidation_summary` `"Daily close below 64000"`, hypothesis `"Funding fade after crowding"`.
  - Session BTC last `66100` vs prior close `64800` (`+2.01%`) at close as-of **2026-03-10T20:15:00+00:00**.
  - Rendered: `tests/fixtures/briefing/frozen_close.md` — “lab wrong (so far): expected short BTC, session +2.01%” **and** still prints Invalidation: Daily close below 64000.
  - 66100 is **not** below 64000. Invalidation was not hit; the path was. There is no alert type for either event.
- Watchlist (pre-open, not evaluated on close): `config/briefing/watchlist.yaml` BTC `levels.support: "64000"` / invalidation mentions “daily close below support”.
- Skeptic: `templates/skeptic-review.md` § Invalidation quality — free markdown; `recorded_skeptic_verdict` only reads `pass|revise|reject`.
- Alerts: `packages/briefing/src/mm_briefing/alerts.py` — no invalidation type. Draft sketch: `ops/drafts/alert-types-proposed.yaml` `invalidation_proximity` (disabled, blocked until typed conditions).

**Proposed playbook / test / alert / data change.**

- Playbook: Skeptic rejects invalidation that is not a typed condition (instrument, comparator, level, clock: e.g. `daily_close`, `mark`, `funding`). Paper open continues to require the human sentence **and** (when promoted) a structured field in `intent_json`.
- Data (when promoted, paper ledger only): `invalidation_json` `{metric, comparator, threshold, clock}` alongside the existing text. Do not silently parse English.
- Test: close with `exit_reason="invalidation hit"` while the last mark is on the wrong side of the structured threshold → gate fail or mandatory `exit_reason` mismatch flag. Characterise today’s behaviour first (it succeeds).
- Alert: **do not enable** `invalidation_proximity` until the structured field exists. Enabling a regex against free text would create false confidence.

**Why it matters.** The only mandatory risk control on paper besides max-loss *text* is invalidation. If close can label any exit an invalidation hit, paper cannot teach invalidation performance — the exact post-mortem section.

**How to test (when promoted).** Extend `test_open_and_close_writes_paper_artifacts` with a structured invalidation `{clock: mark, comparator: lt, threshold: 60000}` and assert today’s free-text path still opens (compat) while the new path refuses a lying `invalidation hit`. No live orders.

**Risk of not doing it.** First real paper will repeat the harness: a plausible sentence, an operator exit label, and a close brief that can be “lab wrong” while invalidation is quiet — with no recorded distinction.

**Not for live until reviewed.** No auto-flatten, no live stop orders, no `live.yaml` stop rules. Structured invalidation is a paper/skeptic artifact change only.

---

### P1 — P&L and slippage are operator-supplied; max-loss is not checked at close

**Gap.** Max loss is required to *open*. Realised P&L is optional, not reconstructed from fills, not compared to `max_loss_amount`, and is stuffed into markdown Notes rather than a first-class field. Exit slippage is discarded when entry slippage was already stored.

**Evidence.**

- Open requires positive max loss: `packages/paper/src/mm_paper/gates.py` `parse_max_loss`; DB `paper_trade_max_loss_amount_check`.
- Close P&L: `packages/paper/src/mm_paper/ledger.py` — `pnl` optional; `Decimal(pnl.strip())` if provided; **no** fill-based PnL; **no** `abs(pnl) > max_loss_amount` flag.
- Template: `templates/paper-trade.md` has sections for fills, slippage, marks, exit reason — **no P&L field**. Writer: `packages/paper/src/mm_paper/artifacts.py` appends `P&L: …` into Notes.
- Slippage overwrite / drop: `close_paper_trade` sets `record.slippage_bps` from `--slippage-bps` if passed; else computes exit slippage **only if** `record.slippage_bps is None`. Entry fill+mark therefore **blocks** exit slippage.
  - Harness numbers (`test_open_and_close_writes_paper_artifacts`): entry fill `65000` mark `64980` long → entry slippage `(65000-64980)/64980*10000 ≈ 3.08 bps`. Close fill `59900` mark `60000` (exit sell) would be `(60000-59900)/60000*10000 ≈ 16.67 bps` — **not stored**.
- CLI close without recomputation: `tests/unit/test_paper_cli.py` close `--pnl 25 --slippage-bps 4.5` **without** close fill/mark; operator numbers win.
- Integration: `PaperRepository.close` never exercised; open insert stores `slippage_bps=opened.slippage_bps` with **empty fills** in that test (no `--fill-price`).
- Risk defaults exist but are not consulted by paper: `config/risk/defaults.yaml` `per_thesis_max_loss_bps: 500`, `require_max_loss: true`. `mm_risk` stub does not run. **This proposal does not implement a risk service** (Phase 5 / AGENTS.md).

**Proposed playbook / test / alert / data change.**

- Playbook: Coordinator must not close without entry+exit fill+mark, and must record whether `|pnl|` exceeded `max_loss_amount` (even if the ledger still accepts the close in Phase 4).
- Data (when promoted): compute `pnl_from_fills` when two fills exist; store `pnl_source=operator|fills`; store `max_loss_breached: bool`; keep operator `pnl` for dissent. Add `marks_json` on `paper_trade` (see P3) so reconstruction does not depend on git alone.
- Test: close with `pnl=-999` against `max_loss=500 USDC` currently succeeds — lock that characterisation, then fail or flag when promoted.
- Alert: none until paper is real; a “max-loss breached on paper” brief type would be a later briefing change, not this PR.

**Why it matters.** Max-loss is the other half of the paper DoD. If close can omit P&L or contradict fills, the post-mortem “expected vs realised P&L / slippage” section cannot be audited.

**How to test (when promoted).** Unit test on `compute_slippage_bps` already exists indirectly via open; add close-path assertions for the 3.08 vs 16.67 bps pair above. Integration: open with fill/mark, close with fill/mark, `PaperRepository.close`, assert both slippages or an `entry_slippage_bps` + `exit_slippage_bps` split.

**Risk of not doing it.** First loss larger than the stated max will still be `status=closed` with whatever `--pnl` the operator typed (or null). Slippage learning will systematically ignore exits.

**Not for live until reviewed.** Do not wire `config/risk/environments/live.yaml`. Do not submit flatten orders. Paper flags only.

---

### P2 — No point-in-time knowledge snapshot at paper entry (unknowns at entry are unrecoverable)

**Gap.** Post-mortem requires “Unknowns at entry”. Open stores `entry_thesis_snapshot_hash` (hash of thesis markdown artifacts), not the observation set known at `opened_at`. Partial/missing metrics that briefing already knows how to flag are not copied onto the trade.

**Evidence.**

- Open record fields: `packages/paper/src/mm_paper/models.py` `PaperTradeRecord` — no `as_of_knowledge`, no observation ids, no data-quality snapshot.
- PIT API today (main): `packages/memory/src/mm_memory/queries.py` — `what_did_we_know(ts) = ingested_at <= ts`. (PR #6 proposes `as_of_knowledge <= T` with lockstep `as_of_knowledge = ingested_at`. This scan **does not merge or reimplement that**. When #6 lands, entry snapshots should use the same watermark the rest of the lab uses.)
- Frozen ETH hole (session 2026-03-10): `tests/fixtures/briefing/frozen_day.json` ETH `open_interest.value: null`, `data_quality: "partial"`, observation_id `01FROZENETHOI0000000000001`. Close brief: `tests/fixtures/briefing/frozen_close.md` — “Open interest: missing (Δ n/a; obs 01FROZENETHOI0000000000001)”, overall **Data quality: partial**.
- Watchlist already encodes the no-trade: `config/briefing/watchlist.yaml` ETH `no_trade: "ETH open_interest is missing or partial"`. That string is pre-open commentary, not a gate on `lab paper open`, and not copied into paper JSON.
- Quality helper: `packages/provenance/src/mm_provenance/quality.py` — missing fields → `partial`; `published_at is None` → `partial`. Paper open does not call it.
- Fixture thesis `THESIS-0002` is `in_research` / long ETH with invalidation “ETH underperforms BTC by 3% on a US session close” — cannot be scored on OI at all on this frozen day.

**Proposed playbook / test / alert / data change.**

- Playbook: on paper open, Coordinator records the output of `lab what-did-we-know --at <opened_at>` for the instrument (observation ids + data_quality) into `paper/<id>-entry-knowledge.json`.
- Data (when promoted): `entry_as_of_knowledge`, `entry_observation_ids`, `entry_data_quality` on the git JSON (DB columns later). Filter with the same PIT function briefing uses. After PR #6 merges, use `as_of_knowledge`, not a third clock.
- Test: open paper against a memory session that contains the frozen ETH OI-null observation; assert the entry snapshot lists `01FROZENETHOI0000000000001` as partial/missing value.
- Alert: draft `instrument_data_partial` in `ops/drafts/alert-types-proposed.yaml` — **disabled**. Promoting it is a briefing config change, Principal-reviewed, not this PR.

**Why it matters.** If we do not snapshot knowledge at entry, post-mortem “unknowns at entry” will be reconstructed from whatever is in the database *now*, including later ingest — the exact look-ahead the lab forbids (`ingested_at` / `available_at` contracts).

**How to test (when promoted).** Fixture ingest + `what_did_we_know` at `2026-03-10T12:00:00Z` vs `2026-03-10T20:15:00Z`; paper open at the earlier stamp must not see later observations. Do not wait for live data.

**Risk of not doing it.** First paper open during a partial ETH book will look clean in `paper/<id>.json`. A later complete OI print will be mistaken for knowledge we had at entry.

**Not for live until reviewed.** Snapshot is read-only Market Memory. No overlap with PR #6’s object-store fail-closed work beyond “use the same PIT definition once it merges”.

---

### P2 — Alert surface misses crowding, path-break, data-quality, and does not honour `window_minutes`

**Gap.** Alerts are correctly fail-closed (no push without numeric thresholds). The two enabled types do not cover the frozen-day events that matter for the fixture paper thesis, and `window_minutes` is config theater.

**Evidence.**

- Enabled types: `config/briefing/alerts.yaml` — `liquidation_spike.min_size: 1.0`, `window_minutes: 60`; `funding_oi_divergence.min_abs_funding: 0.0003`, `min_oi_change_pct: 5.0`.
- Evaluator: `packages/briefing/src/mm_briefing/alerts.py` — only those two type names. `_liquidation_spike` sums **all** `state.liquidations`; `window_minutes` is copied into `event.threshold` metadata and **never used as a filter**. Memory path uses a hard-coded 18h lookback: `packages/briefing/src/mm_briefing/hl.py` `hl_from_memory(..., lookback=timedelta(hours=18))`.
- Frozen BTC crowding (would matter for `THESIS-0001` “Funding fade after crowding”):
  - funding `0.0004` obs `01FROZENBTCFUNDING00000001` (threshold 0.0003 **crossed**)
  - OI `1200.5` vs prior `1000.0` → **+20.05%** obs `01FROZENBTCOI0000000000001` / `01FROZENBTCOIPRIOR00000001` (threshold 5.0 **crossed**)
  - **same sign** → `funding_oi_divergence` correctly does **not** fire: `tests/unit/test_brief_alerts.py` `test_funding_oi_divergence_requires_opposite_signs_and_thresholds` (`reason="no_threshold_crossed"`).
  - There is **no** same-sign crowding alert. Draft: `ops/drafts/alert-types-proposed.yaml` `crowding_funding_oi` (enabled: false).
- Frozen BTC liquidation **would** fire: size `2.50` obs `01FROZENBTCLIQ000000000001` at `2026-03-10T11:40:00+00:00` vs `min_size: 1.0` — `test_liquidation_spike_respects_min_size`. That event is not attached to any paper trade or thesis slug.
- Frozen close path-break: `THESIS-0001` expected short, session BTC `+2.01%` at **2026-03-10T20:15:00Z** — rendered in the close brief, **not** an alert (`generate_close` does not call `evaluate_alerts`).
- Frozen ETH partial OI: watchlist `no_trade` matches; no alert (see P2 knowledge).
- Alert persistence: `generate_alerts` writes `briefs/.../alert.md` only if `decision.pushed`; `brief.payload_json` stores kind + content_hash, not event identity hashes or observation ids as first-class columns. Dedup is in-memory `prior_identity_hashes`.

**Proposed playbook / test / alert / data change.**

- Playbook: on alert-check, Coordinator records identity_hash + observation ids against any **open** paper on that instrument (manual until a join table exists).
- Alert (when Principal promotes, separate PR): enable `crowding_funding_oi` with the same numeric thresholds as divergence but **same sign**; keep `require_threshold_config: true`. Implement `window_minutes` as a real filter on liquidation `market_time` (or refuse to document it until then).
- Alert (later): `thesis_path_break` on close-kind only, using `min_abs_session_move_pct` — still threshold-gated, still no free-text commentary.
- Test: frozen_day + proposed crowding type must push BTC with evidence ids `01FROZENBTCFUNDING00000001` and `01FROZENBTCOI0000000000001`. Characterise that **today** `evaluate_alerts` with production YAML does not. Liquidation window: a liq older than `window_minutes` must not count once the filter exists; today it would.
- Data: persist `AlertEvent.identity_hash` and evidence observation ids on the `brief` row or a child table so dedup survives process restart.

**Why it matters.** The lab’s only canned “paper thesis” in fixtures is a crowding fade. On the canned day, crowding is visible in HL metrics and **silent** in alerts; the close brief notices the path-break hours later with no threshold event. That is the alert hole we will replay on the first real US session.

**How to test (when promoted).** Reuse `tests/unit/test_brief_alerts.py` + `frozen_day.json`. Do not change `config/briefing/alerts.yaml` in the same PR as an unreviewed threshold. Golden `frozen_preopen.md` / `frozen_close.md` hashes must not churn unless the renderer change is intentional (`docs/runbooks/market-pulse.md`).

**Risk of not doing it.** Intraday crowding and partial books stay in pre-open prose. Operators will only notice at 16:15 NY close. `window_minutes: 60` will keep implying a 60-minute liq window that is actually “all liqs in the HL state / 18h”.

**Not for live until reviewed.** **Do not** copy `ops/drafts/alert-types-proposed.yaml` into `config/briefing/alerts.yaml` from this PR. No push channel beyond existing brief files. No execution.

---

### P3 — Paper DB row is not a complete outcome record (marks, close path, backtest link, risk snapshot)

**Gap.** Even after P1–P2, Market Memory cannot answer “what did this paper do?” without the git JSON. Integration tests never close. Backtests do not bind to paper. Risk config version is not snapshotted (and must not become a live risk service in this phase).

**Evidence.**

- Model: `packages/memory/src/mm_memory/models.py` `PaperTrade` — `fills_json`, `expected_path`, `realised_path`, `pnl`, `slippage_bps`, `exit_reason`; **no** `marks_json`, **no** `research_run_id`, **no** `risk_config_version`, **no** `side` column (side lives in `intent_json` only).
- Insert: `packages/memory/src/mm_memory/paper_repository.py` `insert` — no marks argument.
- Integration outcome: `tests/integration/test_phase4_backtest_paper.py` records a `research_run` (kind `backtest`, `params_hash` from `BuyHoldStrategy` on `tests/fixtures/backtest/clean_bars.json`) and a **separate** open `paper_trade` with `invalidation="Close < 60000 on the daily"` — no FK between them; paper never closed.
- Backtest metrics exist (`final_equity`, `total_return`, `max_drawdown`, `n_fills`) in `packages/backtest/src/mm_backtest/harness.py` `BacktestResult.summary` — paper close does not ingest them.
- Risk stub: `packages/risk/src/mm_risk/__init__.py` `__phase__ = 0`. Defaults file `config/risk/defaults.yaml` is unused by `open_paper_trade`. **Out of Phase 4 to build the risk service**; in scope to *propose* copying `schema_version` from **non-live** config into paper `intent_json` as an audit string.
- Realised path: `packages/paper/src/mm_paper/ledger.py` appends only `exit:{reason}@{iso}`. Expected checkpoint `"funding mean-reverts in 48h"` (`test_lab_paper_open_close_list`) is never marked hit/miss.

**Proposed playbook / test / alert / data change.**

- Playbook: list command should show `pnl`, `exit_reason`, and “post-mortem: missing|present”. Already prints pnl when using DB; git `--no-db` list returns raw JSON (ok).
- Data (when promoted): `marks_json`; `entry_slippage_bps` / `exit_slippage_bps`; optional `research_run_id`; `expected_path` items become `{text, status}`. Snapshot `risk_defaults_schema_version` from `config/risk/defaults.yaml` only — **never** from `live.yaml` in Phase 4.
- Test: integration close round-trip; assert marks survive in git JSON **and** DB once the column exists. Do not add `mm_execution` imports (`tests/unit/test_stub_imports.py` already guards research_kit).

**Why it matters.** Git is the review source, but analogues and “query closed paper with |pnl| > max_loss” need Postgres. The integration test currently proves we can **open**.

**How to test (when promoted).** Extend `test_research_run_and_paper_trade_persist` to call `close_paper_trade` + `PaperRepository.close` and assert `exit_reason`, fills, realised_path. Keep `live_trading_enabled` false.

**Risk of not doing it.** Closed-trade queries will disagree with git; marks used for slippage reconstruction (P1) will vanish if the markdown is not committed.

**Not for live until reviewed.** No risk *service*, no order intent, no `live.yaml`. Schema additions are paper-ledger only and need a new Alembic revision after #6’s `0005_knowledge_lockstep` if that lands first (do not fork the migration graph blindly).

---

## Explicit non-proposals (rejected or deferred)

| Claim | Why rejected / deferred |
|---|---|
| “We lost money on THESIS-0001 last week.” | No git paper artifacts. Fixture `THESIS-0001` is briefing-only. |
| “Enable live stops for invalidation.” | Live hard-gated; would require Principal + `live.yaml` + execution. Out of scope. |
| “Implement the Phase 5 risk service now.” | AGENTS.md Phase 4: do not implement the deterministic risk service. Propose snapshots only. |
| “Merge PR #6 as part of this scan.” | Principal review; fail-closed store is a different cell. Entry snapshots should *consume* #6 after merge. |
| “Turn on crowding alerts in `alerts.yaml` in this PR.” | That would change briefing behaviour without Principal review. Draft only. |
| “Alert on every ‘lab wrong’ hook with no threshold.” | Forbidden: `docs/runbooks/market-pulse.md` / `alerts.yaml` `require_threshold_config`. |
| “Unicorn scoring of these gaps.” | Unicorn is a stub; must not auto-promote. |

---

## Suggested promotion order (for Principal)

1. P1 post-mortem gate + close playbook (`ops/drafts/playbook-paper-close-review.md`).
2. P1 structured invalidation + honest exit-reason flags (paper/skeptic only).
3. P1 fill-reconstructed P&L / split slippage / max-loss breached flag.
4. P2 entry `what_did_we_know` snapshot (after or alongside PR #6 PIT definition).
5. P2 crowding + `window_minutes` + optional data-partial alerts (separate briefing PR, thresholds reviewed).
6. P3 DB completeness (marks, close integration test, optional `research_run` link).

Nothing in that list is a live promotion.

---

## Files in this PR

| Path | Role |
|---|---|
| `ops/README.md` | Convention: proposals/drafts are not live logic. |
| `ops/proposals/2026-09-17-outcome-scan.md` | This scan. |
| `ops/drafts/playbook-paper-close-review.md` | Draft Coordinator close checklist. |
| `ops/drafts/alert-types-proposed.yaml` | Disabled alert sketches; **not** `config/briefing/alerts.yaml`. |
