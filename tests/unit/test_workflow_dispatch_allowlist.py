"""Only the Sydney-morning workflow may declare workflow_dispatch.

The Sydney-morning PAT can reach any workflow in this repo that declares
that trigger. Phase 0 promote-gate has no manual promotion path, and the
one-shot migrate workflow was deleted. A future pull request that adds
workflow_dispatch on any other file fails this test.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
ALLOWED = frozenset({"hybrid-sydney-morning.yml"})


def _declares_workflow_dispatch(path: Path) -> bool:
    """True when the workflow `on:` block includes the workflow_dispatch trigger.

    Comments that mention the trigger do not count. PyYAML loads the GitHub
    `on:` key as boolean True.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return False
    block = data[True] if True in data else data.get("on")
    if isinstance(block, str):
        return block == "workflow_dispatch"
    if isinstance(block, list):
        return "workflow_dispatch" in block
    if isinstance(block, dict):
        return "workflow_dispatch" in block
    return False


def test_only_hybrid_sydney_morning_declares_workflow_dispatch() -> None:
    paths = sorted(WORKFLOWS.glob("*.yml"))
    assert paths, f"expected workflows under {WORKFLOWS}"
    declared = sorted(path.name for path in paths if _declares_workflow_dispatch(path))
    assert declared == sorted(ALLOWED), (
        "workflow_dispatch allowlist is hybrid-sydney-morning.yml only; "
        f"found {declared}"
    )
