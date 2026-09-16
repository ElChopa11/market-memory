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
PAPER_LIVE_LATER = "paper/live are later phases; Phase 2 stops at skeptic review"
AUTHOR_CANNOT_BE_SOLE_SKEPTIC = "author of the thesis is not the sole skeptic of record"
