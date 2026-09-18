# PLAN — IMP-031 Phase 6f strategy decay-watch

**Report status:** PARKED.  
**Owner:** Quant  
**Scope:** Phase 6f — prompt-hash strategy decay-watch. Not this PR.

## Why

6e records prompt SHA-256 inputs (`config/scorecards/decay.yaml`, `mm_quant.decay_stub`) with `watch_enabled: false`. Operators still lack a standing watch that alerts when a versioned prompt or strategy hash drifts.

## Outcome

*(filled in the 6f PR)*

## Non-goals

Implementing decay-watch in IMP-030 / 6e. Live trading. Signing. `live.yaml`. Redis. Auto-waive gates.

## Status

PARKED. Do not implement the full prompt-hash decay watch in the 6e PR.
