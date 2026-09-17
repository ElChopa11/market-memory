# Post-IPO / reclaim screen

Standing Equities & Post-IPO Desk product. Read-only **research triage**. **Not a trading decision.**

Plan: [ops/plans/IMP-006-post-ipo-reclaim-screen.md](../../ops/plans/IMP-006-post-ipo-reclaim-screen.md).

## Command

```bash
uv run lab equities reclaim-screen \
  --fixture tests/fixtures/equities/post_ipo_reclaim_snapshot.yaml \
  --no-db
```

Writes `research/screens/post-ipo-reclaim/YYYY-MM-DD.md` plus a `.meta.json` sidecar. Prints JSON (`path`, `params_hash`, per-name verdict + data quality).

| Flag | Effect |
|---|---|
| `--fixture` | JSON/YAML snapshot (prints + optional overlays / reclaim observables). Omit for an empty snapshot (all `unavailable` / `INSUFFICIENT_DATA`) |
| `--universe` | Screen-only YAML (default `config/equities/post_ipo_reclaim.yaml`) |
| `--quant-pack` | Optional QUANT pack directory for overlays on names that exist in the pack. Missing names stay unavailable |
| `--as-of` | Review clock UTC instant |
| `--screen-date` | Artifact date `YYYY-MM-DD` |
| `--research-root` | Where `screens/` is written (default `research`) |
| `--repo-root` | Where `config/` lives |
| `--stale-after-hours` | Override universe default (36) |
| `--no-db` | Git artifacts only |

## Universe

`config/equities/post_ipo_reclaim.yaml` is **screen-only** (`kind=post_ipo_reclaim_screen`, `status=screen_only`). It does **not** change Principal membership in `config/universe.yaml` (`in_universe` / `watch_only`).

Seed candidates: `CRCL`, `HOOD` (already on the Quant Review TV watchlist). Context names `QQQ`, `SPX`, `GLXY` are relative-value denominators, not reclaim candidates.

## Row contract

Each candidate: instrument, as-of, reclaim/relative metrics with source + freshness, data quality `fresh|stale|partial|unavailable`, Quant verdict + reason code from

`RESEARCH_PRIORITY | MONITOR | DEFER | REJECT | INSUFFICIENT_DATA`

Hard screen rule: a beaten-down IPO is not a candidate just because it is down. Needs catalyst, benchmark-relative context, liquidity evidence, and a falsifiable invalidation. Reclaim ≠ one-day bounce.

Missing prints, MDD, listing dates, catalysts → **unavailable** (never invented).

Footer: informational / not a trading decision. Principal gate still required for anything beyond research.

## Limitations

- No equity-feed ingest; no filings/earnings/lock-up tape in Market Memory.
- Committed sample is a fixture subset of the IMP-001 screenshot prints, not a live tape.
- QUANT pack does not overlay CRCL/HOOD, so drawdown vs reference high is unavailable on that sample.

See also: [Quant Review Board](research-workspace.md), [desk charters](../../ops/desk-charters.md).
