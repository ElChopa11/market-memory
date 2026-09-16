# mm-ingest-worker

One-shot read-only ingest process (`ingest-once`). Same pipeline as `lab ingest`.

**Must not:** sign or submit orders.

```bash
uv run ingest-once --fixture tests/fixtures/hl_window.json --no-objects
uv run ingest-once --window 7d
```
