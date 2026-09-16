# Research lifecycle

Artifacts live under `research/YYYY/THESIS-XXXX/` and are copied from `templates/`. Market Memory (later phase) stores content hashes so git and Postgres stay linked.

## Status machine

`draft` → `in_research` → `in_skeptic` → `paper` → `live` (Principal only) → `retired`

Any stage may go to `rejected`. Rejected theses stay queryable learning records.

## Artifact chain and definition of done

`scripts/check-lifecycle.sh` enforces predecessor gates. It **refuses to advance** (exits non-zero) when a later artifact exists without its required earlier artifacts.

### 1. Intent (`intent.md`) — enter `draft`

**DoD**

- Goal in one sentence.
- Why now / trigger observation ids (or explicit “no observation yet”).
- Out of scope listed.
- Definition of done for moving to thesis.
- Owner, `opened_at`, deadline.

Without intent, **thesis is forbidden**.

### 2. Thesis (`thesis.md`) — enter `in_research`

**Requires:** `intent.md`

**DoD**

- Hypothesis, why now, why the market may be wrong or late.
- Evidence list (observation ids + links; may be empty only while still draft — Phase 2 will require links before skeptic).
- Expected path, catalyst, instrument (BTC or ETH perp in v1), time horizon.
- Invalidation, risks / alternative explanations, what would change our mind.
- Status / version.

### 3. Research plan (`research-plan.md`)

**Requires:** `thesis.md`

**DoD**

- Questions to answer; data needed + sources.
- Tests / backtests planned; skeptic focus areas.
- Budget (time, compute); stop conditions.

### 4. Evidence and backtests (`evidence/`, `backtests/`)

**Requires:** `research-plan.md` if any evidence or backtest files are present.

**DoD (Phase 2+; recorded now)**

- Evidence files cite observation ids.
- Backtests record `params_hash`. Same hash must reproduce the same result (Phase 4).
- No look-ahead: knowledge watermark is `ingested_at`.

### 5. Skeptic review (`skeptic-review.md`) — enter `in_skeptic`

**Requires:** `research-plan.md`

**DoD**

- Verdict is exactly `pass`, `revise`, or `reject`.
- Bias / leakage / look-ahead, crowding, liquidity/leverage/slippage, alternatives, already-priced evidence, invalidation quality.
- Required fixes before paper if not `pass`.
- Author of the thesis is not the sole skeptic of record.

Cannot mark paper without a `pass` verdict (enforced in later phases; file presence gated now).

### 6. Paper trade (`paper/` or `paper-trade.md`) — enter `paper`

**Requires:** `skeptic-review.md`

**DoD**

- Thesis id + entry snapshot hash.
- Size, max loss, invalidation (paper **cannot** open without these — Phase 4).
- Expected path checkpoints; fills / slippage / marks; exit reason.

### 7. Promotion (`promotion-decision.md` or `promotion.md`)

**Requires:** a paper artifact

**DoD**

- Paper results summary; risk config version.
- Principal approval (signed commit or recorded approval).
- Live size cap; monitoring plan; halt conditions.
- Dual control: Risk allow is not a substitute for this record.

Live remains **hard-gated** in Phase 0. This artifact is the future gate, not a license to trade.

### 8. Post-mortem (`post-mortem.md`)

**Requires:** paper or promotion artifact

**DoD**

- Expected vs actual path; expected vs realised P&L / slippage.
- Signal quality; risk decision quality; invalidation performance.
- Unknowns at entry.
- Proposed changes (tests, alerts, data, playbook) — **not auto-applied**.
- Closed paper/live thesis requires post-mortem **before any size increase** (Phase 7).

### Unicorn card (`unicorn-card.md`) — optional side path

Unusual / overlooked candidates. Independent evidence (≥2 types), disproof, catalyst, positioning, instrument + liquidity, holding period, risk-defined expression, promotion gate to paper. Does not bypass skeptic or risk.

## Checker behaviour

```bash
./scripts/check-lifecycle.sh
```

- Verifies `templates/` are present.
- Walks `research/` thesis workspaces.
- Fails if `thesis.md` exists without `intent.md` (and similarly for later stages).
- Empty `research/` is valid in Phase 0.

## Control-plane reminders

- Research writes artifacts only; it cannot approve risk or hold live keys.
- Risk never uses an LLM at order time.
- Execution (later) accepts only typed intents that already passed Risk.
- All promotions are git-reviewed + Principal-signed.
