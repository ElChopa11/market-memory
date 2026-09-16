"""Shadow ledger and fill simulation (Phase 4). Must not hold live API wallets or submit orders."""

from mm_paper.errors import PaperError, PaperGateError
from mm_paper.gates import parse_max_loss, require_invalidation, require_open_fields
from mm_paper.ledger import close_paper_trade, open_paper_trade
from mm_paper.models import PaperTradeRecord, compute_slippage_bps

__phase__ = 4
LIVE_TRADING_ENABLED = False

__all__ = [
    "LIVE_TRADING_ENABLED",
    "PaperError",
    "PaperGateError",
    "PaperTradeRecord",
    "close_paper_trade",
    "compute_slippage_bps",
    "open_paper_trade",
    "parse_max_loss",
    "require_invalidation",
    "require_open_fields",
]
