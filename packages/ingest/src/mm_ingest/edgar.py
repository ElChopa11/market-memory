"""SEC EDGAR adapter (IMP-024). Paper only. No API key.

``data.sec.gov`` submissions + ``www.sec.gov/Archives`` full text.
Fair-access: declared User-Agent, ≤10 rps. HTTP 403/blocks → unavailable
+ ``error_class`` (never invent filing text). ``file_date`` is an event
stamp only — ``as_of_knowledge`` stays lab ``ingested_at``.
"""

from __future__ import annotations

import html as html_lib
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import yaml

from mm_common.enums import EvidenceType, SourceKind
from mm_common.hashing import sha256_hex
from mm_common.http import (
    DEFAULT_MAX_ATTEMPTS,
    ERROR_CONFIG,
    ERROR_NONE,
    ERROR_PARSE,
    ERROR_RATE_LIMITED,
    ERROR_TOS_OR_BLOCKED,
    classify_http_status,
    http_get,
)
from mm_common.schemas import ObservationEnvelope
from mm_common.time import parse_utc
from mm_ingest.config import load_ingest_settings, repo_root
from mm_ingest.degrade import feed_status_envelope
from mm_ingest.licence import verdict_for
from mm_ingest.rate_limit import RateLimitBudget, RpsLimiter, budget_from_settings, rps_from_settings, timeout_from_settings
from mm_ingest.sources import EDGAR_SOURCE_NAME
from mm_provenance.envelope import build_envelope

DEFAULT_USER_AGENT = (
    "MarketMemory research-lab (github.com/ElChopa11/market-memory; intel-ingest; paper-only)"
)
DEFAULT_DATA_BASE = "https://data.sec.gov"
DEFAULT_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"
MAX_RPS = 10.0
ALLOWED_HOSTS = frozenset({"data.sec.gov", "www.sec.gov", "sec.gov", "efts.sec.gov"})
FORBIDDEN_HOSTS = frozenset(
    {
        "api.nasdaq.com",
        "feeds.finance.yahoo.com",
        "finance.yahoo.com",
        "query1.finance.yahoo.com",
        "query2.finance.yahoo.com",
        "edgar-mirror.sec-api.io",
    }
)
METRIC_FILING = "edgar_filing"
METRIC_LOCKUP = "lockup_extract"
METRIC_EARNINGS = "confirmed_earnings"
FORM_424B4 = "424B4"
FORM_8K = "8-K"
ITEM_202 = "2.02"
SECTION_SHARES_ELIGIBLE = "SHARES ELIGIBLE FOR FUTURE SALE"

_TAG_RE = re.compile(r"<[^>]+>", re.IGNORECASE)
_ISO_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
_MONTH_DATE_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{1,2}),\s+(20\d{2})\b",
    re.IGNORECASE,
)
_MONTHS = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}


@dataclass(frozen=True)
class LockupTarget:
    instrument: str
    cik: str
    form: str
    url: str
    accession: str = ""
    prospectus_date: str = ""
    qualified_id: str = ""

    def as_public_dict(self) -> dict[str, str]:
        return {
            "instrument": self.instrument,
            "cik": self.cik,
            "form": self.form,
            "url": self.url,
            "accession": self.accession,
            "prospectus_date": self.prospectus_date,
            "qualified_id": self.qualified_id,
        }


@dataclass(frozen=True)
class LockupFacts:
    found: bool
    section: str = ""
    prospectus_dated: str | None = None
    delivery_expected: str | None = None
    lock_up_period: str | None = None
    first_earnings_release_date: str | None = None
    staged_calendar_dates: tuple[str, ...] = ()
    assume_180d: bool = False
    excerpt: str = ""
    error_class: str = ERROR_NONE

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "found": self.found,
            "section": self.section,
            "prospectus_dated": self.prospectus_dated,
            "delivery_expected": self.delivery_expected,
            "lock_up_period": self.lock_up_period,
            "first_earnings_release_date": self.first_earnings_release_date,
            "staged_calendar_dates": list(self.staged_calendar_dates),
            "assume_180d": self.assume_180d,
            "error_class": self.error_class,
        }


@dataclass
class FilingFetch:
    ok: bool
    url: str
    html: str = ""
    error_class: str = ERROR_NONE
    status_code: int | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)


def declared_user_agent(settings: Mapping[str, Any] | None = None) -> str:
    loaded = settings if settings is not None else load_ingest_settings()
    block = _edgar_settings(loaded)
    raw = str(block.get("user_agent") or DEFAULT_USER_AGENT).strip()
    return raw or DEFAULT_USER_AGENT


def _edgar_settings(settings: Mapping[str, Any]) -> dict[str, Any]:
    adapters = settings.get("adapters") if isinstance(settings.get("adapters"), dict) else {}
    if isinstance(adapters.get("edgar"), dict) and adapters["edgar"]:
        merged = dict(adapters["edgar"])
    else:
        merged = {}
    filings = settings.get("filings") if isinstance(settings.get("filings"), dict) else {}
    nested = filings.get("edgar") if isinstance(filings.get("edgar"), dict) else {}
    merged.update(nested)
    return merged


def assert_allowed_url(url: str) -> str | None:
    """Return error_class if the URL is forbidden or not EDGAR. Never fetch those hosts."""
    parsed = urlparse(str(url or ""))
    host = (parsed.hostname or "").lower()
    if not host:
        return ERROR_CONFIG
    if host in FORBIDDEN_HOSTS or host.endswith(".nasdaq.com") or "yahoo.com" in host:
        return ERROR_TOS_OR_BLOCKED
    if host not in ALLOWED_HOSTS:
        return ERROR_CONFIG
    return None


def pad_cik(cik: str) -> str:
    digits = "".join(ch for ch in str(cik) if ch.isdigit())
    return digits.zfill(10) if digits else ""


def accession_nodash(accession: str) -> str:
    return str(accession or "").replace("-", "")


def accession_from_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    # /Archives/edgar/data/{cik}/{accession_nodash}/{file}
    if len(parts) >= 5 and parts[-2].isdigit():
        raw = parts[-2]
        if len(raw) >= 18:
            return f"{raw[:10]}-{raw[10:12]}-{raw[12:]}"
        return raw
    return ""


def filing_observation_id(instrument: str, form: str, file_date: str) -> str:
    compact = str(file_date).replace("-", "")[:8]
    return f"edgar-{str(instrument).upper()}-{str(form).lower()}-{compact}"


def html_to_text(raw: str) -> str:
    text = _TAG_RE.sub(" ", raw or "")
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _month_to_iso(month: str, day: str, year: str) -> str:
    mm = _MONTHS.get(month.lower())
    if not mm:
        return ""
    return f"{year}-{mm}-{int(day):02d}"


def _collect_iso_dates(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in _ISO_DATE_RE.finditer(text):
        value = match.group(1)
        if value not in seen:
            seen.add(value)
            found.append(value)
    for match in _MONTH_DATE_RE.finditer(text):
        value = _month_to_iso(match.group(1), match.group(2), match.group(3))
        if value and value not in seen:
            seen.add(value)
            found.append(value)
    return found


def _sentence_near(text: str, needle: str) -> str | None:
    lowered = text.lower()
    idx = lowered.find(needle.lower())
    if idx < 0:
        return None
    start = text.rfind(".", 0, idx)
    start = 0 if start < 0 else start + 1
    end = text.find(".", idx)
    chunk = text[start:] if end < 0 else text[start : end + 1]
    return re.sub(r"\s+", " ", chunk).strip() or None


def shares_eligible_section(text: str) -> str:
    lowered = text.lower()
    idx = lowered.find("shares eligible for future sale")
    if idx < 0:
        idx = lowered.find("lock-up")
    if idx < 0:
        idx = lowered.find("lock up")
    if idx < 0:
        return ""
    window = text[idx : idx + 8000]
    return re.sub(r"\s+", " ", window).strip()


def extract_lockup_facts(html_or_text: str) -> LockupFacts:
    """Extract lockup facts from stored filing text. Missing section → parse_error."""
    if not str(html_or_text or "").strip():
        return LockupFacts(found=False, error_class=ERROR_PARSE)
    text = html_to_text(html_or_text)
    section = shares_eligible_section(text)
    if not section:
        return LockupFacts(found=False, error_class=ERROR_PARSE)
    dates = _collect_iso_dates(section)
    prospectus = None
    dated_sentence = (
        _sentence_near(text, "prospectus dated")
        or _sentence_near(section, "date of this prospectus")
        or _sentence_near(section, "prospectus dated")
    )
    if dated_sentence:
        dated = _collect_iso_dates(dated_sentence)
        if dated:
            prospectus = dated[0]
    delivery = None
    delivery_sentence = (
        _sentence_near(text, "delivery of the shares")
        or _sentence_near(text, "delivery expected")
        or _sentence_near(section, "on or about")
    )
    if delivery_sentence:
        delivered = _collect_iso_dates(delivery_sentence)
        if delivered:
            delivery = delivered[-1] if prospectus and delivered[0] == prospectus and len(delivered) > 1 else delivered[0]
    lock_period = (
        _sentence_near(section, "lock-up period")
        or _sentence_near(section, "lock up period")
        or _sentence_near(section, "earlier of")
    )
    ferd = _sentence_near(section, "first earnings release date")
    staged = [d for d in dates if d != prospectus]
    assume_flat = not (
        "earlier of" in section.lower()
        or "not a flat" in section.lower()
        or "staged" in section.lower()
        or len(staged) > 1
    )
    excerpt = section[:1200]
    return LockupFacts(
        found=True,
        section=SECTION_SHARES_ELIGIBLE,
        prospectus_dated=prospectus,
        delivery_expected=delivery,
        lock_up_period=lock_period,
        first_earnings_release_date=ferd,
        staged_calendar_dates=tuple(staged),
        assume_180d=assume_flat,
        excerpt=excerpt,
        error_class=ERROR_NONE,
    )


def eight_k_has_item_202(html_or_text: str, items: list[str] | None = None) -> bool:
    if items and any(str(item).strip() == ITEM_202 for item in items):
        return True
    text = html_to_text(html_or_text).lower()
    return "item 2.02" in text or "item 2.02." in text


def load_lockup_targets(path: Path | None = None) -> list[LockupTarget]:
    """Intel lockup_watch names from monitor.yaml. Ingest must not import mm_desks."""
    monitor = path or (repo_root() / "config" / "watchlist" / "monitor.yaml")
    if not monitor.is_file():
        return []
    data = yaml.safe_load(monitor.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return []
    watch = data.get("lockup_watch") if isinstance(data.get("lockup_watch"), dict) else {}
    names = watch.get("names") if isinstance(watch.get("names"), dict) else {}
    out: list[LockupTarget] = []
    for symbol, row in names.items():
        if not isinstance(row, dict):
            continue
        url = str(row.get("url") or "")
        if not url:
            continue
        out.append(
            LockupTarget(
                instrument=str(symbol).upper(),
                cik=str(row.get("cik") or ""),
                form=str(row.get("filing") or FORM_424B4),
                url=url,
                accession=accession_from_url(url),
                prospectus_date=str(row.get("prospectus_date") or "")[:10],
                qualified_id=str(row.get("qualified_id") or ""),
            )
        )
    return out


def _file_date_dt(file_date: str, fallback: datetime) -> datetime:
    raw = str(file_date or "").strip()
    if not raw:
        return fallback
    if "T" in raw:
        return parse_utc(raw)
    return datetime.fromisoformat(f"{raw[:10]}T00:00:00+00:00").astimezone(timezone.utc)


def _row_ingested(row: Mapping[str, Any], default: datetime) -> datetime:
    extra = row.get("ingested_at")
    if extra is None:
        return default
    if isinstance(extra, datetime):
        return extra
    return parse_utc(str(extra))


def filing_envelopes(
    *,
    instrument: str,
    form: str,
    cik: str,
    accession: str,
    file_date: str,
    url: str,
    ingested_at: datetime,
    html: str,
    stale_after_seconds: int = 120,
    prospectus_dated: str | None = None,
    delivery_expected: str | None = None,
    items: list[str] | None = None,
) -> list[ObservationEnvelope]:
    """Typed filing + lockup / 8-K 2.02 extracts from *stored* text. Never invents text."""
    if not str(html or "").strip():
        return [
            feed_status_envelope(
                source_name=EDGAR_SOURCE_NAME,
                instrument=str(instrument).upper(),
                ingested_at=ingested_at,
                error_class=ERROR_PARSE,
                notes=("EDGAR filing body empty; no lockup or earnings invented",),
                venue="filings",
                source_url_or_id=url or "edgar:empty",
                metric=METRIC_FILING,
            )
        ]
    event = _file_date_dt(file_date, ingested_at)
    obs_id = filing_observation_id(instrument, form, file_date or event.date().isoformat())
    content_hash = sha256_hex(html)
    extras = {
        "form": str(form),
        "cik": str(cik),
        "accession": str(accession or accession_from_url(url)),
        "file_date": event.date().isoformat(),
        "observation_id": obs_id,
    }
    filing_payload: dict[str, Any] = {
        "observation_id": obs_id,
        "form": form,
        "cik": cik,
        "accession": extras["accession"],
        "file_date": extras["file_date"],
        "url": url,
        "filing_content_hash": content_hash,
        "licence_verdict": verdict_for(EDGAR_SOURCE_NAME).verdict,
        "raw": {"html": html, "historical": True},
        "historical": True,
    }
    if prospectus_dated:
        filing_payload["prospectus_dated"] = prospectus_dated
    if delivery_expected:
        filing_payload["delivery_expected"] = delivery_expected
    if items:
        filing_payload["items"] = list(items)
    out = [
        build_envelope(
            source_name=EDGAR_SOURCE_NAME,
            source_kind=SourceKind.NEWS,
            source_url_or_id=obs_id,
            instrument=str(instrument).upper(),
            metric=METRIC_FILING,
            value=obs_id,
            published_at=event,
            ingested_at=ingested_at,
            market_time=event,
            payload=filing_payload,
            extras=extras,
            historical=True,
            stale_after_seconds=stale_after_seconds,
            venue="filings",
            evidence_type=EvidenceType.FACT,
        )
    ]
    form_u = str(form).upper().replace(" ", "")
    if form_u in {"424B4", "424B3", "S-1", "S1", "424B5"}:
        facts = extract_lockup_facts(html)
        if not facts.found:
            out.append(
                feed_status_envelope(
                    source_name=EDGAR_SOURCE_NAME,
                    instrument=str(instrument).upper(),
                    ingested_at=ingested_at,
                    published_at=event,
                    error_class=facts.error_class or ERROR_PARSE,
                    notes=("Shares Eligible / lock-up language missing from stored filing; not invented",),
                    venue="filings",
                    source_url_or_id=obs_id,
                    metric=METRIC_LOCKUP,
                    payload={"file_date": extras["file_date"], "filing_content_hash": content_hash},
                )
            )
            return out
        lockup_payload = {
            "observation_id": obs_id,
            "form": form,
            "cik": cik,
            "accession": extras["accession"],
            "file_date": extras["file_date"],
            "url": url,
            "filing_content_hash": content_hash,
            "licence_verdict": verdict_for(EDGAR_SOURCE_NAME).verdict,
            "historical": True,
            **facts.as_public_dict(),
            "excerpt": facts.excerpt,
        }
        if prospectus_dated and not lockup_payload.get("prospectus_dated"):
            lockup_payload["prospectus_dated"] = prospectus_dated
        if delivery_expected and not lockup_payload.get("delivery_expected"):
            lockup_payload["delivery_expected"] = delivery_expected
        out.append(
            build_envelope(
                source_name=EDGAR_SOURCE_NAME,
                source_kind=SourceKind.NEWS,
                source_url_or_id=obs_id,
                instrument=str(instrument).upper(),
                metric=METRIC_LOCKUP,
                value=obs_id,
                published_at=event,
                ingested_at=ingested_at,
                market_time=event,
                payload=lockup_payload,
                extras=extras,
                historical=True,
                stale_after_seconds=stale_after_seconds,
                venue="filings",
                evidence_type=EvidenceType.FACT,
            )
        )
    if form_u in {"8-K", "8K"} and eight_k_has_item_202(html, items):
        earn_extras = dict(extras)
        earn_extras["item"] = ITEM_202
        out.append(
            build_envelope(
                source_name=EDGAR_SOURCE_NAME,
                source_kind=SourceKind.NEWS,
                source_url_or_id=obs_id,
                instrument=str(instrument).upper(),
                metric=METRIC_EARNINGS,
                value=f"item_{ITEM_202}",
                published_at=event,
                ingested_at=ingested_at,
                market_time=event,
                payload={
                    "observation_id": obs_id,
                    "form": FORM_8K,
                    "item": ITEM_202,
                    "signal": "confirmed_earnings",
                    "estimates": None,
                    "file_date": extras["file_date"],
                    "cik": cik,
                    "accession": extras["accession"],
                    "url": url,
                    "filing_content_hash": content_hash,
                    "licence_verdict": verdict_for(EDGAR_SOURCE_NAME).verdict,
                    "historical": True,
                },
                extras=earn_extras,
                historical=True,
                stale_after_seconds=stale_after_seconds,
                venue="filings",
                evidence_type=EvidenceType.FACT,
            )
        )
    return out


def fetch_filing(
    url: str,
    *,
    http_client: httpx.Client | None = None,
    budget: RateLimitBudget | None = None,
    rps: RpsLimiter | None = None,
    user_agent: str | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Callable[[float], None] | None = None,
) -> FilingFetch:
    blocked = assert_allowed_url(url)
    if blocked:
        return FilingFetch(
            ok=False,
            url=url,
            error_class=blocked,
            notes=(f"refused host (error_class={blocked}); no nasdaq/yahoo scrape; no invented text",),
        )
    limiter = budget or RateLimitBudget(name="edgar", max_requests_per_minute=600)
    if not limiter.allow():
        return FilingFetch(
            ok=False,
            url=url,
            error_class=ERROR_RATE_LIMITED,
            notes=("EDGAR rate-limit budget exhausted; no filing invented",),
        )
    if rps is not None:
        rps.wait(sleep)
    ua = user_agent or declared_user_agent()
    owns = http_client is None
    client = http_client or httpx.Client(timeout=8.0, headers={"User-Agent": ua, "Accept-Encoding": "gzip, deflate"})
    try:
        client.headers["User-Agent"] = ua
        kwargs: dict[str, Any] = {"max_attempts": max_attempts, "parse_json": False}
        if sleep is not None:
            kwargs["sleep"] = sleep
        result = http_get(client, url, **kwargs)
        if not result.ok:
            klass = result.error_class
            if result.status_code is not None:
                klass = classify_http_status(result.status_code)
            return FilingFetch(
                ok=False,
                url=url,
                error_class=klass,
                status_code=result.status_code,
                notes=(f"EDGAR HTTP failed (error_class={klass}); filing text not invented",),
            )
        body = result.text or ""
        if not body.strip() or body.strip().lower() in {"<html></html>", "forbidden", "not found"}:
            return FilingFetch(
                ok=False,
                url=url,
                error_class=ERROR_PARSE,
                status_code=result.status_code,
                notes=("EDGAR returned an empty/stub body; filing text not invented",),
            )
        if "your request has been blocked" in body.lower() or "unusual access" in body.lower():
            return FilingFetch(
                ok=False,
                url=url,
                html="",
                error_class=ERROR_TOS_OR_BLOCKED,
                status_code=result.status_code,
                notes=("EDGAR fair-access block in body; filing text not invented",),
            )
        return FilingFetch(ok=True, url=url, html=body, status_code=result.status_code)
    finally:
        if owns:
            client.close()


def envelopes_from_stored_or_error(
    row: Mapping[str, Any],
    *,
    ingested_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    instrument = str(row.get("instrument") or "UNKNOWN").upper()
    error_class = str(row.get("error_class") or "")
    url = str(row.get("url") or row.get("source_url_or_id") or "")
    if error_class and error_class != ERROR_NONE:
        return [
            feed_status_envelope(
                source_name=EDGAR_SOURCE_NAME,
                instrument=instrument,
                ingested_at=ingested_at,
                error_class=error_class,
                notes=(str(row.get("notes") or f"EDGAR unavailable (error_class={error_class}); no filing invented"),),
                venue="filings",
                source_url_or_id=url or f"edgar:{error_class}",
                metric=str(row.get("metric") or METRIC_FILING),
                payload={"status_code": row.get("status_code"), "form": row.get("form")},
            )
        ]
    html = str(row.get("html") or row.get("text") or "")
    html_path = row.get("html_path")
    if not html and html_path:
        path = Path(str(html_path))
        if not path.is_file():
            path = repo_root() / path
        if path.is_file():
            html = path.read_text(encoding="utf-8")
        else:
            return [
                feed_status_envelope(
                    source_name=EDGAR_SOURCE_NAME,
                    instrument=instrument,
                    ingested_at=ingested_at,
                    error_class=ERROR_PARSE,
                    notes=(f"stored filing missing at {html_path}; no lockup invented",),
                    venue="filings",
                    source_url_or_id=url or str(html_path),
                    metric=METRIC_FILING,
                )
            ]
    return filing_envelopes(
        instrument=instrument,
        form=str(row.get("form") or FORM_424B4),
        cik=str(row.get("cik") or ""),
        accession=str(row.get("accession") or accession_from_url(url)),
        file_date=str(row.get("file_date") or row.get("prospectus_dated") or ""),
        url=url,
        ingested_at=_row_ingested(row, ingested_at),
        html=html,
        stale_after_seconds=stale_after_seconds,
        prospectus_dated=None if row.get("prospectus_dated") is None else str(row.get("prospectus_dated")),
        delivery_expected=None if row.get("delivery_expected") is None else str(row.get("delivery_expected")),
        items=list(row.get("items") or []) if isinstance(row.get("items"), list) else None,
    )


def pull_lockup_targets(
    targets: list[LockupTarget] | None = None,
    *,
    ingested_at: datetime,
    http_client: httpx.Client | None = None,
    settings: Mapping[str, Any] | None = None,
    sleep: Callable[[float], None] | None = None,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    loaded = settings if settings is not None else load_ingest_settings()
    wanted = targets if targets is not None else load_lockup_targets()
    if not wanted:
        return [
            feed_status_envelope(
                source_name=EDGAR_SOURCE_NAME,
                instrument="LOCKUP",
                ingested_at=ingested_at,
                error_class=ERROR_CONFIG,
                notes=("no lockup_watch targets; no filing invented",),
                venue="filings",
                source_url_or_id="edgar:lockup_watch",
            )
        ]
    ua = declared_user_agent(loaded)
    timeout = timeout_from_settings(dict(loaded), "edgar", default=8.0)
    budget = budget_from_settings(dict(loaded), "edgar", default_rpm=600)
    rps = RpsLimiter(name="edgar", max_rps=min(MAX_RPS, rps_from_settings(dict(loaded), "edgar", default=MAX_RPS)))
    owns = http_client is None
    client = http_client or httpx.Client(
        timeout=timeout,
        headers={"User-Agent": ua, "Accept-Encoding": "gzip, deflate"},
    )
    out: list[ObservationEnvelope] = []
    try:
        for target in wanted:
            blocked = assert_allowed_url(target.url)
            if blocked:
                out.append(
                    feed_status_envelope(
                        source_name=EDGAR_SOURCE_NAME,
                        instrument=target.instrument,
                        ingested_at=ingested_at,
                        error_class=blocked,
                        notes=(f"lockup url refused (error_class={blocked}); no invented text",),
                        venue="filings",
                        source_url_or_id=target.url,
                        metric=METRIC_LOCKUP,
                    )
                )
                continue
            fetched = fetch_filing(
                target.url,
                http_client=client,
                budget=budget,
                rps=rps,
                user_agent=ua,
                sleep=sleep,
            )
            if not fetched.ok:
                out.append(
                    feed_status_envelope(
                        source_name=EDGAR_SOURCE_NAME,
                        instrument=target.instrument,
                        ingested_at=ingested_at,
                        error_class=fetched.error_class,
                        notes=fetched.notes,
                        venue="filings",
                        source_url_or_id=target.url,
                        metric=METRIC_LOCKUP,
                        payload={"status_code": fetched.status_code, "cik": target.cik, "form": target.form},
                    )
                )
                continue
            out.extend(
                filing_envelopes(
                    instrument=target.instrument,
                    form=target.form,
                    cik=target.cik,
                    accession=target.accession or accession_from_url(target.url),
                    file_date=target.prospectus_date,
                    url=target.url,
                    ingested_at=ingested_at,
                    html=fetched.html,
                    stale_after_seconds=stale_after_seconds,
                    prospectus_dated=target.prospectus_date or None,
                )
            )
    finally:
        if owns:
            client.close()
    return out


def submissions_url(cik: str, *, base_url: str = DEFAULT_DATA_BASE) -> str:
    return f"{base_url.rstrip('/')}/submissions/CIK{pad_cik(cik)}.json"


def archives_url(cik: str, accession: str, filename: str, *, archives_base: str = DEFAULT_ARCHIVES_BASE) -> str:
    return f"{archives_base.rstrip('/')}/{int(pad_cik(cik))}/{accession_nodash(accession)}/{filename}"
