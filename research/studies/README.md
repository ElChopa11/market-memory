# Candidate studies

Deliverable path for Quant validation **after** intake gates land (rule 9).

**STATUS: INTAKE_ONLY** for C-001 / C-002 / C-003. Those cards stay `compute: false` / `results: []`. Do **not** write dated candidate-compute files under `C-001/`, `C-002/`, `C-003/`, or `signal-correlation/` until computation is unblocked.

Methodology / permission-filter studies that change the queue (analysis only, not strategy compute) may live under sibling folders such as `trend-permission-filter/`. They do not unpark C-00x.

When unblocked, write:

```text
research/studies/C-001/YYYY-MM-DD.md
research/studies/C-002/YYYY-MM-DD.md
research/studies/C-003/YYYY-MM-DD.md
research/studies/signal-correlation/YYYY-MM-DD.md
```

Each file must state: coded definition, params + commit ref of `config/candidates/<id>.yaml`, sample, window, split, cost model, benchmark, haircut, results per regime, verdict (`PASS` \| `FAIL` \| `INSUFFICIENT SAMPLE`), what would render the result spurious. Base rates belong in Market Memory, not only here.

A post-hoc param change is `C-00x.v2` with a reset sample. No silent tuning. No sizing. No scan-gate.
