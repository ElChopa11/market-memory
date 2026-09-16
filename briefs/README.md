# briefs/

Generated Market Pulse artifacts land here as `YYYY/MM/DD/{preopen,close,alert}.md`.

Do not commit dated output. Regenerate with:

```bash
uv run lab brief preopen --fixture tests/fixtures/briefing/frozen_day.json --no-db
```

See [docs/runbooks/market-pulse.md](../docs/runbooks/market-pulse.md).
