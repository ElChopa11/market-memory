"""Standing source-health / data-quality report. Read-only. No trading credentials."""

from mm_source_health.engine import generate_source_health
from mm_source_health.models import SOURCE_INVENTORY, HealthReport, SourceHealth
from mm_source_health.store import write_source_health_report

__phase__ = 4
LIVE_TRADING_ENABLED = False

__all__ = [
    "LIVE_TRADING_ENABLED",
    "SOURCE_INVENTORY",
    "HealthReport",
    "SourceHealth",
    "generate_source_health",
    "write_source_health_report",
]
