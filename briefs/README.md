# briefs/

Generated Market Pulse artifacts:

| Kind | Path |
|---|---|
| US pre-market (DoD) | `YYYY-MM-DD/us-pre-market.md` |
| Legacy pre-open / close / alert | `YYYY/MM/DD/{preopen,close,alert}.md` |

`lab brief preopen` writes **both** pre-market paths with identical bytes.

Dated output is gitignored except an explicit committed sample on the DoD path. Regenerate with:

```bash
uv run lab brief preopen --fixture tests/fixtures/briefing/frozen_day.json --no-db
uv run lab brief preopen --live --no-db
```

See [docs/runbooks/market-pulse.md](../docs/runbooks/market-pulse.md) and [ops/plans/IMP-002-us-market-pulse.md](../ops/plans/IMP-002-us-market-pulse.md).
