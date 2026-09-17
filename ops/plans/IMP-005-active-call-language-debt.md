# PLAN — IMP-005 Active-call language debt (membership vocabulary)

**Report status:** PR READY  
**Owner:** Don/Quant (Principal + Quant & Market Structure Desk)  
**Scope:** rename/rewrite historical membership + queue language so Principal universe membership is not a Quant/trade call. No orders, wallets, live keys, Pulse/Stooq/FRED code, Quant Board rewrite, or universe expansion.

## Why

IMP-001 locked closed Quant verdicts and banned investment-call language (`active call`, make/buy/sell, high confidence, sizing). Historical files still used Principal-universe field names and prose (`active_calls` / “active call”) that read like trade recommendations. Principal asked to clear that Gap before merging other work.

## Canonical vocabulary

| Term | Where | Meaning |
|---|---|---|
| **controlled_universe** | `config/universe.yaml` (the locked file) | Principal-locked research/ingest universe. Intent-level only — not orders. |
| **membership** | `crypto_perps` ∪ `equities` | Full locked ingest (crypto) / briefing (equities) set. Survivors are not equal priority. |
| **in_universe** | YAML key (was `active_calls`) | Thesis-priority Principal membership. **Not** a Quant verdict. **Not** a trade. |
| **watch_only** | YAML key (unchanged) | Still ingested / still in the controlled universe; no thesis-priority membership. |
| Quant verdicts | Board / cards only | `RESEARCH_PRIORITY` \| `MONITOR` \| `DEFER` \| `REJECT` \| `INSUFFICIENT_DATA` |

### Rename map (old → new)

| Old | New |
|---|---|
| YAML `active_calls` | `in_universe` |
| YAML `watch_only` | `watch_only` (unchanged) |
| Prose “active call(s)” as membership | in-universe membership / thesis-priority membership |
| Prose “call-tier” / “call priority” | membership partition / membership tier |
| Footer “create an `active_call`” | “change universe membership” |
| MAKE as a recommendation | `RESEARCH_PRIORITY` (Quant) or in-universe membership (Principal) |
| WATCH as a recommendation | `MONITOR` or `watch_only` |
| CUT as a recommendation | `REJECT` / `DEFER` (context) |

Membership **ticker sets stay the same** (rename-only key move):

- `in_universe.crypto_perps` = `[BTC]`
- `in_universe.equities` = `[NVDA, AVGO, MSFT, META, JPM, XOM]`
- `watch_only.crypto_perps` = `[ETH, UNI, AAVE]`
- `watch_only.equities` = `[SMH, XLF]`

## Reuse

- Quant language gate stays: `mm_research_kit.quant_review.language` still forbids “active call”, MAKE, buy/sell, high confidence, sizing in **Quant Board output**.
- Cheap lint: templates + canonical membership config keys must not reintroduce `active_calls` / call-recommendation phrases.
- Historical pack **filenames** that contain `active-calls` are retained as evidence ids (citations / git history). Body text uses membership vocabulary. Ban-quoting in IMP-001 lessons and the language gate itself is intentional.

## Engine / artifacts

No new generator. Clean cut on `config/universe.yaml` (no `active_calls` shim). Tests updated to the new key.

## Tests

- `tests/unit/test_scaffold.py` — locked membership sets via `in_universe`.
- `tests/unit/test_membership_vocab.py` — canonical keys are not `active_calls`; templates do not ship forbidden call-language.
- Briefing / source-health no-decision footers no longer say `active_call`.
- Frozen briefing hashes regenerated after footer rewrite.

## Non-goals

IMP-004 Pulse source hardening (#34 PARKED — do not continue). Universe expansion. Quant Board rewrite. MAKE/buy/sell recommendations. Sizing. Execution. `live.yaml`. Secrets. Paid data. Telegram. Invented market prints.
