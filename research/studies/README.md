# Candidate studies

Deliverable path for Quant validation **after** intake gates land (rule 9).

**STATUS: INTAKE_ONLY.** No dated study files. NOTHING computed. Phase 1 unconditional base rates are not in Memory yet. 6e instance auto-track is not wired.

When unblocked, write:

```text
research/studies/C-001/YYYY-MM-DD.md
research/studies/C-002/YYYY-MM-DD.md
research/studies/C-003/YYYY-MM-DD.md
research/studies/signal-correlation/YYYY-MM-DD.md
```

Each file must state: coded definition, params + commit ref of `config/candidates/<id>.yaml`, sample, window, split, cost model, benchmark, haircut, results per regime, verdict (`PASS` \| `FAIL` \| `INSUFFICIENT SAMPLE`), what would make the result spurious. Base rates belong in Market Memory, not only here.

A post-hoc param change is `C-00x.v2` with a reset sample. No silent tuning. No sizing. No scan-gate.
