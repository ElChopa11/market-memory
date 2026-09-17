# PLAN — IMP-007 Dedicated crypto + equities thesis-card templates

**Report status:** PR READY  
**Owner:** Don/Research (Crypto Desk + Equities & Post-IPO Desk)  
**Scope:** dedicated research thesis-card templates (plus copy-into-workspace). No orders, wallets, live keys, Pulse/Stooq/FRED work, universe expansion, Quant Board rewrite, or execution.

## Why

Desk charters name crypto and equity thesis cards as artifacts. Operators only had generic `templates/thesis.md`, which lacks IMP-001 closed verdicts, IMP-005 membership vocabulary, provenance fields, and an Independent Skeptic stub. Queue packs under `research/queue/` are evidence, not reusable desk cards.

## Path choice

| Role | Path |
|---|---|
| Crypto card | `templates/crypto-thesis-card.md` |
| Equities card | `templates/equities-thesis-card.md` |
| Lifecycle spine | unchanged `templates/thesis.md` + `lab thesis new` |
| Copy-into-workspace | `mm_research_kit.thesis_cards` (desk file beside `thesis.md`) |
| Runbook | `docs/runbooks/thesis-cards.md` |

Do **not** replace `thesis.md`. Lifecycle DoD (`intent` → `thesis.md` → plan → evidence → skeptic) stays on the generic spine. Desk cards are the desk-specific research surface.

`lab thesis new --instrument BTC` (with `config/universe.yaml` readable from `--repo-root`) copies `crypto-thesis-card.md`. Equity membership names copy `equities-thesis-card.md`. Unknown / non-membership names get no extra card.

## Card contract

Both cards include:

- Principal membership: `in_universe` | `watch_only` | `deferred_must_cut` | `not_in_membership` (IMP-005 keys; not a Quant verdict)
- Closed Quant verdicts (IMP-001): `RESEARCH_PRIORITY` | `MONITOR` | `DEFER` | `REJECT` | `INSUFFICIENT_DATA`
- Provenance table (source, timestamp, capture, evidence_confidence, observation id)
- Knowledge watermark `as_of_knowledge` (never `published_at` / `market_time`)
- Independent Skeptic stub (`pending`, never a faked pass)
- Explicit non-goals: no sizing, no execution, no investment-call language, no universe edits

Crypto card: HL structure placeholders (funding / OI / basis) stay `unavailable` until evidenced. Public `/info` only.

Equities card: filings / peers / liquidity stay `unavailable` until evidenced. Post-IPO reclaim remains IMP-006’s screen; this card is not that product. Drawdown is not a thesis.

## Language

Same gate as Quant output (`mm_research_kit.quant_review.language`) plus template lint in `tests/unit/test_membership_vocab.py`. Forbidden: active call, MAKE, buy, sell, high confidence, sizing / order instruction language.

## Tests

See `tests/unit/test_thesis_cards.py`. Scaffold requires both templates. Membership pin must match `config/universe.yaml` (no ticker expansion).

## Non-goals

Pulse / Stooq / FRED. Universe expansion. Quant Board rewrite. MAKE / investment-call recommendations. Sizing. Execution. `live.yaml`. Secrets. Paid data. Telegram. ToS-violating scrapes. Replacing generic `thesis.md`. Filings/earnings ingest (still a Data-desk gap).

## Limitations

- Generic `thesis.md` remains required for lifecycle.
- No equity-feed ingest; equities evidence is named sources or `unavailable`.
- Desk-card copy needs `config/universe.yaml` at `--repo-root` (tests that use an empty tmp root still create the generic spine only).
