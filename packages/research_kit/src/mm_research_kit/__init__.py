"""Helpers to write research artifacts. No secrets. Must not access trading credentials or import live signing."""

from mm_research_kit.artifacts import artifact_content_hash
from mm_research_kit.errors import GateError, ResearchKitError
from mm_research_kit.evidence import EvidenceLink, has_evidence_links, link_evidence, load_evidence_links
from mm_research_kit.lifecycle import (
    advance_status,
    check_templates,
    check_workspace,
    discover_workspaces,
    read_status,
)
from mm_research_kit.skeptic import open_skeptic_review, record_skeptic_verdict
from mm_research_kit.workspace import ThesisSpec, create_thesis_from_intent, find_workspace

__phase__ = 2
LIVE_TRADING_ENABLED = False

__all__ = [
    "EvidenceLink",
    "GateError",
    "LIVE_TRADING_ENABLED",
    "ResearchKitError",
    "ThesisSpec",
    "advance_status",
    "artifact_content_hash",
    "check_templates",
    "check_workspace",
    "create_thesis_from_intent",
    "discover_workspaces",
    "find_workspace",
    "has_evidence_links",
    "link_evidence",
    "load_evidence_links",
    "open_skeptic_review",
    "read_status",
    "record_skeptic_verdict",
]
