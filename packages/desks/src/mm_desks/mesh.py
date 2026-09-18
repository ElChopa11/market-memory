"""Coordinator mesh worker stub (Phase 6a).

Subscribe to desk.*.output / coord.assemble / dq.event, track desk health,
assemble the daily pack from persisted envelopes. Missing or killed desks
become FAILED + error_class. Telegram remains a sink (5e), not the bus.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import as_utc
from mm_desks.bus import Bus, DeskHealth, EnvelopeStore, InMemoryBus, InMemoryEnvelopeStore, NotifyEvent
from mm_desks.cadence import DESK_META, all_channels
from mm_desks.coord import CoordDesk, PIPELINE_FOR_PACK
from mm_desks.envelope import (
    ERROR_CLASS_KILLED,
    ERROR_CLASS_MISSING,
    DeskEnvelope,
    envelope_from_output,
    failed_desk_output,
    output_from_canonical,
    stamp_output,
)
from mm_desks.fixture import load_frozen_day
from mm_desks.orchestrator import PIPELINE, run_from_fixture
from mm_desks.protocol import FAILED, OK, DeskContext, DeskOutput, ENGINE_VERSION

MESH_DESKS: tuple[str, ...] = PIPELINE_FOR_PACK


@dataclass(frozen=True)
class PublishResult:
    envelope: DeskEnvelope
    inserted: bool
    channels: tuple[str, ...]


@dataclass(frozen=True)
class AssembleResult:
    as_of_knowledge: datetime
    envelopes: tuple[DeskEnvelope, ...]
    coord: DeskEnvelope
    health: dict[str, DeskHealth]
    pack_markdown: str
    content_hash: str
    status: str
    completeness_pct: float

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "engine_version": ENGINE_VERSION,
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "content_hash": self.content_hash,
            "status": self.status,
            "completeness_pct": self.completeness_pct,
            "pack_present": bool(self.pack_markdown),
            "coord_envelope_id": self.coord.envelope_id,
            "coord_content_hash": self.coord.content_hash,
            "desks": {
                env.desk: {
                    "status": env.status,
                    "error_class": env.error_class,
                    "content_hash": env.content_hash,
                    "n": env.n,
                    "completeness": env.completeness,
                    "channel": env.channel,
                }
                for env in self.envelopes
            },
            "health": {slug: row.as_public_dict() for slug, row in self.health.items()},
        }


class CoordMeshWorker:
    """Stub Coord worker: persist envelopes, NOTIFY lightweight keys, assemble packs."""

    def __init__(
        self,
        store: EnvelopeStore,
        bus: Bus,
        *,
        repo_root: Path | None = None,
    ) -> None:
        self.store = store
        self.bus = bus
        self.repo_root = Path(repo_root) if repo_root is not None else Path(".")
        self.health: dict[str, DeskHealth] = {
            slug: DeskHealth(desk=slug, status="unknown") for slug in DESK_META
        }

    def subscribe_channels(self) -> tuple[str, ...]:
        return all_channels(self.repo_root)

    def _touch_health(self, envelope: DeskEnvelope) -> None:
        self.health[envelope.desk] = DeskHealth(
            desk=envelope.desk,
            status=envelope.status,
            last_as_of=envelope.as_of_utc,
            last_envelope_id=envelope.envelope_id,
            last_content_hash=envelope.content_hash,
            error_class=envelope.error_class,
            n=envelope.n,
            completeness=envelope.completeness,
        )

    def publish(self, envelope: DeskEnvelope, *, alert: bool = False) -> PublishResult:
        inserted = self.store.put(envelope)
        channels: list[str] = []
        if inserted:
            self.bus.notify(envelope.channel, envelope.notify_payload())
            channels.append(envelope.channel)
            if alert and envelope.alert_channel:
                self.bus.notify(envelope.alert_channel, envelope.notify_payload())
                channels.append(envelope.alert_channel)
            if envelope.status != OK and envelope.dq_channel:
                self.bus.notify(envelope.dq_channel, envelope.notify_payload())
                channels.append(envelope.dq_channel)
        self._touch_health(envelope)
        return PublishResult(envelope=envelope, inserted=inserted, channels=tuple(channels))

    def on_event(self, event: NotifyEvent) -> DeskEnvelope | None:
        envelope_id = str((event.payload or {}).get("id") or "")
        if not envelope_id:
            return None
        env = self.store.get(envelope_id)
        if env is not None:
            self._touch_health(env)
        return env

    def drain(
        self,
        channels: Sequence[str] | None = None,
        *,
        timeout: float | None = 0.5,
        stop_after: int | None = None,
    ) -> list[NotifyEvent]:
        wanted = tuple(channels or self.subscribe_channels())
        seen: list[NotifyEvent] = []
        for event in self.bus.listen(wanted, timeout=timeout, stop_after=stop_after):
            self.on_event(event)
            seen.append(event)
        return seen

    def assemble(
        self,
        as_of: datetime,
        ctx: DeskContext,
        *,
        required: Sequence[str] = MESH_DESKS,
        killed: Sequence[str] = (),
    ) -> AssembleResult:
        watermark = as_utc(as_of)
        killed_set = set(killed)
        envelopes: list[DeskEnvelope] = []
        for slug in required:
            env = None if slug in killed_set else self.store.latest(slug, watermark)
            if env is None:
                error = ERROR_CLASS_KILLED if slug in killed_set else ERROR_CLASS_MISSING
                output = failed_desk_output(slug, watermark, error_class=error, repo_root=self.repo_root)
                output = stamp_output(output, ctx)
                env = envelope_from_output(output, repo_root=self.repo_root)
                self.publish(env, alert=True)
            else:
                self._touch_health(env)
            envelopes.append(env)
            if env.body:
                ctx.prior[slug] = output_from_canonical(env.body)
            else:
                ctx.prior[slug] = failed_desk_output(
                    slug,
                    watermark,
                    error_class=env.error_class or ERROR_CLASS_MISSING,
                    repo_root=self.repo_root,
                )
        coord_out = stamp_output(CoordDesk().run(watermark, ctx), ctx)
        coord_env = envelope_from_output(coord_out, repo_root=self.repo_root)
        self.publish(coord_env)
        pack_md = ""
        if coord_out.artifacts:
            pack_md = coord_out.artifacts[0].content
        digest = sha256_hex(
            canonical_json(
                {
                    "coord": coord_env.canonical(),
                    "desks": [env.canonical() for env in envelopes],
                }
            )
        )
        return AssembleResult(
            as_of_knowledge=watermark,
            envelopes=tuple(envelopes),
            coord=coord_env,
            health=dict(self.health),
            pack_markdown=pack_md,
            content_hash=digest,
            status=coord_out.status,
            completeness_pct=coord_out.completeness_pct,
        )


@dataclass
class MeshDryResult:
    as_of_knowledge: datetime
    fixture_id: str
    session_date: str
    published: tuple[PublishResult, ...]
    assemble: AssembleResult
    content_hash: str
    killed: tuple[str, ...] = ()
    engine_version: str = ENGINE_VERSION

    def as_public_dict(self) -> dict[str, Any]:
        payload = self.assemble.as_public_dict()
        payload.update(
            {
                "fixture_id": self.fixture_id,
                "session_date": self.session_date,
                "killed": list(self.killed),
                "published": [
                    {
                        "desk": row.envelope.desk,
                        "inserted": row.inserted,
                        "content_hash": row.envelope.content_hash,
                        "channels": list(row.channels),
                    }
                    for row in self.published
                ],
                "double_run_hash": self.content_hash,
            }
        )
        return payload


def publish_desk_outputs(
    outputs: Sequence[DeskOutput],
    worker: CoordMeshWorker,
    ctx: DeskContext,
    *,
    skip: Sequence[str] = (),
) -> list[PublishResult]:
    skip_set = set(skip)
    published: list[PublishResult] = []
    for output in outputs:
        if output.slug in skip_set or output.slug == "coord":
            continue
        stamped = stamp_output(output, ctx)
        env = envelope_from_output(stamped, repo_root=worker.repo_root)
        published.append(worker.publish(env, alert=stamped.status == FAILED))
    return published


def mesh_from_fixture(
    path: Path,
    *,
    repo_root: Path,
    killed: Sequence[str] = (),
    store: EnvelopeStore | None = None,
    bus: Bus | None = None,
) -> MeshDryResult:
    """Fixture-only mesh: run desks, publish envelopes, Coord assembles from the store."""
    day = load_frozen_day(path, repo_root=repo_root)
    run_slugs = tuple(slug for slug in PIPELINE if slug != "coord" and slug not in set(killed))
    run = run_from_fixture(path, repo_root=repo_root, slugs=run_slugs, send=False)
    ctx = DeskContext(repo_root=repo_root, fixture=day, thesis=day.thesis)
    worker = CoordMeshWorker(
        store or InMemoryEnvelopeStore(),
        bus or InMemoryBus(),
        repo_root=repo_root,
    )
    published = publish_desk_outputs(run.desks, worker, ctx, skip=killed)
    assemble = worker.assemble(day.as_of_knowledge, ctx, killed=killed)
    return MeshDryResult(
        as_of_knowledge=day.as_of_knowledge,
        fixture_id=day.fixture_id,
        session_date=day.session_date,
        published=tuple(published),
        assemble=assemble,
        content_hash=assemble.content_hash,
        killed=tuple(killed),
    )
