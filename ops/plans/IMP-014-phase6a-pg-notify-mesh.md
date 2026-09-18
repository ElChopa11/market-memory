# PLAN — IMP-014 Phase 6a PG LISTEN/NOTIFY mesh

**Report status:** IN_REVIEW (this PR).  
**Owner:** Don / Chief of Staff (Coordinator)  
**Scope:** Desk protocol hardening + Postgres `LISTEN/NOTIFY` bus + Coord worker stub. No live trading. No execution. No `live.yaml`. No Redis. No Phase 6b market-data.

## Why

Phase 5e delivers Telegram as a single Coordinator channel. Per-desk workers have no durable notify bus. Principal lock: **bus = Postgres LISTEN/NOTIFY (no Redis)**; one phase per PR.

## Outcome

- Queue: IMP-013 DONE (#44). This item the implementation thread. IMP-015 Phase 6b parked.
- `DeskOutput` envelope header: desk, as_of UTC+Sydney, status, n, completeness, regime placeholder `unset`, `op=paper|observation`, universe, sources/missing. Cadence metadata from `config/desks/cadence.yaml`.
- `content_hash` idempotency: same `as_of` + observations → identical hash. `envelope_id` is not hashed.
- Bus: Postgres `LISTEN/NOTIFY` only. Channels `desk.<slug>.output`, `desk.<slug>.alert`, `coord.assemble`, `dq.event`. Envelopes persist in `desk_envelope` / `desk_health`. NOTIFY carries ids/keys only.
- Coord worker stub: subscribe, track health, assemble daily pack from Memory. Missing/killed desk → `FAILED` + `error_class`.
- CLI: `lab mesh dry --fixture --no-db` (and `--kill-desk`). `lab desk run` unchanged default `--no-send`.
- ADR 0004. Runbook mesh section. README Phase 6 in progress (6a).
- Import walls unchanged. No Redis client. No secrets.

## Tests

- `tests/unit/test_phase6a_envelope.py` — header fields, double-run hash
- `tests/unit/test_phase6a_mesh.py` — killed/missing desk FAILED + error_class
- `tests/unit/test_phase6a_cli.py` — `lab mesh dry` / channels
- `tests/unit/test_phase6a_queue.py`
- `tests/integration/test_phase6a_pg_notify.py` — persist + LISTEN/NOTIFY + idempotency

## Gates kept

`live_trading_enabled: false`. risk-config-guard. promote-gate. PIT. degrade-never-invent. No secrets in git. Import walls. Ask before any new network/keys/order dependency.

## Non-goals

Redis. Flow/macro packages (6b). Per-desk Telegram fan-out (6c). Listings/IPO desk (6d). Scorecards (6e). Decay/prompt versioning (6f). Live trading. Signing. Order endpoints. Paid deps. Reopening IMP-013 except queue hygiene.

## Status

IN_REVIEW (this PR). IMP-013 is DONE (#44). IMP-015 Phase 6b is READY/PARKED — do not implement flow/macro/regime here.
