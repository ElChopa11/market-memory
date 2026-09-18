# mm-macro

Phase 6b **macro regime + calendar** library (IMP-015). Macro & Cross-Asset Desk.

**May:** classify a cross-asset regime tag from **explicit YAML thresholds** (`config/macro/regimes.yaml`) using two driving inputs (VIX + DXY); surface FRED/curve/credit/commodities when present; tag `EVENT_RISK` within N minutes of high-impact calendar events.

**Must not:** invent missing FRED/Stooq/calendar feeds; depend on `mm_execution`; treat a regime tag as a call or allocation.

Config: [`config/macro/regimes.yaml`](../../config/macro/regimes.yaml).

Runbook: [../../docs/runbooks/macro-desk.md](../../docs/runbooks/macro-desk.md).

Missing feeds → `unavailable` / `DEGRADED`. Never invent.
