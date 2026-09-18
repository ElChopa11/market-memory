"""Thesis / skeptic coordinator commands. Must not hold trading credentials."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from mm_common.time import utcnow
from mm_memory.db import dsn_from_env, session_scope
from mm_memory.thesis_repository import ThesisRepository, UnknownObservationError
from mm_research_kit.artifacts import artifact_content_hash
from mm_research_kit.errors import GateError, ResearchKitError
from mm_research_kit.evidence import link_evidence, load_evidence_links, normalize_role
from mm_research_kit.lifecycle import advance_status, discover_workspaces, read_author_role, read_status
from mm_research_kit.markdown import get_field
from mm_research_kit.skeptic import open_skeptic_review, record_skeptic_verdict
from mm_research_kit.workspace import (
    ThesisSpec,
    create_thesis_from_intent,
    find_workspace,
    git_path,
)


def _print(payload: dict) -> None:
    print(json.dumps(payload, indent=2, default=str))


def _maybe_session(args: Namespace):
    if getattr(args, "no_db", False):
        return None
    return session_scope(getattr(args, "dsn", None) or dsn_from_env())


def _upsert_workspace(session, workspace: Path, repo_root: Path, *, status: str | None = None) -> str:
    thesis_text = (workspace / "thesis.md").read_text(encoding="utf-8") if (workspace / "thesis.md").is_file() else ""
    repo = ThesisRepository(session)
    record = repo.upsert(
        slug=workspace.name,
        status=status or read_status(workspace) or "draft",
        author_role=read_author_role(workspace),
        artifact_git_path=git_path(workspace, repo_root),
        artifact_content_hash=artifact_content_hash(workspace),
        instrument=get_field(thesis_text, "Instrument") or None,
        horizon=get_field(thesis_text, "Time horizon") or None,
    )
    return record.thesis.id


def cmd_thesis_new(args: Namespace) -> int:
    research_root: Path = args.research_root
    templates_root: Path = args.templates_root
    repo_root: Path = args.repo_root
    spec: ThesisSpec | None = None
    intent_path = Path(args.from_intent) if args.from_intent else None
    if intent_path is None:
        if not args.goal:
            raise GateError("cannot create/mark thesis without intent")
        spec = ThesisSpec(
            goal=args.goal,
            owner=args.owner,
            why_now=args.why_now,
            out_of_scope=args.out_of_scope,
            instrument=args.instrument,
            horizon=args.horizon or "",
            deadline=args.deadline or "",
            hypothesis=args.hypothesis or "",
            author_role=args.owner,
        )
    created = create_thesis_from_intent(
        research_root=research_root,
        templates_root=templates_root,
        spec=spec,
        intent_path=intent_path,
        repo_root=repo_root,
    )
    db_id = None
    ctx = _maybe_session(args)
    if ctx is not None:
        with ctx as session:
            db_id = _upsert_workspace(session, created.path, repo_root, status=created.status)
    _print(
        {
            "slug": created.slug,
            "path": str(created.path),
            "status": created.status,
            "artifact_git_path": created.artifact_git_path,
            "artifact_content_hash": created.artifact_content_hash,
            "thesis_id": db_id,
        }
    )
    return 0


def cmd_thesis_link_evidence(args: Namespace) -> int:
    workspace = find_workspace(args.research_root, args.slug)
    role = normalize_role(args.role)
    ctx = _maybe_session(args)
    if ctx is not None:
        with ctx as session:
            repo = ThesisRepository(session)
            row = repo.get_by_slug(workspace.name)
            if row is None:
                thesis_id = _upsert_workspace(session, workspace, args.repo_root)
                row = repo.get(thesis_id)
            assert row is not None
            repo.link_evidence(
                thesis_id=row.id,
                observation_id=args.observation,
                role=role,
                notes=args.notes or None,
            )
            link = link_evidence(
                workspace,
                observation_id=args.observation,
                role=role,
                notes=args.notes or "",
            )
            _upsert_workspace(session, workspace, args.repo_root, status=read_status(workspace))
            evidence_count = repo.evidence_count(row.id)
    else:
        link = link_evidence(
            workspace,
            observation_id=args.observation,
            role=role,
            notes=args.notes or "",
        )
        evidence_count = len(load_evidence_links(workspace))
    _print(
        {
            "slug": workspace.name,
            "observation_id": link.observation_id,
            "role": link.role,
            "notes": link.notes,
            "evidence_count": evidence_count,
            "status": read_status(workspace),
        }
    )
    return 0


def cmd_thesis_advance(args: Namespace) -> int:
    workspace = find_workspace(args.research_root, args.slug)
    actor = "Coordinator"
    reason = "lab thesis advance"
    ctx = _maybe_session(args)
    if ctx is not None:
        with ctx as session:
            thesis_id = _upsert_workspace(session, workspace, args.repo_root)
            repo = ThesisRepository(session)

            def hook(log) -> None:
                repo.log_status_event(
                    thesis_id=thesis_id,
                    from_status=log.from_status,
                    to_status=log.to_status,
                    actor=log.actor,
                    ts=log.ts,
                    reason=log.reason,
                    risk_decision=log.risk_decision,
                    principal_override=log.principal_override,
                )

            status = advance_status(workspace, args.to, actor=actor, reason=reason, hook=hook)
            _upsert_workspace(session, workspace, args.repo_root, status=status)
    else:
        status = advance_status(workspace, args.to, actor=actor, reason=reason)
    _print({"slug": workspace.name, "status": status, "path": str(workspace)})
    return 0


def cmd_thesis_list(args: Namespace) -> int:
    ctx = _maybe_session(args)
    if ctx is not None:
        with ctx as session:
            repo = ThesisRepository(session)
            rows = repo.list_theses(status=args.status)
            payload = [
                {
                    "id": row.id,
                    "slug": row.slug,
                    "status": row.status,
                    "artifact_git_path": row.artifact_git_path,
                    "instrument": row.instrument,
                    "artifact_content_hash": row.artifact_content_hash,
                    "evidence_count": repo.evidence_count(row.id),
                    "updated_at": row.updated_at.isoformat(),
                }
                for row in rows
            ]
    else:
        payload = []
        for workspace in discover_workspaces(args.research_root):
            status = read_status(workspace)
            if args.status and status != args.status:
                continue
            payload.append(
                {
                    "slug": workspace.name,
                    "status": status,
                    "path": str(workspace),
                    "evidence_count": len(load_evidence_links(workspace)),
                }
            )
    _print({"count": len(payload), "theses": payload})
    return 0


def cmd_thesis_show(args: Namespace) -> int:
    workspace = find_workspace(args.research_root, args.slug)
    links = load_evidence_links(workspace)
    ctx = _maybe_session(args)
    db = None
    if ctx is not None:
        with ctx as session:
            row = ThesisRepository(session).get_by_slug(workspace.name)
            if row is not None:
                db = {
                    "id": row.id,
                    "status": row.status,
                    "artifact_content_hash": row.artifact_content_hash,
                    "artifact_git_path": row.artifact_git_path,
                }
    _print(
        {
            "slug": workspace.name,
            "path": str(workspace),
            "status": read_status(workspace),
            "evidence": [link.__dict__ for link in links],
            "db": db,
        }
    )
    return 0


def cmd_skeptic_open(args: Namespace) -> int:
    workspace = find_workspace(args.research_root, args.slug)
    status = open_skeptic_review(workspace, reviewer=args.reviewer)
    ctx = _maybe_session(args)
    if ctx is not None:
        with ctx as session:
            _upsert_workspace(session, workspace, args.repo_root, status=status)
    _print({"slug": workspace.name, "status": status, "reviewer": args.reviewer})
    return 0


def cmd_skeptic_record(args: Namespace) -> int:
    workspace = find_workspace(args.research_root, args.slug)
    status = record_skeptic_verdict(
        workspace,
        verdict=args.verdict,
        reviewer=args.reviewer,
        findings=args.findings or "",
    )
    ctx = _maybe_session(args)
    if ctx is not None:
        with ctx as session:
            thesis_id = _upsert_workspace(session, workspace, args.repo_root, status=status)
            ThesisRepository(session).record_skeptic(
                thesis_id=thesis_id,
                reviewer_id_or_role=args.reviewer,
                verdict=args.verdict,
                findings_json={"notes": args.findings or "", "recorded_at": utcnow().isoformat()},
                artifact_git_path=git_path(workspace / "skeptic-review.md", args.repo_root)
                if (workspace / "skeptic-review.md").is_file()
                else git_path(workspace, args.repo_root),
                content_hash=artifact_content_hash(workspace),
            )
    _print(
        {
            "slug": workspace.name,
            "status": status,
            "verdict": args.verdict,
            "reviewer": args.reviewer,
        }
    )
    return 0


def dispatch_thesis(args: Namespace) -> int:
    cmd = getattr(args, "thesis_cmd", None)
    handlers = {
        "new": cmd_thesis_new,
        "link-evidence": cmd_thesis_link_evidence,
        "advance": cmd_thesis_advance,
        "list": cmd_thesis_list,
        "show": cmd_thesis_show,
    }
    if cmd is None or cmd not in handlers:
        print("usage: lab thesis {new,link-evidence,advance,list,show}", flush=True)
        return 2
    return handlers[cmd](args)


def dispatch_skeptic(args: Namespace) -> int:
    cmd = getattr(args, "skeptic_cmd", None)
    handlers = {
        "open": cmd_skeptic_open,
        "record": cmd_skeptic_record,
    }
    if cmd is None or cmd not in handlers:
        print("usage: lab skeptic {open,record}", flush=True)
        return 2
    return handlers[cmd](args)


def run_research_command(handler, args: Namespace) -> int:
    try:
        return handler(args)
    except GateError as exc:
        print(f"gate failed: {exc}", flush=True)
        return 2
    except UnknownObservationError as exc:
        print(f"gate failed: {exc}", flush=True)
        return 2
    except (ResearchKitError, FileNotFoundError, KeyError) as exc:
        print(f"error: {exc}", flush=True)
        return 2
