"""Link observation ids to a thesis workspace (git artifact)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from mm_common.enums import EVIDENCE_ROLE_VALUES, EvidenceRole
from mm_common.time import utcnow
from mm_research_kit.artifacts import write_text
from mm_research_kit.errors import GateError
from mm_research_kit.markdown import append_bullet_under_heading

LINKS_REL = Path("evidence") / "links.md"
_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*)\s*\|\s*([^|]*)\s*\|\s*$")
_SEP = re.compile(r"^\|[\s:\-|]+\|\s*$")

LINKS_HEADER = """# Evidence links

Observation ids from Market Memory linked to this thesis. Roles: `supports` | `opposes` | `context`.

Git is the human-review source; Market Memory stores the same links plus artifact content hashes.

| observation_id | role | notes | linked_at |
| --- | --- | --- | --- |
"""


@dataclass(frozen=True)
class EvidenceLink:
    observation_id: str
    role: str
    notes: str = ""
    linked_at: str = ""


def links_path(workspace: Path) -> Path:
    return workspace / LINKS_REL


def parse_evidence_links(text: str) -> list[EvidenceLink]:
    links: list[EvidenceLink] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or _SEP.match(stripped):
            continue
        match = _ROW.match(stripped)
        if not match:
            continue
        observation_id, role, notes, linked_at = (part.strip() for part in match.groups())
        if observation_id.lower() in {"observation_id", "---"}:
            continue
        if not observation_id or set(observation_id) <= {"-"}:
            continue
        links.append(
            EvidenceLink(
                observation_id=observation_id,
                role=role.lower(),
                notes=notes,
                linked_at=linked_at,
            )
        )
    return links


def load_evidence_links(workspace: Path) -> list[EvidenceLink]:
    path = links_path(workspace)
    if not path.is_file():
        return []
    return parse_evidence_links(path.read_text(encoding="utf-8"))


def has_evidence_links(workspace: Path) -> bool:
    return bool(load_evidence_links(workspace))


def render_links(links: list[EvidenceLink]) -> str:
    lines = [LINKS_HEADER.rstrip(), ""]
    for link in links:
        notes = (link.notes or "").replace("|", "/")
        linked_at = link.linked_at or ""
        lines.append(f"| {link.observation_id} | {link.role} | {notes} | {linked_at} |")
    return "\n".join(lines).rstrip() + "\n"


def normalize_role(role: str) -> str:
    value = role.strip().lower()
    if value not in EVIDENCE_ROLE_VALUES:
        allowed = ", ".join(EVIDENCE_ROLE_VALUES)
        raise GateError(f"unknown evidence role {role!r}; use {allowed}")
    return EvidenceRole(value).value


def link_evidence(
    workspace: Path,
    *,
    observation_id: str,
    role: str = EvidenceRole.SUPPORTS.value,
    notes: str = "",
) -> EvidenceLink:
    observation_id = observation_id.strip()
    if not observation_id:
        raise GateError("observation id is required")
    role_value = normalize_role(role)
    existing = load_evidence_links(workspace)
    linked_at = utcnow().isoformat()
    updated = EvidenceLink(
        observation_id=observation_id,
        role=role_value,
        notes=notes.strip(),
        linked_at=linked_at,
    )
    replaced = False
    next_links: list[EvidenceLink] = []
    for row in existing:
        if row.observation_id == observation_id and row.role == role_value:
            next_links.append(updated)
            replaced = True
        else:
            next_links.append(row)
    if not replaced:
        next_links.append(updated)
    path = links_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text(path, render_links(next_links))
    thesis = workspace / "thesis.md"
    if thesis.is_file():
        bullet = f"- `{observation_id}` ({role_value})"
        if notes.strip():
            bullet += f" — {notes.strip()}"
        write_text(thesis, append_bullet_under_heading(thesis.read_text(encoding="utf-8"), "Evidence", bullet))
    return updated
