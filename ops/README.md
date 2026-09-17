# Ops cell

Proposals and draft playbooks for Principal / Coordinator review.

**This tree is not live logic.** Nothing here enables trading, edits risk environments, or hot-patches alerts. Promote a proposal through the normal git-reviewed strategy lifecycle (`docs/research-lifecycle.md`) before it becomes a template, test, or config change.

| Path | What it is |
|---|---|
| `ops/proposals/` | Dated outcome scans and change proposals |
| `ops/drafts/` | Non-live playbook / alert / test sketches |

Hard constraints (same as `AGENTS.md`):

- Do not edit `config/risk/environments/live.yaml` from this tree.
- Do not add credentials, signing, or `mm_execution` usage.
- Do not merge proposals into live briefing/risk config without Principal review.
