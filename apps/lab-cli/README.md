# mm-lab-cli

Coordinator surface (`lab` CLI). Phase 1 commands: `status`, `migrate`, `ingest`, `what-did-we-know`.

**Must not:** hold trading credentials.

```bash
uv run lab status
uv run lab migrate
uv run lab ingest --fixture tests/fixtures/hl_window.json --no-objects
uv run lab what-did-we-know --at 2026-09-10T00:00:00Z
```
