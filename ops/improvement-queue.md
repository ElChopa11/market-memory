# Continuous-improvement queue

Source of truth for Principal-adopted **permanent** continuous-improvement ops.

## Operating model

- **Single-threaded:** at most one IMP is `IN_PROGRESS` at a time. Park everything else.
- **Priority:** P0 > P1 > P2. Do not start a lower item while a higher open item is unblocked.
- **Agent reports to Principal:** only `PLAN` | `BLOCKED` | `PR READY` | daily digest. No status novels.
- **No autonomous trading.** This queue does not authorize orders, wallets, live keys, strategy promotion, or execution. Research stays read-only unless a later IMP explicitly changes mandate (Principal + git review).

Item schema (every item): **ID, Priority, Type, Problem, Evidence, Proposed outcome, Definition of done, Non-goals, Dependencies, Risk level, Status, Owner, PR, Lesson learned.**

Status values: `BACKLOG` | `IN_PROGRESS` | `IN_REVIEW` | `BLOCKED` | `DONE`.

---

## IMP-001

- **ID:** IMP-001
- **Priority:** P1
- **Type:** research quality
- **Problem:** The lab needs a disciplined Quant Review Board — a decision board, not a call generator. Watchlist names were being discussed with call/MAKE language and with “arbitrage” / “bullish reclaim” used loosely.
- **Evidence:** Principal-approved TradingView watchlists (crypto USDC.P perps + cross-asset/US list) attached to this IMP; QUANT-20260917 active-calls pack still uses call-tier language (`research/queue/QUANT-20260917-active-calls.md`); locked ingest universe is a different, smaller membership (`config/universe.yaml`).
- **Proposed outcome:** Read-only Quant Review Board with four tracks, controlled verdicts/reason codes, persisted Quant Cards, and `lab quant-review`. RESEARCH_PRIORITY means “deeper thesis pack next,” never paper/live.
- **Definition of done:**
  - Queue file exists with this schema; this item is the single in-flight IMP.
  - `config/quant_review_universe.yaml` is the review-board input universe (screenshot-derived; does **not** expand locked ingest `config/universe.yaml`).
  - Generator CLI: `lab quant-review` (fixture-first, optional Market Memory overlay).
  - One Quant Card per reviewed name; board at `research/quant/YYYY-MM-DD/quant-review-board.md`.
  - Verdicts exactly one of `RESEARCH_PRIORITY | MONITOR | DEFER | REJECT | INSUFFICIENT_DATA`; every verdict has a controlled reason code.
  - Sector-relative opportunity labeled **relative-value candidate** or **reclaim candidate**, never `ARBITRAGE` unless Track D criteria are fully met.
  - “Bullish reclaim” requires explicit multi-session observables; one-day bounce is not a reclaim.
  - Promotion MONITOR→RESEARCH_PRIORITY only when all promotion criteria hold; Independent Skeptic review is a checklist field (not a faked pass).
  - Board has ≤3 `RESEARCH_PRIORITY`; executable-arbitrage list usually empty; post-IPO reclaim list is MONITOR unless promotion criteria met.
  - Board footer exactly: `Research only. Not a trade instruction, allocation decision, or execution approval.`
  - Tests: no data → INSUFFICIENT_DATA; stale data blocks promotion; ordinary relative-value ≠ ARBITRAGE; post-IPO underperformance alone ≠ RESEARCH_PRIORITY; every verdict has a reason code; output has no trade sizing, order language, or active-call/MAKE language.
  - Sample board + cards committed from the approved universe.
- **Non-goals:** Not a call generator. No MAKE / active-call / confidence-as-verdict. No trade sizing, orders, wallets, account endpoints, live keys, or strategy promotion. Does not unlock ingest membership. Does not implement US Market Pulse (IMP-002). Does not rewrite QUANT-20260917 packs.
- **Dependencies:** Existing research_kit artifacts, briefing data-quality vocabulary, optional QUANT-20260917 overlay for overlapping names, optional Market Memory `what_did_we_know` (as_of_knowledge lockstep with ingested_at).
- **Risk level:** Low (read-only research artifacts; no execution surface).
- **Status:** IN_PROGRESS
- **Owner:** Don/cloud
- **PR:**
- **Lesson learned:**

---

## IMP-002

- **ID:** IMP-002
- **Priority:** P1
- **Type:** reliability
- **Problem:** US Market Pulse vertical slice is unfinished; parked so this queue stays single-threaded.
- **Evidence:** Prior cloud agent was stopped for single-thread discipline; Phase 3 Market Pulse exists (`lab brief preopen|close|alert-check`) but the US vertical-slice IMP was not completed in-repo.
- **Proposed outcome:** A scoped US Market Pulse vertical slice (DoD to be written when this item is pulled).
- **Definition of done:** TBD when IMP-002 is unparked. Do not invent scope here.
- **Non-goals:** Do not start while IMP-001 is in flight. No live trading.
- **Dependencies:** IMP-001 complete (single-thread). Existing `packages/briefing` + `lab brief`.
- **Risk level:** Medium (session-clock / data-quality surface; still read-only).
- **Status:** BACKLOG
- **Owner:** unassigned
- **PR:**
- **Lesson learned:** Parked; prior cloud agent stopped for single-thread.

---

## IMP-003

- **ID:** IMP-003
- **Priority:** P2
- **Type:** research quality
- **Problem:** Open call-language debt: QUANT active-calls packs and locked-universe notes still say “active calls,” which the Quant Review Board now forbids as verdict/call language.
- **Evidence:** `research/queue/QUANT-20260917-active-calls.md` (title + “ACTIVE CALLS only”); `config/universe.yaml` keys `active_calls` / notes; README “active calls (thesis priority).” Board output must not emit MAKE / active-call language (`mm_research_kit.quant_review.language`).
- **Proposed outcome:** Later, retire call-tier wording in packs and human docs; keep ingest membership keys stable or alias them. Review-board language (relative-value / reclaim / unexecutable arb) is canonical going forward.
- **Definition of done:** TBD when pulled. Must not break `tests/unit/test_scaffold.py` universe lock without an explicit Principal note.
- **Non-goals:** Not in this PR. Do not rewrite QUANT-20260917 numbers. Do not expand ingest universe.
- **Dependencies:** IMP-001 merged (language gate exists).
- **Risk level:** Low (docs/config wording; lockfile of membership must stay).
- **Status:** BACKLOG
- **Owner:** unassigned
- **PR:**
- **Lesson learned:**
