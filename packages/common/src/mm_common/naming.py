"""Canonical desk and artifact naming (Phase 6c-2 / IMP-019).

Machine ids (desk slugs, PLAYBOOK artifact types) are stable. Human labels are
looked up here and nowhere else. Unknown ids fail closed.

Coord is orchestration only — not a publishing desk. Delivery is Ops-owned.
Sleeves (crypto, equities, chart, watchlist, listings, scorecard, decay, flow, macro, briefing) and gates (skeptic,
risk) are labels, not extra desks.

Must not hold secrets, place orders, or talk to Hyperliquid.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

INTEL = "intel"
RESEARCH = "research"
QUANT = "quant"
IC_RISK = "ic_risk"
OPS = "ops"
WATCHLIST = "watchlist"
LISTINGS = "listings"
SCORECARD = "scorecard"
DECAY = "decay"

COORD = "coord"
ALERTS = "alerts"

KIND_PUBLISHING = "publishing"
KIND_ORCHESTRATION = "orchestration"
KIND_ROUTE = "route"
KIND_SLEEVE = "sleeve"
KIND_GATE = "gate"

DAILY_BIAS = "DAILY_BIAS"
EDGE_SCAN = "EDGE_SCAN"
INTEL_PACKET = "INTEL_PACKET"
CHART_ARTIFACT = "CHART_ARTIFACT"
OFFICIAL_BRIEF = "OFFICIAL_BRIEF"
STATE_CARD = "STATE_CARD"


class UnknownNameError(ValueError):
    """Fail-closed: unknown desk slug, route, sleeve, gate, or artifact type."""


@dataclass(frozen=True)
class NamedSlug:
    """Stable machine id plus the human label operators see."""

    slug: str
    display: str
    short: str
    tier: str
    kind: str
    notes: str = ""


@dataclass(frozen=True)
class ArtifactName:
    """PLAYBOOK ladder type: machine id vs human label vs owning desk slug."""

    artifact_type: str
    display: str
    desk: str
    notes: str = ""


_PUBLISHING: tuple[NamedSlug, ...] = (
    NamedSlug(
        slug=INTEL,
        display="Intel (Market Intelligence)",
        short="Intel",
        tier="2",
        kind=KIND_PUBLISHING,
        notes="Ingest + flow + macro + Pulse sleeves",
    ),
    NamedSlug(
        slug=RESEARCH,
        display="Research (Investment Research)",
        short="Research",
        tier="3",
        kind=KIND_PUBLISHING,
        notes="Crypto + equities + chart + watchlist + listings sleeves",
    ),
    NamedSlug(
        slug=QUANT,
        display="Quant",
        short="Quant",
        tier="4",
        kind=KIND_PUBLISHING,
        notes="Closed-verdict triage; factor math; like-for-like pack scorecards; prompt-hash decay watch; not a call",
    ),
    NamedSlug(
        slug=IC_RISK,
        display="IC/Risk (Investment Committee & Risk)",
        short="IC/Risk",
        tier="5-6",
        kind=KIND_PUBLISHING,
        notes="Two gates (Skeptic + Risk), not two desks",
    ),
    NamedSlug(
        slug=OPS,
        display="Ops",
        short="Ops",
        tier="1",
        kind=KIND_PUBLISHING,
        notes="Queue hygiene, pack assemble, delivery, decay-watch alert path. Coord/Don orchestrates — not a sixth desk",
    ),
)

_ORCHESTRATION: tuple[NamedSlug, ...] = (
    NamedSlug(
        slug=COORD,
        display="Coord (orchestration)",
        short="Coord",
        tier="1",
        kind=KIND_ORCHESTRATION,
        notes="Don/Coord is orchestration only. Channel coord.assemble is not a desk slug.",
    ),
)

_ROUTES: tuple[NamedSlug, ...] = (
    NamedSlug(
        slug=ALERTS,
        display="Alerts",
        short="Alerts",
        tier="1",
        kind=KIND_ROUTE,
        notes="Ops-owned Telegram sink. Not a publishing desk.",
    ),
)

_SLEEVES: tuple[NamedSlug, ...] = (
    NamedSlug(
        slug="crypto",
        display="Research (Investment Research) / crypto sleeve",
        short="crypto sleeve",
        tier="3a",
        kind=KIND_SLEEVE,
        notes="Maps into research. Not a publishing desk.",
    ),
    NamedSlug(
        slug="equities",
        display="Research (Investment Research) / equities sleeve",
        short="equities sleeve",
        tier="3b",
        kind=KIND_SLEEVE,
        notes="Maps into research. Not a publishing desk.",
    ),
    NamedSlug(
        slug="chart",
        display="Research (Investment Research) / chart product",
        short="chart product",
        tier="3",
        kind=KIND_SLEEVE,
        notes="Chart is a Research product, not a desk.",
    ),
    NamedSlug(
        slug="flow",
        display="Intel (Market Intelligence) / flow sleeve",
        short="flow sleeve",
        tier="2",
        kind=KIND_SLEEVE,
        notes="Maps into intel. Not a publishing desk.",
    ),
    NamedSlug(
        slug="macro",
        display="Intel (Market Intelligence) / macro sleeve",
        short="macro sleeve",
        tier="2",
        kind=KIND_SLEEVE,
        notes="Maps into intel. Not a publishing desk.",
    ),
    NamedSlug(
        slug="briefing",
        display="Intel (Market Intelligence) / Pulse sleeve",
        short="Pulse sleeve",
        tier="2",
        kind=KIND_SLEEVE,
        notes="Maps into intel. Not a publishing desk.",
    ),
    NamedSlug(
        slug="watchlist",
        display="Research (Investment Research) / watchlist monitor",
        short="watchlist monitor",
        tier="3",
        kind=KIND_SLEEVE,
        notes="Daily scan of locked universe (in_universe ∪ watch_only). Not a call. Not a sixth desk.",
    ),
    NamedSlug(
        slug="listings",
        display="Research (Investment Research) / listings IPO screen",
        short="listings / IPO screen",
        tier="3",
        kind=KIND_SLEEVE,
        notes="IPO / direct listing / index-event screen. Not a call. Not a sixth desk. Not universe promotion.",
    ),
    NamedSlug(
        slug="scorecard",
        display="Quant / like-for-like pack scorecard",
        short="pack scorecard",
        tier="4",
        kind=KIND_SLEEVE,
        notes="Like-for-like pack scoring with provenance. Incomparable artifacts stay tagged, never scored as equals. Not a call. Not a sixth desk.",
    ),
    NamedSlug(
        slug="decay",
        display="Quant / prompt-hash decay watch",
        short="decay watch",
        tier="4",
        kind=KIND_SLEEVE,
        notes="Prompt and config SHA-256 drift watch. Mismatch → Ops-owned NOTIFY/queue signal. Does not waive gates or invent scorecard numbers. Not a sixth desk.",
    ),
)

_GATES: tuple[NamedSlug, ...] = (
    NamedSlug(
        slug="skeptic",
        display="IC/Risk / Skeptic gate",
        short="Skeptic gate",
        tier="5",
        kind=KIND_GATE,
        notes="Gate inside ic_risk, not a desk.",
    ),
    NamedSlug(
        slug="risk",
        display="IC/Risk / Risk gate",
        short="Risk gate",
        tier="6",
        kind=KIND_GATE,
        notes="Gate inside ic_risk, not a desk.",
    ),
)

_ARTIFACTS: tuple[ArtifactName, ...] = (
    ArtifactName(DAILY_BIAS, "Daily Bias", RESEARCH, "Instrument / direction / conviction / level"),
    ArtifactName(EDGE_SCAN, "Edge Scan", RESEARCH, "SCAN_CARD fields + optional writer prose"),
    ArtifactName(INTEL_PACKET, "Intel Packet", INTEL, "Feeds, missing, idea detail"),
    ArtifactName(CHART_ARTIFACT, "Chart Artifact", RESEARCH, "Levels + PNG; chart is a Research product"),
    ArtifactName(OFFICIAL_BRIEF, "Official Brief", OPS, "30-second executive cut"),
    ArtifactName(STATE_CARD, "State Card", OPS, "Flat / armed / in / cooling + permission + rearm"),
)

PUBLISHING_DESKS: tuple[str, ...] = tuple(row.slug for row in _PUBLISHING)
PIPELINE: tuple[str, ...] = PUBLISHING_DESKS
MESH_DESKS: tuple[str, ...] = (INTEL, RESEARCH, QUANT, IC_RISK)
ROUTE_SLUGS: tuple[str, ...] = PUBLISHING_DESKS + (ALERTS,)
ARTIFACT_TYPES: tuple[str, ...] = tuple(row.artifact_type for row in _ARTIFACTS)
RETIRED_DESK_SLUGS: tuple[str, ...] = (
    "crypto",
    "equities",
    "flow",
    "macro",
    "chart",
    "skeptic",
    "risk",
    COORD,
    "briefing",
)
SLEEVE_MAP: dict[str, str] = {
    "crypto": RESEARCH,
    "equities": RESEARCH,
    "chart": RESEARCH,
    "watchlist": RESEARCH,
    "listings": RESEARCH,
    "scorecard": QUANT,
    "decay": QUANT,
    "flow": INTEL,
    "macro": INTEL,
    "briefing": INTEL,
    "skeptic": IC_RISK,
    "risk": IC_RISK,
    COORD: OPS,
}
GATES_IN_IC_RISK: tuple[str, ...] = ("skeptic", "risk")
ASSEMBLE_CHANNEL = "coord.assemble"
DQ_CHANNEL = "dq.event"

_BY_SLUG: dict[str, NamedSlug] = {
    row.slug: row for row in (*_PUBLISHING, *_ORCHESTRATION, *_ROUTES, *_SLEEVES, *_GATES)
}
_ARTIFACT_BY_TYPE: dict[str, ArtifactName] = {row.artifact_type: row for row in _ARTIFACTS}


def _norm(value: str) -> str:
    return str(value or "").strip()


def _unknown(kind: str, value: str, allowed: tuple[str, ...]) -> UnknownNameError:
    listed = ", ".join(allowed)
    return UnknownNameError(f"unknown {kind} {value!r}; choose from {listed}")


def require_publishing_desk(slug: str) -> NamedSlug:
    key = _norm(slug)
    row = _BY_SLUG.get(key)
    if row is None or row.kind != KIND_PUBLISHING:
        raise _unknown("publishing desk", slug, PUBLISHING_DESKS)
    return row


def require_route_slug(slug: str) -> NamedSlug:
    """Telegram / CLI delivery routes: five desks plus the alerts sink."""
    key = _norm(slug)
    row = _BY_SLUG.get(key)
    if row is None or key not in ROUTE_SLUGS:
        raise _unknown("delivery route", slug, ROUTE_SLUGS)
    return row


def require_artifact_type(artifact_type: str) -> ArtifactName:
    key = _norm(artifact_type)
    row = _ARTIFACT_BY_TYPE.get(key)
    if row is None:
        raise _unknown("artifact type", artifact_type, ARTIFACT_TYPES)
    return row


def require_named_slug(slug: str) -> NamedSlug:
    """Publishing desk, sleeve, gate, coord, or alerts. Still fail-closed."""
    key = _norm(slug)
    row = _BY_SLUG.get(key)
    if row is None:
        raise _unknown("name", slug, tuple(_BY_SLUG))
    return row


def desk_display(slug: str) -> str:
    return require_publishing_desk(slug).display


def desk_short(slug: str) -> str:
    return require_publishing_desk(slug).short


def desk_tier(slug: str) -> str:
    return require_publishing_desk(slug).tier


def sleeve_display(slug: str) -> str:
    row = require_named_slug(slug)
    if row.kind not in {KIND_SLEEVE, KIND_GATE}:
        raise _unknown("sleeve or gate", slug, tuple(s.slug for s in (*_SLEEVES, *_GATES)))
    return row.display


def sleeve_tier(slug: str) -> str:
    row = require_named_slug(slug)
    if row.kind not in {KIND_SLEEVE, KIND_GATE}:
        raise _unknown("sleeve or gate", slug, tuple(s.slug for s in (*_SLEEVES, *_GATES)))
    return row.tier


def coord_display() -> str:
    return require_named_slug(COORD).display


def alerts_display() -> str:
    return require_named_slug(ALERTS).display


def artifact_display(artifact_type: str) -> str:
    return require_artifact_type(artifact_type).display


def artifact_desk(artifact_type: str) -> str:
    return require_artifact_type(artifact_type).desk


def publishing_slugs_help() -> str:
    return "|".join(PUBLISHING_DESKS)


def route_slugs_help() -> str:
    return "|".join(ROUTE_SLUGS)


def telegram_header(
    slug: str,
    *,
    artifact_type: str | None = None,
    sleeve: str | None = None,
) -> str:
    """Human Telegram banner. Machine ids stay on the envelope (`desk` = slug)."""
    row = require_route_slug(slug)
    line = f"{row.display} · {row.slug}"
    if sleeve:
        sleeve_row = require_named_slug(sleeve)
        if sleeve_row.kind != KIND_SLEEVE:
            raise _unknown("sleeve", sleeve, tuple(s.slug for s in _SLEEVES))
        line = f"{line} · {sleeve_row.short}"
    if artifact_type:
        art = require_artifact_type(artifact_type)
        line = f"{line} · {art.display} ({art.artifact_type})"
    return line


def with_telegram_header(
    markdown: str,
    slug: str,
    *,
    artifact_type: str | None = None,
    sleeve: str | None = None,
) -> str:
    header = telegram_header(slug, artifact_type=artifact_type, sleeve=sleeve)
    body = markdown or ""
    if body.startswith(header):
        return body
    if not body:
        return header + "\n"
    return f"{header}\n\n{body}"


def roster_lines() -> tuple[str, ...]:
    return tuple(f"{row.slug}: {row.display}" for row in _PUBLISHING)


def as_config_dict() -> dict[str, Any]:
    """Operator-facing shape. Tests assert this matches config/desks/naming.yaml."""

    def named(row: NamedSlug) -> dict[str, str]:
        payload = {
            "slug": row.slug,
            "display": row.display,
            "short": row.short,
            "tier": row.tier,
            "kind": row.kind,
        }
        if row.notes:
            payload["notes"] = row.notes
        return payload

    def art(row: ArtifactName) -> dict[str, str]:
        payload = {
            "id": row.artifact_type,
            "display": row.display,
            "desk": row.desk,
        }
        if row.notes:
            payload["notes"] = row.notes
        return payload

    return {
        "version": "imp-031.1",
        "publishing_desks": [named(row) for row in _PUBLISHING],
        "orchestration": [named(row) for row in _ORCHESTRATION],
        "routes": [named(row) for row in _ROUTES],
        "sleeves": [named(row) for row in _SLEEVES],
        "gates": [named(row) for row in _GATES],
        "artifacts": [art(row) for row in _ARTIFACTS],
        "sleeve_map": dict(SLEEVE_MAP),
        "channels": {
            "assemble": ASSEMBLE_CHANNEL,
            "dq": DQ_CHANNEL,
        },
    }


def assert_config_matches(raw: Mapping[str, Any]) -> None:
    """Fail closed if YAML drifts from this module."""
    expected = as_config_dict()
    if dict(raw) != expected:
        raise UnknownNameError("config/desks/naming.yaml does not match mm_common.naming")
