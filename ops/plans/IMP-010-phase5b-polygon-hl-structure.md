# PLAN — IMP-010 Phase 5b Polygon equities + HL structure

**Report status:** DONE (#41)  
**Owner:** Don/Data (Data & Market Memory Desk) + Crypto / Equities desks as consumers  
**Scope:** Polygon as default equities vendor; Hyperliquid funding / OI / basis / depth; optional public spot cross-check; FRED + fixture calendar. Read-only. No Telegram. No execution. No `live.yaml`.

## Why

Phase 5a committed desk boundaries only. Equities still had no durable tape in Memory. Crypto structure (funding, OI, basis, depth) was not a standing ingest product. Principal lock: **equities default = Polygon** (Ask is N/A).

## Path choice

| Role | Path |
|---|---|
| Equities adapter (swappable) | `packages/ingest/src/mm_ingest/equities/` (`mm_ingest`, not `mm_desks`) |
| Polygon default | `PolygonEquitiesAdapter`; registry default `polygon` |
| HL structure | `mm_ingest.structure` + `l2Book` on `/info` allowlist |
| Spot DQ | `mm_ingest.spot` (CoinGecko / Binance **public**) |
| Macro | `mm_ingest.macro` (FRED env-only; calendar fixture) |
| Rate limits | `config/ingest.yaml` `rate_limits.*` |
| Fixtures | `tests/fixtures/phase5b/` |
| Adversarial PIT | `tests/adversarial/test_phase5b_point_in_time.py` |
| Runbook | `docs/runbooks/polygon-hl-structure.md` |

## Tests

See `tests/unit/test_phase5b_ingest.py`, `tests/unit/test_phase5b_queue.py`, `tests/adversarial/test_phase5b_point_in_time.py`. Source-health inventory includes `polygon`, `binance.public`, `hyperliquid.structure`.

## Gates kept

`live_trading_enabled: false`. risk-config-guard. promote-gate. PIT law (`as_of_knowledge` = `ingested_at`). Degrade-never-invent. No secrets in git. Import-boundary CI. No new network library (httpx only).

## Non-goals

Desk full runners (5d). Quant factor library (5c). Telegram / 5e. Signing / `hl_trade`. Risk service. Live path. Paid deps without Principal ask. Redis. Reopening IMP-009 docs except queue hygiene.

## Status

DONE (#41). IMP-011 Phase 5c is IN_REVIEW on the following PR — do not implement factors here.
