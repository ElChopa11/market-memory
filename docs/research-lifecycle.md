# Research lifecycle

Artifacts live under `research/YYYY/THESIS-XXXX/` and are copied from `templates/`. Market Memory stores content hashes, thesis indexes, and `thesis_evidence` links so git and Postgres stay joined. Git remains the human-review source.

## Status machine

`draft` → `in_research` → `in_skeptic` → `paper` → `live` (Principal only; later phase) → `retired`

Any stage may go to `rejected`. **Rejected theses stay queryable learning records** (git workspace retained; `lab thesis list --status rejected`). Revival requires a new intent, not a silent reopen.

**Skeptic FAIL:** `revise` **returns** the thesis to `in_research`; `reject` **archives** it as `rejected`. **Risk BLOCK** is terminal without Principal override (no paper/live). **No self-approve.**

Phase 4/5a implements through paper. `live` remains later and the CLI refuses it.

Transition log hook (Market Memory `thesis_status_event`): `actor`, `ts`, `reason` plus from/to status. `lab thesis advance` writes the row when DB is connected. Shape: `mm_research_kit.state_machine.TransitionLog`.

## Artifact chain and definition of done

`scripts/check-lifecycle.sh` enforces predecessor gates. It **refuses to advance** (exits non-zero) when a later artifact exists without its required earlier artifacts, and when status is `in_skeptic` (or `paper`/`live`) without evidence links.

### 1. Intent (`intent.md`) — enter `draft`

**DoD**

- Goal in one sentence.
- Why now / trigger observation ids (or explicit “no observation yet”).
- Out of scope listed.
- Definition of done for moving to thesis.
- Owner, `opened_at`, deadline.

Without intent, **thesis is forbidden**. `lab thesis new` always writes intent first.

### 2. Thesis (`thesis.md`) — enter `in_research`

**Requires:** `intent.md`

Create from intent in one command:

```bash
uv run lab thesis new --goal "…" --owner Research --instrument BTC
```

**DoD**

- Hypothesis, why now, why the market may be wrong or late.
- Evidence list (observation ids + links; may be empty only while still `draft`/`in_research`).
- Expected path, catalyst, instrument (BTC or ETH perp in v1), time horizon.
- Invalidation, risks / alternative explanations, what would change our mind.
- Status / version.

Desk-specific companions (IMP-007; not a substitute for `thesis.md`): `crypto-thesis-card.md` or `equities-thesis-card.md` when `--instrument` is in locked membership. See [runbooks/thesis-cards.md](runbooks/thesis-cards.md).

### 3. Research plan (`research-plan.md`)

**Requires:** `thesis.md`

**DoD**

- Questions to answer; data needed + sources.
- Tests / backtests planned; skeptic focus areas.
- Budget (time, compute); stop conditions.

### 4. Evidence and backtests (`evidence/`, `backtests/`)

**Requires:** `research-plan.md` if any evidence or backtest files are present.

**DoD (Phase 4)**

- Evidence files cite observation ids (`evidence/links.md` plus Market Memory `thesis_evidence`).
- Link via `lab thesis link-evidence THESIS-XXXX --observation <id> --role supports|opposes|context`.
- Backtests record `params_hash` (`lab backtest run`). No look-ahead: bar knowledge watermark is `available_at`; observations use `ingested_at`.

### 5. Skeptic review (`skeptic-review.md`) — enter `in_skeptic`

**Requires:** `research-plan.md` **and at least one evidence link**. Cannot mark `in_skeptic` without evidence links.

```bash
uv run lab skeptic open THESIS-XXXX --reviewer Skeptic
uv run lab skeptic record THESIS-XXXX --verdict pass|revise|reject --reviewer Skeptic
```

**DoD**

- Verdict is exactly `pass`, `revise`, or `reject`.
- Bias / leakage / look-ahead, crowding, liquidity/leverage/slippage, alternatives, already-priced evidence, invalidation quality.
- Required fixes before paper if not `pass`.
- Author of the thesis is not the sole skeptic of record.

Cannot mark paper without a `pass` verdict. Runbook: [runbooks/research-workspace.md](runbooks/research-workspace.md).

### 6. Paper trade (`paper/` or `paper-trade.md`) — enter `paper`

**Requires:** `skeptic-review.md` with verdict `pass`, evidence links, **invalidation**, and **max loss**.

```bash
uv run lab paper open THESIS-XXXX \
  --size 0.01 \
  --max-loss "500 USDC" \
  --invalidation "BTC daily close < 60000"
```

**DoD**

- Thesis id + entry snapshot hash.
- Size, max loss, invalidation (paper **cannot** open without these).
- Expected path checkpoints; fills / slippage / marks; exit reason.

`live` remains **hard-gated**. Runbook: [runbooks/paper-trade.md](runbooks/paper-trade.md). Backtest runbook: [runbooks/backtest.md](runbooks/backtest.md).

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

- Verifies `templates/` are present (including `evidence-links.md`).
- Walks `research/` thesis workspaces.
- Fails if `thesis.md` exists without `intent.md` (and similarly for later stages).
- Fails if status is `in_skeptic` (or `paper`/`live`) without rows in `evidence/links.md`.
- Empty `research/` is valid. Rejected workspaces must remain and still pass predecessor checks.

Coordinator CLI: `lab thesis new|link-evidence|advance|list`, `lab skeptic open|record`, `lab backtest run`, `lab paper open|close|list`. See [runbooks/research-workspace.md](runbooks/research-workspace.md).

## Control-plane reminders

- Research writes artifacts only; it cannot approve risk or hold live keys.
- Risk never uses an LLM at order time.
- Execution (later) accepts only typed intents that already passed Risk.
- All promotions are git-reviewed + Principal-signed.
- Desk pipeline and Principal-only gates: [ops/desk-charters.md](../ops/desk-charters.md), [ops/decision-rights.md](../ops/decision-rights.md).
