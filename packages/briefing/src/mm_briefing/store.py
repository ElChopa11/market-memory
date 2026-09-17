"""Write markdown briefs under briefs/YYYY/MM/DD/ and the DoD pre-market path."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from mm_briefing.models import BriefDocument, storage_quality


def artifact_relpath(doc: BriefDocument) -> Path:
    return (
        Path("briefs")
        / f"{doc.session_date.year:04d}"
        / f"{doc.session_date.month:02d}"
        / f"{doc.session_date.day:02d}"
        / f"{doc.kind}.md"
    )


def dod_relpath(doc: BriefDocument) -> Path | None:
    """Principal Phase 2 canonical pre-market path."""
    if doc.kind == "preopen":
        return Path("briefs") / doc.session_date.isoformat() / "us-pre-market.md"
    return None


def write_brief(doc: BriefDocument, *, root: Path) -> Path:
    rel = artifact_relpath(doc)
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc.markdown, encoding="utf-8")
    path.with_suffix(".sha256").write_text(doc.content_hash + "\n", encoding="utf-8")
    canonical = path
    dod = dod_relpath(doc)
    if dod is not None:
        dod_path = root / dod
        dod_path.parent.mkdir(parents=True, exist_ok=True)
        dod_path.write_text(doc.markdown, encoding="utf-8")
        dod_path.with_suffix(".sha256").write_text(doc.content_hash + "\n", encoding="utf-8")
        canonical = dod_path
    return canonical


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
        data_quality=storage_quality(doc.data_quality),
        payload_json={
            "kind": doc.kind,
            "content_hash": doc.content_hash,
            "legacy_path": artifact_relpath(doc).as_posix(),
            "dod_path": dod_relpath(doc).as_posix() if dod_relpath(doc) else None,
        },
    )
    return row.id
