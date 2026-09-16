"""Research workspace errors. Never include secrets."""

from __future__ import annotations


class ResearchKitError(Exception):
    """Base error for artifact helpers."""


class GateError(ResearchKitError):
    """A lifecycle definition-of-done gate failed."""


NO_INTENT = "cannot create/mark thesis without intent"
IN_SKEPTIC_WITHOUT_EVIDENCE = "cannot mark in_skeptic without evidence links"
REJECTED_IS_TERMINAL = (
    "rejected theses remain queryable learning records; open a new intent to revive"
)
PAPER_LIVE_LATER = "live is later phase; Phase 4 stops at the paper/shadow ledger"
LIVE_LATER = PAPER_LIVE_LATER
PAPER_INCOMPLETE = "paper trade cannot open without invalidation + max loss"
PAPER_REQUIRES_SKEPTIC_PASS = "cannot mark paper without a skeptic pass"
AUTHOR_CANNOT_BE_SOLE_SKEPTIC = "author of the thesis is not the sole skeptic of record"
