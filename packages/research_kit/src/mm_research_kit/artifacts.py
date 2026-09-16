"""Copy templates, fill fields, and hash git artifacts. No secrets."""

from __future__ import annotations

from pathlib import Path

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import utcnow
from mm_research_kit.markdown import set_field, set_section_body

HASHED_RELATIVE_PATHS = (
    "intent.md",
    "thesis.md",
    "research-plan.md",
    "evidence/links.md",
    "skeptic-review.md",
)


def copy_template(templates_root: Path, name: str, destination: Path) -> str:
    source = templates_root / name
    if not source.is_file():
        raise FileNotFoundError(f"missing template: {source}")
    text = source.read_text(encoding="utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    return text


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def fill_intent(
    text: str,
    *,
    slug: str,
    goal: str,
    why_now: str,
    out_of_scope: str,
    definition_of_done: str,
    owner: str,
    opened_at: str,
    deadline: str,
    instrument: str,
    status: str,
) -> str:
    text = set_field(text, "Thesis id", slug)
    text = set_field(text, "Goal (one sentence)", goal)
    text = set_field(text, "Why now / trigger observation ids", why_now)
    text = set_field(text, "Out of scope", out_of_scope)
    text = set_field(text, "Definition of done for moving to thesis", definition_of_done)
    text = set_field(text, "Owner", owner)
    text = set_field(text, "opened_at", opened_at)
    text = set_field(text, "deadline", deadline)
    text = set_field(text, "Instrument universe (v1 default BTC + ETH perps)", instrument)
    text = set_field(text, "Status", status)
    return text


def fill_thesis(
    text: str,
    *,
    slug: str,
    status: str,
    author_role: str,
    instrument: str,
    horizon: str,
    hypothesis: str = "",
) -> str:
    text = set_field(text, "Thesis id", slug)
    text = set_field(text, "Status / version", status)
    text = set_field(text, "Author role", author_role)
    text = set_field(text, "Instrument", instrument)
    text = set_field(text, "Time horizon", horizon)
    if hypothesis.strip():
        text = set_section_body(text, "Hypothesis", hypothesis.strip())
    return text


def fill_research_plan(text: str, *, slug: str, owner: str, status: str) -> str:
    text = set_field(text, "Thesis id", slug)
    text = set_field(text, "Owner", owner)
    text = set_field(text, "Status", status)
    return text


def fill_skeptic_review(
    text: str,
    *,
    slug: str,
    reviewer: str | None = None,
    created_at: str | None = None,
    verdict: str | None = None,
) -> str:
    text = set_field(text, "Thesis id", slug)
    if reviewer is not None:
        text = set_field(text, "Reviewer id or role", reviewer)
    if created_at is not None:
        text = set_field(text, "Created at", created_at)
    if verdict is not None:
        text = set_field(text, "Verdict", verdict)
    return text


def artifact_content_hash(workspace: Path) -> str:
    payload: dict[str, str] = {}
    for rel in HASHED_RELATIVE_PATHS:
        path = workspace / rel
        payload[rel] = path.read_text(encoding="utf-8") if path.is_file() else ""
    return sha256_hex(canonical_json(payload))


def isoformat_now() -> str:
    return utcnow().isoformat()
