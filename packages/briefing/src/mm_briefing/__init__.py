"""Market Pulse briefing engine (Phase 3). Must not execute trades.

Alerts never push without threshold config.
"""

from mm_briefing.alerts import evaluate_alerts
from mm_briefing.config import load_briefing_settings, load_schedule
from mm_briefing.engine import generate_from_fixture, generate_from_sources, load_fixture_file
from mm_briefing.render import brief_hash
from mm_briefing.schedule import fires_between, next_fire, us_session_status
from mm_briefing.store import write_brief

__phase__ = 3
LIVE_TRADING_ENABLED = False

__all__ = [
    "LIVE_TRADING_ENABLED",
    "brief_hash",
    "evaluate_alerts",
    "fires_between",
    "generate_from_fixture",
    "generate_from_sources",
    "load_briefing_settings",
    "load_fixture_file",
    "load_schedule",
    "next_fire",
    "us_session_status",
    "write_brief",
]
