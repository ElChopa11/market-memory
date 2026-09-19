"""SEC EDGAR adapter (IMP-024). Free, official, no API key.

data.sec.gov submissions + Archives 424B4/S-1 lockup evidence. Declared
User-Agent and <=10 rps fair-access. Never invents a flat 180-day expiry.
file_date is not the knowledge clock — as_of_knowledge stays ingested_at.

licence_verdict closed-set is ok_gov (accurate). Plain-language equivalent
redistributable_official follows 15 U.S.C. § 78ll (lawfully obtained EDGAR
information may be used, resold, or redisseminated without restriction).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any

import httpx

from mm_common.enums import EvidenceType, SourceKind
from mm_common.http import (
    DEFAULT_MAX_ATTEMPTS,
    ERROR_NONE,
    ERROR_PARSE,
    ERROR_RATE_LIMITED,
    http_get,
)
from mm_common.schemas import ObservationEnvelope
from mm_common.time import parse_utc
from mm_ingest.config import load_ingest_settings
from mm_ingest.degrade import feed_status_envelope
from mm_ingest.licence import VERDICT_OK_GOV, verdict_for
from mm_ingest.rate_limit import RateLimitBudget
from mm_ingest.sources import EDGAR_SOURCE_NAME, edgar_headers
from mm_provenance.envelope import build_envelope

LOCKUP_METRIC = "lockup_expiry"
FILING_METRIC = "sec_filing"
DEFAULT_FORMS = frozenset({"424B4", "S-1", "S-1/A", "8-K"})
# Language that proves the lockup is a formula, not a flat 180 calendar days.
FORMULA_MARKERS = (
    "earlier of",
    "staged",
    "extension",
    "earnings",
    "qe ",
    "qe_",
    "second trading day",
    "2nd trading",
    "trading day after",
)


def pad_cik(cik: str | int) -> str:
    digits = "".join(ch for ch in str(cik) if ch.isdigit())
    return digits.zfill(10)


def submissions_url(cik: str | int, *, base_url: str) -> str:
    return f"{base_url.rstrip('/')}/submissions/CIK{pad_cik(cik)}.json"


def licence_verdict() -> str:
    verdict = verdict_for(EDGAR_SOURCE_NAME).verdict
    return verdict if verdict else VERDICT_OK_GOV


def _user_agent(settings: Mapping[str, Any] | None = None) -> str:
    loaded = settings if settings is not None else load_ingest_settings()
    adapters = loaded.get("adapters") if isinstance(loaded.get("adapters"), dict) else {}
    block = adapters.get("edgar") if isinstance(adapters.get("edgar"), dict) else {}
    raw = str(block.get("user_agent") or "").strip()
    return raw or "ElChopa11-market-memory filings (https://github.com/ElChopa11/market-memory)"


def client_headers(settings: Mapping[str, Any] | None = None) -> dict[str, str]:
    return edgar_headers(_user_agent(settings))


def parse_recent_filings(payload: Mapping[str, Any]) -> list[dict[str, str]]:
    """Columnar submissions.filings.recent → row dicts. Never invents forms."""
    filings = payload.get("filings") if isinstance(payload.get("filings"), dict) else {}
    recent = filings.get("recent") if isinstance(filings, dict) else {}
    if not isinstance(recent, dict):
        return []
    forms = recent.get("form") or []
    accessions = recent.get("accessionNumber") or []
    dates = recent.get("filingDate") or []
    documents = recent.get("primaryDocument") or []
    if not isinstance(forms, list):
        return []
    rows: list[dict[str, str]] = []
    for i, form in enumerate(forms):
        accession = str(accessions[i]) if i < len(accessions) else ""
        file_date = str(dates[i]) if i < len(dates) else ""
        document = str(documents[i]) if i < len(documents) else ""
        rows.append(
            {
                "form": str(form),
                "accession": accession,
                "file_date": file_date,
                "primary_document": document,
            }
        )
    return rows


def accession_path(accession: str) -> str:
    return accession.replace("-", "")


def archives_url(*, cik: str, accession: str, document: str) -> str:
    return (
        "https://www.sec.gov/Archives/edgar/data/"
        f"{int(pad_cik(cik))}/{accession_path(accession)}/{document}"
    )


def lockup_is_formula(*, assume_180d: bool, excerpt: str, terms: str) -> bool:
    """Refuse a flat 180-day assumption. Staged / earlier-of / extension language is required."""
    if assume_180d:
        return False
    blob = f"{excerpt} {terms}".lower()
    if not blob.strip():
        return False
    return any(marker in blob for marker in FORMULA_MARKERS)


def _row_ingested(row: Mapping[str, Any], default: datetime) -> datetime:
    extra = row.get("ingested_at")
    if extra is None:
        return default
    if isinstance(extra, datetime):
        return extra
    return parse_utc(str(extra))


def _file_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if "T" in text:
        return parse_utc(text)
    return datetime.fromisoformat(f"{text[:10]}T00:00:00+00:00").astimezone(timezone.utc)


def _issuer_instrument(issuer: Mapping[str, Any], ticker: str) -> str:
    return str(issuer.get("qualified_id") or issuer.get("instrument") or f"NASDAQ:{ticker}").upper()


def _degrade(
    *,
    instrument: str,
    ingested_at: datetime,
    error_class: str,
    notes: tuple[str, ...],
    source_url_or_id: str,
    metric: str = "feed_status",
) -> ObservationEnvelope:
    return feed_status_envelope(
        source_name=EDGAR_SOURCE_NAME,
        instrument=instrument,
        ingested_at=ingested_at,
        error_class=error_class,
        notes=notes,
        venue="filings",
        source_url_or_id=source_url_or_id,
        metric=metric,
    )


def normalize_filing_observation(
    *,
    instrument: str,
    cik: str,
    form: str,
    accession: str,
    file_date: str,
    document: str,
    ingested_at: datetime,
    stale_after_seconds: int = 120,
    url: str | None = None,
) -> ObservationEnvelope:
    published = _file_datetime(file_date) or ingested_at
    href = url or archives_url(cik=cik, accession=accession, document=document)
    return build_envelope(
        source_name=EDGAR_SOURCE_NAME,
        source_kind=SourceKind.NEWS,
        source_url_or_id=href,
        instrument=instrument,
        metric=FILING_METRIC,
        value=form,
        published_at=published,
        ingested_at=ingested_at,
        market_time=published,
        payload={
            "cik": pad_cik(cik),
            "form": form,
            "accession": accession,
            "file_date": file_date[:10] if file_date else None,
            "primary_document": document,
            "licence_verdict": licence_verdict(),
            "historical": True,
        },
        extras={"cik": pad_cik(cik), "form": form, "accession": accession},
        historical=True,
        stale_after_seconds=stale_after_seconds,
        venue="filings",
        evidence_type=EvidenceType.FACT,
    )


def normalize_lockup_observation(
    *,
    instrument: str,
    cik: str,
    lockup: Mapping[str, Any],
    ingested_at: datetime,
    stale_after_seconds: int = 120,
) -> ObservationEnvelope:
    assume_180d = bool(lockup.get("assume_180d"))
    excerpt = str(lockup.get("excerpt") or lockup.get("lockup_period") or "")
    terms = str(lockup.get("terms") or lockup.get("lockup_period") or excerpt)
    bound = str(lockup.get("fail_closed_blackout_until") or "")[:10]
    url = str(lockup.get("url") or "")
    form = str(lockup.get("filing") or lockup.get("form") or "424B4")
    accession = str(lockup.get("accession") or "")
    file_date = str(lockup.get("file_date") or lockup.get("prospectus_date") or "")
    if assume_180d or not lockup_is_formula(assume_180d=assume_180d, excerpt=excerpt, terms=terms):
        return _degrade(
            instrument=instrument,
            ingested_at=ingested_at,
            error_class=ERROR_PARSE,
            notes=(
                "EDGAR lockup must be a prospectus formula, not a flat 180d assumption",
                "no expiry invented",
            ),
            source_url_or_id=url or f"edgar:{pad_cik(cik)}:lockup",
            metric=LOCKUP_METRIC,
        )
    if not bound or not url:
        return _degrade(
            instrument=instrument,
            ingested_at=ingested_at,
            error_class=ERROR_PARSE,
            notes=("lockup bound or prospectus URL missing; no 180d invented",),
            source_url_or_id=url or f"edgar:{pad_cik(cik)}:lockup",
            metric=LOCKUP_METRIC,
        )
    published = _file_datetime(file_date) or ingested_at
    return build_envelope(
        source_name=EDGAR_SOURCE_NAME,
        source_kind=SourceKind.NEWS,
        source_url_or_id=url,
        instrument=instrument,
        metric=LOCKUP_METRIC,
        value=bound,
        published_at=published,
        ingested_at=ingested_at,
        market_time=published,
        payload={
            "cik": pad_cik(cik),
            "form": form,
            "accession": accession,
            "file_date": file_date[:10] if file_date else None,
            "fail_closed_blackout_until": bound,
            "assume_180d": False,
            "staged_early_releases": bool(lockup.get("staged_early_releases")),
            "formula": terms.strip(),
            "excerpt": excerpt.strip()[:2000],
            "licence_verdict": licence_verdict(),
            "historical": True,
        },
        extras={
            "cik": pad_cik(cik),
            "form": form,
            "accession": accession,
            "assume_180d": "false",
        },
        historical=True,
        stale_after_seconds=stale_after_seconds,
        venue="filings",
        evidence_type=EvidenceType.FACT,
    )


def envelopes_from_issuer(
    ticker: str,
    issuer: Mapping[str, Any],
    *,
    ingested_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    instrument = _issuer_instrument(issuer, ticker)
    cik = str(issuer.get("cik") or "")
    if not cik:
        return [
            _degrade(
                instrument=instrument,
                ingested_at=ingested_at,
                error_class=ERROR_PARSE,
                notes=("CIK missing; no EDGAR filing invented",),
                source_url_or_id="edgar:missing_cik",
            )
        ]
    error_class = str(issuer.get("error_class") or "")
    if error_class:
        return [
            _degrade(
                instrument=instrument,
                ingested_at=ingested_at,
                error_class=error_class,
                notes=(f"EDGAR unavailable (error_class={error_class}); no lockup invented",),
                source_url_or_id=str(issuer.get("url") or f"edgar:{pad_cik(cik)}"),
            )
        ]
    out: list[ObservationEnvelope] = []
    submissions = issuer.get("submissions")
    if isinstance(submissions, dict):
        wanted = {str(x).upper() for x in (issuer.get("forms") or DEFAULT_FORMS)}
        for row in parse_recent_filings(submissions):
            if row["form"].upper() not in wanted:
                continue
            if not row["accession"] or not row["file_date"]:
                continue
            out.append(
                normalize_filing_observation(
                    instrument=instrument,
                    cik=cik,
                    form=row["form"],
                    accession=row["accession"],
                    file_date=row["file_date"],
                    document=row["primary_document"],
                    ingested_at=_row_ingested(issuer, ingested_at),
                    stale_after_seconds=stale_after_seconds,
                    url=str(issuer.get("url") or "") or None,
                )
            )
    lockup = issuer.get("lockup")
    if isinstance(lockup, dict):
        out.append(
            normalize_lockup_observation(
                instrument=instrument,
                cik=cik,
                lockup=lockup,
                ingested_at=_row_ingested(lockup, ingested_at),
                stale_after_seconds=stale_after_seconds,
            )
        )
    if not out:
        return [
            _degrade(
                instrument=instrument,
                ingested_at=ingested_at,
                error_class=ERROR_PARSE,
                notes=("no 424B4/S-1/lockup rows in payload; no expiry invented",),
                source_url_or_id=f"edgar:{pad_cik(cik)}",
            )
        ]
    return out


def envelopes_from_payload(
    payload: Mapping[str, Any],
    *,
    ingested_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    if payload.get("error_class") and not isinstance(payload.get("issuers"), dict):
        return [
            _degrade(
                instrument="EDGAR",
                ingested_at=ingested_at,
                error_class=str(payload.get("error_class")),
                notes=(f"EDGAR feed unavailable (error_class={payload.get('error_class')}); no filings invented",),
                source_url_or_id="edgar:feed_status",
            )
        ]
    issuers = payload.get("issuers") or payload.get("lockups") or {}
    if not isinstance(issuers, dict) or not issuers:
        return [
            _degrade(
                instrument="EDGAR",
                ingested_at=ingested_at,
                error_class=ERROR_PARSE,
                notes=("EDGAR payload has no issuers; no lockup invented",),
                source_url_or_id="edgar:empty",
            )
        ]
    out: list[ObservationEnvelope] = []
    for ticker, issuer in issuers.items():
        if not isinstance(issuer, dict):
            continue
        out.extend(
            envelopes_from_issuer(
                str(ticker),
                issuer,
                ingested_at=ingested_at,
                stale_after_seconds=stale_after_seconds,
            )
        )
    return out


def fetch_submissions(
    cik: str,
    *,
    ingested_at: datetime,
    http_client: httpx.Client | None = None,
    base_url: str = "",
    budget: RateLimitBudget | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Callable[[float], None] | None = None,
    settings: Mapping[str, Any] | None = None,
    instrument: str | None = None,
    stale_after_seconds: int = 120,
) -> tuple[list[ObservationEnvelope], str]:
    """Live data.sec.gov submissions GET. Missing/blocked → unavailable, never invent."""
    loaded = settings if settings is not None else load_ingest_settings()
    adapters = loaded.get("adapters") if isinstance(loaded.get("adapters"), dict) else {}
    block = adapters.get("edgar") if isinstance(adapters.get("edgar"), dict) else {}
    host = base_url or str(block.get("base_url") or "https://data.sec.gov")
    url = submissions_url(cik, base_url=host)
    name = instrument or f"CIK{pad_cik(cik)}"
    limiter = budget or RateLimitBudget(name="edgar", max_requests_per_minute=60)
    if not limiter.allow():
        return (
            [
                _degrade(
                    instrument=name,
                    ingested_at=ingested_at,
                    error_class=ERROR_RATE_LIMITED,
                    notes=("EDGAR rate-limit budget exhausted; no filing invented",),
                    source_url_or_id=url,
                )
            ],
            ERROR_RATE_LIMITED,
        )
    owns = http_client is None
    headers = client_headers(loaded)
    client = http_client or httpx.Client(timeout=8.0, headers=headers)
    try:
        kwargs: dict[str, Any] = {
            "max_attempts": max_attempts,
            "parse_json": True,
            "headers": headers,
        }
        if sleep is not None:
            kwargs["sleep"] = sleep
        result = http_get(client, url, **kwargs)
        if not result.ok:
            return (
                [
                    _degrade(
                        instrument=name,
                        ingested_at=ingested_at,
                        error_class=result.error_class,
                        notes=(f"EDGAR HTTP failed (error_class={result.error_class}); no lockup invented",),
                        source_url_or_id=url,
                    )
                ],
                result.error_class,
            )
        payload = result.json_payload if isinstance(result.json_payload, dict) else {}
        if not payload:
            return (
                [
                    _degrade(
                        instrument=name,
                        ingested_at=ingested_at,
                        error_class=ERROR_PARSE,
                        notes=("EDGAR submissions payload is empty; no filing invented",),
                        source_url_or_id=url,
                    )
                ],
                ERROR_PARSE,
            )
        issuer = {
            "qualified_id": name,
            "cik": cik,
            "submissions": payload,
            "forms": list(DEFAULT_FORMS),
        }
        return envelopes_from_issuer(name, issuer, ingested_at=ingested_at, stale_after_seconds=stale_after_seconds), ERROR_NONE
    finally:
        if owns:
            client.close()
