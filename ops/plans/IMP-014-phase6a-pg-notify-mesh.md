# PLAN — IMP-014 Phase 6a PG LISTEN/NOTIFY mesh

**Report status:** DONE (#45).  
**Owner:** Don / Chief of Staff (Coordinator)  
**Scope:** Desk protocol hardening + Postgres `LISTEN/NOTIFY` bus + Coord worker stub. No live trading. No execution. No `live.yaml`. No Redis. No Phase 6b market-data.

## Why

Phase 5e delivers Telegram as a single Coordinator channel. Per-desk workers have no durable notify bus. Principal lock: **bus = Postgres LISTEN/NOTIFY (no Redis)**; one phase per PR.

## Outcome

- Queue: IMP-013 DONE (#44). This item the implementation thread. IMP-015 Phase 6b parked (at 6a merge).
- `DeskOutput` envelope header: desk, as_of UTC+Sydney, status, n, completeness, regime placeholder `unset` (filled in IMP-015), `op=paper|observation`, universe, sources/missing.
- Bus: Postgres `LISTEN/NOTIFY` only. No Redis.

## Status

DONE (#45). IMP-015 Phase 6b is the following implementation thread.
