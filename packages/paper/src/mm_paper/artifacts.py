"""Write paper-trade markdown + JSON under a thesis `paper/` folder."""

from __future__ import annotations

import json
from pathlib import Path

from mm_common.hashing import canonical_json
from mm_paper.models import PaperTradeRecord
from mm_research_kit.artifacts import copy_template, write_text
from mm_research_kit.markdown import set_field, set_section_body
from mm_research_kit.workspace import git_path


def paper_dir(workspace: Path) -> Path:
    path = workspace / "paper"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_paper_artifacts(
    workspace: Path,
    record: PaperTradeRecord,
    *,
    templates_root: Path,
    repo_root: Path,
) -> PaperTradeRecord:
    dest_md = paper_dir(workspace) / f"{record.id}.md"
    text = copy_template(templates_root, "paper-trade.md", dest_md)
    text = set_field(text, "Thesis id", record.thesis_slug)
    text = set_field(text, "Entry thesis snapshot hash", record.entry_thesis_snapshot_hash)
    text = set_field(text, "Opened at", record.opened_at.isoformat())
    text = set_field(text, "Closed at", record.closed_at.isoformat() if record.closed_at else "")
    text = set_field(text, "Instrument", record.instrument)
    text = set_field(text, "Size", record.size)
    text = set_field(text, "Max loss", record.max_loss)
    text = set_field(text, "Invalidation", record.invalidation)
    text = set_section_body(text, "Expected path checkpoints", _bullets(record.expected_path) or "(none)")
    text = set_section_body(text, "Fills", _json_block(record.fills) or "(none)")
    text = set_section_body(
        text,
        "Slippage",
        format(record.slippage_bps, "f") + " bps" if record.slippage_bps is not None else "(none)",
    )
    text = set_section_body(text, "Marks", _json_block(record.marks) or "(none)")
    text = set_section_body(text, "Exit reason", record.exit_reason or "(open)")
    notes = record.notes or ""
    if record.pnl is not None:
        notes = (notes + f"\n\nP&L: {format(record.pnl, 'f')}").strip()
    text = set_section_body(text, "Notes", notes or "(none)")
    write_text(dest_md, text)

    dest_json = paper_dir(workspace) / f"{record.id}.json"
    dest_json.write_text(canonical_json(record.canonical()) + "\n", encoding="utf-8")

    record.artifact_git_path = git_path(dest_md, repo_root)
    dest_json.write_text(canonical_json(record.canonical()) + "\n", encoding="utf-8")
    return record


def load_paper_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def list_paper_artifacts(workspace: Path) -> list[dict]:
    folder = workspace / "paper"
    if not folder.is_dir():
        return []
    rows = []
    for path in sorted(folder.glob("*.json")):
        rows.append(load_paper_json(path))
    return rows


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items if item.strip())


def _json_block(items: list) -> str:
    if not items:
        return ""
    return canonical_json([item.canonical() if hasattr(item, "canonical") else item for item in items])
