# ADR 0008 — Phase 6c-2 naming / display layer

- **Status:** Accepted
- **Date:** 2026-09-18
- **Phase:** 6c-2 naming. No live trading. No signing. No Redis. No 6d listings. No 6c-4/6c-5.

## Context

Phase 6c-1 (#49) cut publishing desks to five slugs. Display titles, Telegram banners, PLAYBOOK artifact labels, and sleeve/gate copy still used Phase-5 strings (`Crypto Desk`, `Equities Desk`, skeptic-as-desk, `ladder.<type>` envelope desks). Principal lock: one naming module/config.

## Decision

Canonical names live in `mm_common.naming` and `config/desks/naming.yaml` (tests fail closed if they drift).

| Kind | Machine id | Human label |
|---|---|---|
| Publishing desks | `intel` `research` `quant` `ic_risk` `ops` | Intel (Market Intelligence), Research (Investment Research), Quant, IC/Risk (Investment Committee & Risk), Ops |
| Orchestration | `coord` (not a desk) | Coord (orchestration) |
| Telegram sink | `alerts` | Alerts |
| PLAYBOOK types | `DAILY_BIAS` … `STATE_CARD` | Daily Bias … State Card |
| Sleeves / gates | `crypto` `equities` `chart` `flow` `macro` `briefing` `skeptic` `risk` | Research/Intel sleeve or IC/Risk gate labels |

Unknown slugs and artifact types raise `UnknownNameError`. Mesh NOTIFY payloads stay ids only (`desk` = slug). Human labels are a lookup at render time (Telegram header, pack owner column, CLI).

## Consequences

- Artifacts, Telegram headers, mesh envelopes, CLI, and runbooks import the naming layer instead of string literals.
- Retired Phase-5 slugs are sleeves/gates, not publishing desks.
- Coord remains `coord.assemble` (channel), not a sixth desk.

## Not this ADR

6c-4 watchlist monitor. 6c-5 delivery expansion. 6d listings/IPO. Live/signing/Redis.
