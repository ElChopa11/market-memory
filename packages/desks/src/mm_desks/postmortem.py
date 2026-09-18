"""Mandatory post-mortem before a closed idea's instrument publishes a new idea."""

from __future__ import annotations

from pathlib import Path

TEMPLATE_REL = Path("templates/post-mortem.md")


class PostMortemRequired(ValueError):
    """Blocking: closed idea has no post-mortem for this instrument."""


def template_exists(repo_root: Path) -> bool:
    return (Path(repo_root) / TEMPLATE_REL).is_file()


def post_mortem_path(research_root: Path, slug: str) -> Path:
    return Path(research_root) / slug / "post-mortem.md"


def is_filled(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if "<!-- tests, alerts, data, playbook" in text and text.count("\n") < 12:
        return False
    thesis_line = next((line for line in text.splitlines() if line.lower().startswith("- **thesis id:**")), "")
    value = thesis_line.split(":", 1)[-1].strip() if thesis_line else ""
    return bool(value)


def assert_can_publish_new_idea(
    *,
    instrument: str,
    closed_slugs: tuple[str, ...],
    research_root: Path,
    repo_root: Path,
) -> None:
    if not template_exists(repo_root):
        raise PostMortemRequired("templates/post-mortem.md missing")
    inst = instrument.upper()
    for slug in closed_slugs:
        # Convention: closed ideas for an instrument include the ticker in the slug or path marker.
        if inst not in slug.upper() and not slug:
            continue
        path = post_mortem_path(research_root, slug)
        if inst in slug.upper() and not is_filled(path):
            raise PostMortemRequired(
                f"closed idea {slug} for {inst} requires templates/post-mortem.md filled before a new idea"
            )
