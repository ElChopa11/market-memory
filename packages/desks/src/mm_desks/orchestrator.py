"""Run one desk or the Intel → 3a|3b → Quant → Skeptic → Risk → Coord pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import as_utc
from mm_desks.coord import CoordDesk
from mm_desks.crypto import CryptoDesk
from mm_desks.equities import EquitiesDesk
from mm_desks.fixture import load_frozen_day
from mm_desks.intel import IntelDesk
from mm_desks.models import FrozenDay
from mm_desks.protocol import ENGINE_VERSION, DeskContext, DeskOutput
from mm_desks.quant import QuantDesk
from mm_desks.risk import RiskDesk
from mm_desks.skeptic import SkepticDesk
from mm_delivery.payload import SEND_ENABLED, prepare_payload
from mm_delivery.deliver import deliver
from mm_research_kit.state_machine import TransitionLog

PIPELINE: tuple[str, ...] = ("intel", "crypto", "equities", "quant", "skeptic", "risk", "coord")

_DESKS = {
    "intel": IntelDesk(),
    "crypto": CryptoDesk(),
    "equities": EquitiesDesk(),
    "quant": QuantDesk(),
    "skeptic": SkepticDesk(),
    "risk": RiskDesk(),
    "coord": CoordDesk(),
}


@dataclass(frozen=True)
class DeskRunResult:
    as_of_knowledge: datetime
    fixture_id: str
    session_date: str
    desks: tuple[DeskOutput, ...]
    events: tuple[TransitionLog, ...]
    content_hash: str
    pack_markdown: str
    send: bool = False
    engine_version: str = ENGINE_VERSION

    def canonical(self) -> dict[str, Any]:
        return {
            "engine_version": self.engine_version,
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "fixture_id": self.fixture_id,
            "session_date": self.session_date,
            "desks": [row.canonical() for row in self.desks],
            "events": [
                {
                    "actor": event.actor,
                    "ts": event.ts.isoformat(),
                    "reason": event.reason,
                    "from_status": event.from_status,
                    "to_status": event.to_status,
                    "thesis_slug": event.thesis_slug,
                    "risk_decision": event.risk_decision,
                    "principal_override": event.principal_override,
                }
                for event in self.events
            ],
            "pack_markdown": self.pack_markdown,
            "send": False,
            "send_enabled": SEND_ENABLED,
        }

    def as_public_dict(self) -> dict[str, Any]:
        payload = {
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "fixture_id": self.fixture_id,
            "session_date": self.session_date,
            "engine_version": self.engine_version,
            "content_hash": self.content_hash,
            "send": False,
            "no_send": True,
            "desks": [
                {
                    "slug": row.slug,
                    "desk": row.desk,
                    "tier": row.tier,
                    "status": row.status,
                    "completeness_pct": row.completeness_pct,
                    "provenance_ids": list(row.provenance_ids),
                    "notes": list(row.notes),
                }
                for row in self.desks
            ],
            "events": [
                {
                    "actor": event.actor,
                    "ts": event.ts.isoformat(),
                    "reason": event.reason,
                    "from_status": event.from_status,
                    "to_status": event.to_status,
                }
                for event in self.events
            ],
        }
        return payload


def _hash_pack(markdown: str, desks: tuple[DeskOutput, ...], events: tuple[TransitionLog, ...]) -> str:
    payload = {
        "pack_markdown": markdown,
        "desks": [row.canonical() for row in desks],
        "events": [
            {
                "actor": event.actor,
                "ts": event.ts.isoformat(),
                "reason": event.reason,
                "from_status": event.from_status,
                "to_status": event.to_status,
                "risk_decision": event.risk_decision,
            }
            for event in events
        ],
        "send": False,
    }
    return sha256_hex(canonical_json(payload))


def run_desks(
    *,
    as_of: datetime,
    ctx: DeskContext,
    slugs: tuple[str, ...] | list[str],
) -> DeskRunResult:
    watermark = as_utc(as_of)
    for slug in slugs:
        if slug not in _DESKS:
            raise ValueError(f"unknown desk slug {slug!r}; choose from {list(PIPELINE)}")
        output = _DESKS[slug].run(watermark, ctx)
        ctx.prior[slug] = output
    ordered = tuple(ctx.prior[slug] for slug in slugs if slug in ctx.prior)
    coord = ctx.prior.get("coord")
    pack_md = ""
    if coord is not None:
        pack_md = str(coord.payload.get("pack_markdown") or "")
        if coord.artifacts:
            pack_md = coord.artifacts[0].content
    events = tuple(ctx.events)
    digest = _hash_pack(pack_md, ordered, events)
    return DeskRunResult(
        as_of_knowledge=watermark,
        fixture_id=ctx.fixture.fixture_id,
        session_date=ctx.fixture.session_date,
        desks=ordered,
        events=events,
        content_hash=digest,
        pack_markdown=pack_md,
        send=False,
    )


def run_from_fixture(
    path: Path,
    *,
    repo_root: Path,
    slugs: tuple[str, ...] | None = None,
    workspace: Path | None = None,
    send: bool = False,
) -> DeskRunResult:
    if send:
        raise RuntimeError("desk runners never send; use mm_delivery.deliver after the pack")
    from mm_delivery.payload import assert_no_send

    assert_no_send(send_requested=False)
    day: FrozenDay = load_frozen_day(path, repo_root=repo_root)
    ctx = DeskContext(
        repo_root=repo_root,
        fixture=day,
        send_enabled=False,
        workspace=workspace,
        thesis=day.thesis,
    )
    chosen = PIPELINE if slugs is None else tuple(slugs)
    return run_desks(as_of=day.as_of_knowledge, ctx=ctx, slugs=chosen)


def write_dry_run(result: DeskRunResult, *, out_root: Path, repo_root: Path | None = None) -> dict[str, str]:
    """Write pack + no-send + telegram payload under briefs/YYYY-MM-DD/. No network."""
    day_dir = out_root / "briefs" / result.session_date
    day_dir.mkdir(parents=True, exist_ok=True)
    pack_path = day_dir / "desk-pack.md"
    hash_path = day_dir / "desk-run.sha256"
    payload_path = day_dir / "no-send.json"
    pack_path.write_text(result.pack_markdown or "", encoding="utf-8")
    hash_path.write_text(result.content_hash + "\n", encoding="utf-8")
    payload = prepare_payload(result.pack_markdown or "")
    payload_path.write_text(
        canonical_json(payload.canonical()) + "\n",
        encoding="utf-8",
    )
    for desk in result.desks:
        for artifact in desk.artifacts:
            if artifact.kind != "markdown" or not artifact.relpath:
                continue
            target = day_dir / f"{desk.slug}-{Path(artifact.relpath).name}"
            target.write_text(artifact.content, encoding="utf-8")
    paths = {
        "pack": str(pack_path),
        "sha256": str(hash_path),
        "no_send": str(payload_path),
    }
    completeness = 100.0
    for row in result.desks:
        if row.slug == "coord":
            completeness = float(row.completeness_pct)
            break
    delivery = deliver(
        result.pack_markdown or "",
        desk="coord",
        as_of=result.as_of_knowledge,
        send=False,
        kind="desk_pack",
        completeness_pct=completeness,
        repo=repo_root,
        out_root=out_root,
        session_date=result.session_date,
        respect_quiet_hours=False,
    )
    if delivery.written:
        paths.update(delivery.written)
    paths["telegram_payload_hash"] = delivery.payload_hash
    return paths
