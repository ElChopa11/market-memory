"""Source metadata for Phase 5b feeds. No secrets."""

from __future__ import annotations

from dataclasses import dataclass

from mm_common.enums import SourceKind
from mm_ingest.hl_info import DEFAULT_INFO_URL
from mm_provenance.normalize import HL_BASE_URL, HL_SOURCE_KIND, HL_SOURCE_NAME, HL_TOS_NOTES


@dataclass(frozen=True)
class SourceMeta:
    name: str
    kind: SourceKind
    base_url: str
    trust_tier: int
    tos_notes: str


POLYGON_SOURCE_NAME = "polygon"
POLYGON_BASE_URL = "https://api.polygon.io"
POLYGON_TOS_NOTES = (
    "Polygon.io Stocks REST, ToS-lawful, env POLYGON_API_KEY only. "
    "Never commit the key. Degrade-never-invent on missing/rate-limited/not-on-plan."
)

FRED_SOURCE_NAME = "fred"
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_TOS_NOTES = "FRED observations API. Env FRED_API_KEY only. Missing key → unavailable, never invent a series."

EDGAR_SOURCE_NAME = "edgar"
EDGAR_BASE_URL = "https://data.sec.gov"
EDGAR_TOS_NOTES = (
    "SEC EDGAR public records (data.sec.gov submissions + Archives). Free, no API key. "
    "Declared User-Agent required. Fair-access max 10 rps. licence_verdict ok_gov "
    "(redistributable_official via 15 U.S.C. § 78ll). Lockups are prospectus formulas, "
    "not a flat 180 days. file_date is not the knowledge clock."
)
EDGAR_DEFAULT_UA = "ElChopa11-market-memory filings (https://github.com/ElChopa11/market-memory)"

COINGECKO_SOURCE_NAME = "coingecko"
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3/simple/price"
COINGECKO_TOS_NOTES = "CoinGecko public REST. No key for simple/price. Rate-limit → unavailable."

BINANCE_SOURCE_NAME = "binance.public"
BINANCE_BASE_URL = "https://api.binance.com/api/v3/ticker/price"
BINANCE_TOS_NOTES = "Binance public market-data REST only. No signed endpoints, no orders."

CALENDAR_SOURCE_NAME = "calendar.yaml"
CALENDAR_BASE_URL = "config/briefing/calendar.yaml"
CALENDAR_TOS_NOTES = "Fixture-friendly economic calendar. No live calendar API in Phase 5b."

HL_STRUCTURE_SOURCE_NAME = HL_SOURCE_NAME

REGISTRY: dict[str, SourceMeta] = {
    HL_SOURCE_NAME: SourceMeta(
        name=HL_SOURCE_NAME,
        kind=HL_SOURCE_KIND,
        base_url=HL_BASE_URL or DEFAULT_INFO_URL,
        trust_tier=4,
        tos_notes=HL_TOS_NOTES,
    ),
    POLYGON_SOURCE_NAME: SourceMeta(
        name=POLYGON_SOURCE_NAME,
        kind=SourceKind.EXCHANGE,
        base_url=POLYGON_BASE_URL,
        trust_tier=4,
        tos_notes=POLYGON_TOS_NOTES,
    ),
    FRED_SOURCE_NAME: SourceMeta(
        name=FRED_SOURCE_NAME,
        kind=SourceKind.MACRO,
        base_url=FRED_BASE_URL,
        trust_tier=3,
        tos_notes=FRED_TOS_NOTES,
    ),
    EDGAR_SOURCE_NAME: SourceMeta(
        name=EDGAR_SOURCE_NAME,
        kind=SourceKind.NEWS,
        base_url=EDGAR_BASE_URL,
        trust_tier=4,
        tos_notes=EDGAR_TOS_NOTES,
    ),
    COINGECKO_SOURCE_NAME: SourceMeta(
        name=COINGECKO_SOURCE_NAME,
        kind=SourceKind.EXCHANGE,
        base_url=COINGECKO_BASE_URL,
        trust_tier=3,
        tos_notes=COINGECKO_TOS_NOTES,
    ),
    BINANCE_SOURCE_NAME: SourceMeta(
        name=BINANCE_SOURCE_NAME,
        kind=SourceKind.EXCHANGE,
        base_url=BINANCE_BASE_URL,
        trust_tier=3,
        tos_notes=BINANCE_TOS_NOTES,
    ),
    CALENDAR_SOURCE_NAME: SourceMeta(
        name=CALENDAR_SOURCE_NAME,
        kind=SourceKind.MACRO,
        base_url=CALENDAR_BASE_URL,
        trust_tier=2,
        tos_notes=CALENDAR_TOS_NOTES,
    ),
}


def edgar_headers(user_agent: str | None = None) -> dict[str, str]:
    ua = (user_agent or EDGAR_DEFAULT_UA).strip() or EDGAR_DEFAULT_UA
    return {
        "User-Agent": ua,
        "Accept-Encoding": "gzip, deflate",
        "Accept": "application/json, text/plain, */*",
    }


def meta_for(name: str, *, kind: str | None = None, base_url: str | None = None) -> SourceMeta:
    if name in REGISTRY:
        return REGISTRY[name]
    return SourceMeta(
        name=name,
        kind=SourceKind(kind) if kind else SourceKind.INTERNAL,
        base_url=base_url or "",
        trust_tier=2,
        tos_notes="Unknown ingest source; degrade-never-invent.",
    )
