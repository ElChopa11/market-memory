"""Paper/shadow ledger errors."""

from __future__ import annotations


class PaperError(Exception):
    """Base error for the shadow ledger."""


class PaperGateError(PaperError):
    """A paper-trade definition-of-done gate failed."""


MISSING_INVALIDATION = "paper trade cannot open without invalidation"
MISSING_MAX_LOSS = "paper trade cannot open without max loss"
MAX_LOSS_NOT_POSITIVE = "max loss must be greater than zero"
MISSING_EXIT_REASON = "paper trade cannot close without an exit reason"
LIVE_NOT_ALLOWED = "paper ledger cannot submit live orders"
