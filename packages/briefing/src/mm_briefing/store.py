"""Write markdown briefs under briefs/YYYY/MM/DD/ and optionally index in Market Memory."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from mm_briefing.models import BriefDocument


def artifact_relpath(doc: BriefDocument) -> Path:
    return Path("briefs") / f"{doc.session_date.year:04d}" / f"{doc.session_date.month:02d}" / f"{doc.session_date.day:02d}" / f"{doc.kind}.md"


def write_brief(doc: BriefDocument, *, root: Path) -> Path:
    rel = artifact_relpath(doc)
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc.markdown, encoding="utf-8")
    hash_path = path.with_suffix(".sha256")
    hash_path.write_text(doc.content_hash + "\n", encoding="utf-8")
    return path


def index_brief(session: Session, doc: BriefDocument, *, artifact_path: Path, root: Path) -> str:
    from mm_memory.brief_repository import BriefRepository

    rel = artifact_path.resolve().relative_to(root.resolve()).as_posix()
    row = BriefRepository(session).put(
        kind=doc.kind,
        session_date=doc.session_date,
        generated_at=doc.generated_at,
        as_of_knowledge=doc.as_of_knowledge,
        artifact_git_path=rel,
        content_hash=doc.content_hash,
        data_quality=doc.data_quality,
        payload_json={"kind": doc.kind, "content_hash": doc.content_hash},
    )
    return row.id
